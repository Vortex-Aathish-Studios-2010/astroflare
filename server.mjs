import http from 'node:http';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import app from './dist/server/index.js';
const port=Number(process.env.PORT||3000);
const env={ASTROFLARE_UPSTREAM:process.env.ASTROFLARE_UPSTREAM};
// Static pages and files never change while the server runs, so each is built, compressed and fingerprinted once.
// The container shares a very small CPU with the engine and the AI router, so sending a quarter of the bytes (and a
// quick 304 when the browser already has the file) is what keeps the first screen fast.
const COMPRESSIBLE=/^(text\/|application\/(json|javascript)|image\/svg|font\/ttf)/;
const cache=new Map();
async function staticEntry(req,proto){
 const key=proto+' '+req.url;let entry=cache.get(key);if(entry)return entry;
 const result=await app.fetch(new Request('http://localhost'+req.url,{method:'GET',headers:{'x-forwarded-proto':proto}}),env);
 if(result.status!==200)return null;
 const body=Buffer.from(await result.arrayBuffer()),type=result.headers.get('content-type')||'';
 const headers=Object.fromEntries(result.headers);
 entry={status:200,headers,body,gz:COMPRESSIBLE.test(type)&&body.length>1024?zlib.gzipSync(body,{level:9}):null,etag:'"'+crypto.createHash('sha1').update(body).digest('base64url').slice(0,22)+'"'};
 if(cache.size<200)cache.set(key,entry);return entry;
}
function sendStatic(req,res,entry){
 const h={...entry.headers,ETag:entry.etag,Vary:'Accept-Encoding'};delete h['content-length'];
 if(req.headers['if-none-match']===entry.etag){res.writeHead(304,{ETag:entry.etag,'Cache-Control':h['Cache-Control']||h['cache-control']||'no-cache',Vary:'Accept-Encoding'});res.end();return;}
 const gz=entry.gz&&/\bgzip\b/.test(req.headers['accept-encoding']||'');const out=gz?entry.gz:entry.body;
 if(gz)h['Content-Encoding']='gzip';h['Content-Length']=out.length;
 res.writeHead(200,h);res.end(req.method==='HEAD'?undefined:out);
}
http.createServer(async(req,res)=>{
 try {
  const proto=String(req.headers['x-forwarded-proto']||'').split(',')[0].trim()==='https'?'https':'http';
  if((req.method==='GET'||req.method==='HEAD')&&!req.url.startsWith('/api/')){
   const entry=await staticEntry(req,proto);if(entry){sendStatic(req,res,entry);return;}
  }
  const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>262144){res.writeHead(413);res.end('Request too large');return;}chunks.push(chunk);}
  const init={method:req.method,headers:req.headers};if(!['GET','HEAD'].includes(req.method))init.body=Buffer.concat(chunks);
  const result=await app.fetch(new Request('http://localhost'+req.url,init),env);res.writeHead(result.status,Object.fromEntries(result.headers));res.end(Buffer.from(await result.arrayBuffer()));
 }catch{res.writeHead(500);res.end('Server error');}
}).listen(port,'0.0.0.0',()=>{console.log('Astroflare listening on port '+port);
 // Warm the home page so the first visitor does not wait for its compression.
 setImmediate(()=>{for(const proto of ['https','http'])staticEntry({url:'/'},proto).catch(()=>{});});});
