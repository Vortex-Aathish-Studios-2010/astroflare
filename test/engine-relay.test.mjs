import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {handleRequest} from '../dist/server/index.js';import app from '../dist/server/index.js';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('a configured local engine replaces the public upstream and never touches it',async()=>{
 const seen=[];const res=await handleRequest(new Request('https://site.test/api/assess',{method:'POST',body:'{}'}),async(url,opts)=>{seen.push(url);return Response.json({ok:1});},'http://127.0.0.1:8001/');
 assert.deepEqual(seen,['http://127.0.0.1:8001/api/assess']);assert.equal(res.headers.get('X-Assessment-Engine'),'local-engine');
 const health=await handleRequest(new Request('https://site.test/healthz'),fetch,'http://127.0.0.1:8001');assert.equal((await health.json()).assessmentEngine,'local-engine');
});

test('without a configured engine the original public upstream is still used',async()=>{
 const seen=[];await handleRequest(new Request('https://site.test/api/assess',{method:'POST',body:'{}'}),async url=>{seen.push(url);return Response.json({});});
 assert.deepEqual(seen,['https://astroflare.onrender.com/api/assess']);
 const health=await handleRequest(new Request('https://site.test/healthz'));assert.equal((await health.json()).assessmentEngine,'remote-original');
});

test('the visitor address is forwarded for per-visitor limits, other headers are not',async()=>{
 let opts;await handleRequest(new Request('https://site.test/api/ask',{method:'POST',headers:{'x-forwarded-for':'203.0.113.9','cookie':'c','authorization':'a'},body:'{}'}),async(u,o)=>{opts=o;return Response.json({});},'http://127.0.0.1:8001');
 assert.equal(opts.headers['X-Forwarded-For'],'203.0.113.9');assert.equal(opts.headers.cookie,undefined);assert.equal(opts.headers.authorization,undefined);
 await handleRequest(new Request('https://site.test/api/ask',{method:'POST',body:'{}'}),async(u,o)=>{opts=o;return Response.json({});},'http://127.0.0.1:8001');
 assert.equal(opts.headers['X-Forwarded-For'],undefined);
});

test('the evidence-question AI route is relayed, POST only',async()=>{
 const seen=[];const ok=await handleRequest(new Request('https://x/api/research/ask',{method:'POST',body:'{"question":"q"}'}),async url=>{seen.push(url);return Response.json({mode:'ai'});});
 assert.equal(ok.status,200);assert.deepEqual(seen,['https://astroflare.onrender.com/api/research/ask']);
 assert.equal((await handleRequest(new Request('https://x/api/research/ask'))).status,405);
});

test('the default export reads the engine address from its environment argument',async()=>{
 const seen=[];const original=globalThis.fetch;globalThis.fetch=async url=>{seen.push(String(url));return Response.json({});};
 try{await app.fetch(new Request('https://site.test/api/status'),{ASTROFLARE_UPSTREAM:'http://127.0.0.1:8001'});await app.fetch(new Request('https://site.test/api/status'));}finally{globalThis.fetch=original;}
 assert.deepEqual(seen,['http://127.0.0.1:8001/api/status','https://astroflare.onrender.com/api/status']);
});

test('the built interface turns the AI features on and offers the optional evidence explanation',()=>{
 const html=read('public/index.html');
 assert.match(html,/const AI_ENABLED=true;/);assert.doesNotMatch(html,/AI remains inactive/);
 assert.match(html,/\/api\/research\/ask/);assert.match(html,/Explain with AI \(optional\)/);
});
