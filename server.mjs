import http from 'node:http';
import app from './dist/server/index.js';
const port=Number(process.env.PORT||3000);
http.createServer(async(req,res)=>{
 try {
  const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>262144){res.writeHead(413);res.end('Request too large');return;}chunks.push(chunk);}
  const init={method:req.method,headers:req.headers};if(!['GET','HEAD'].includes(req.method))init.body=Buffer.concat(chunks);
  const result=await app.fetch(new Request('http://localhost'+req.url,init));res.writeHead(result.status,Object.fromEntries(result.headers));res.end(Buffer.from(await result.arrayBuffer()));
 }catch{res.writeHead(500);res.end('Server error');}
}).listen(port,'0.0.0.0',()=>console.log('Astroflare listening on port '+port));
