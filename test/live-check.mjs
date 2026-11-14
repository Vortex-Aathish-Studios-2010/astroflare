import fs from 'node:fs';import assert from 'node:assert/strict';import {handleRequest} from '../dist/server/index.js';
const base='https://astroflare.onrender.com';const schema=JSON.parse(fs.readFileSync(new URL('../sources/schema.json',import.meta.url)));
async function post(path,body){const r=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(60000)});assert.equal(r.status,200,path);return r.json();}
for(const example of schema.examples){
 const inputs=example.inputs,basis=Object.fromEntries(Object.keys(inputs).map(k=>[k,'assumption']));
 const body={inputs,basis},direct=await post('/api/assess',body);
 const proxied=await handleRequest(new Request('https://copy.test/api/assess',{method:'POST',body:JSON.stringify(body)}));assert.equal(proxied.status,200);const via=await proxied.json();assert.deepEqual(via,direct,'All original assessment output must be unchanged');console.log('PASS original engine equality: '+example.id);
}
const inputs=schema.examples[1].inputs;const answers=Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,{value:v,basis:'assumption',source:'typed',unknown:false}]));
const flow=await post('/api/guide/flow',{answers,goal:'investigate'});assert.ok(flow.steps);const profile=await post('/api/guide/profile',{answers,goal:'investigate',mission:{description:'Hypothetical regression test',destination:'transit'}});assert.ok(profile.derived);console.log('PASS guide flow and profile');
