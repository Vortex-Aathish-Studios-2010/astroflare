import test from 'node:test';import assert from 'node:assert/strict';import {spawn} from 'node:child_process';import fs from 'node:fs';
const port=31000+Math.floor(Math.random()*2000);
async function withServer(fn){
 const child=spawn(process.execPath,['server.mjs'],{cwd:new URL('..',import.meta.url),env:{...process.env,PORT:String(port),ASTROFLARE_UPSTREAM:''},stdio:['ignore','pipe','pipe']});
 try{await new Promise((res,rej)=>{const t=setTimeout(()=>rej(new Error('server did not start')),15000);child.stdout.on('data',d=>{if(String(d).includes('listening')){clearTimeout(t);res();}});child.on('exit',()=>rej(new Error('server exited')));});
  return await fn('http://127.0.0.1:'+port);}finally{child.kill();}
}
const get=(u,headers={})=>fetch(u,{headers,redirect:'manual'});

test('static pages are compressed once, fingerprinted, and answer repeat visits with 304',async()=>{
 await withServer(async base=>{
  const local=fs.readFileSync(new URL('../public/index.html',import.meta.url));
  const gz=await get(base+'/',{'accept-encoding':'gzip'});
  assert.equal(gz.status,200);assert.equal(gz.headers.get('content-encoding'),'gzip');assert.equal(gz.headers.get('vary'),'Accept-Encoding');
  const sent=Number(gz.headers.get('content-length'));assert.ok(sent>0&&sent<local.length/2,'the bytes sent are less than half the page');
  assert.deepEqual(Buffer.from(await gz.arrayBuffer()),local,'the compressed page decompresses to the built page exactly');
  const etag=gz.headers.get('etag');assert.match(etag,/^"[A-Za-z0-9_-]{22}"$/);
  assert.match(gz.headers.get('content-security-policy'),/script-src 'self' 'sha256-/,'security headers are kept');
  const again=await get(base+'/',{'accept-encoding':'gzip','if-none-match':etag});assert.equal(again.status,304);assert.equal((await again.arrayBuffer()).byteLength,0);
  const stale=await get(base+'/',{'accept-encoding':'gzip','if-none-match':'"other"'});assert.equal(stale.status,200);
  // a client that does not accept gzip gets the plain page
  const plain=await fetch(base+'/',{headers:{'accept-encoding':'identity'}});assert.equal(plain.headers.get('content-encoding'),null);assert.deepEqual(Buffer.from(await plain.arrayBuffer()),local);
  // documentation, data and images still work; images and zips are not recompressed
  for(const [path,type] of [['/documentation','text/html'],['/dataset.json','application/json'],['/measurements.csv','text/csv'],['/nasa-candle-flames-1g-vs-microgravity.jpg','image/jpeg'],['/source.zip','application/zip']]){const r=await get(base+path,{'accept-encoding':'gzip'});assert.equal(r.status,200,path);assert.match(r.headers.get('content-type'),new RegExp(type),path);if(type.startsWith('image')||type.endsWith('zip'))assert.equal(r.headers.get('content-encoding'),null,path);await r.arrayBuffer();}
  assert.equal((await get(base+'/healthz')).status,200);
  const missing=await get(base+'/no-such-page');assert.equal(missing.status,404);await missing.arrayBuffer();
  const head=await fetch(base+'/',{method:'HEAD',headers:{'accept-encoding':'gzip'}});assert.equal(head.status,200);
 });
});

test('API routes are never cached or compressed by the static layer',async()=>{
 await withServer(async base=>{
  const wrongMethod=await get(base+'/api/assess');assert.equal(wrongMethod.status,405);assert.equal(wrongMethod.headers.get('etag'),null);await wrongMethod.arrayBuffer();
  const unknown=await get(base+'/api/nope');assert.equal(unknown.status,404);assert.equal(unknown.headers.get('etag'),null);await unknown.arrayBuffer();
 });
});
