import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';import {JSDOM,VirtualConsole} from 'jsdom';import {handleRequest} from '../dist/server/index.js';
const root=new URL('../',import.meta.url),read=p=>fs.readFileSync(new URL(p,root),'utf8');
const source=read('public/research.js');const ctx=vm.createContext({});vm.runInContext(source+';globalThis.rank=rankResearch;',ctx);
test('relevance matches topics, counts duplicates once and handles no match',()=>{
 const a=ctx.rank('electrical wire wiring airflow');assert.equal(a[0].id,'etfe');assert.equal(a[0].points,2);
 assert.equal(ctx.rank('wire wire wire')[0].points,1);assert.ok(ctx.rank('unrelated bananas').every(x=>x.points===0));
 assert.equal(ctx.rank('smoke detection toxic products')[0].id,'saffire6');
});
test('measured rates and units match reported NASA transcription',()=>{const csv=read('public/measurements.csv');assert.match(csv,/flame_spread_mm_s/);assert.deepEqual(csv.trim().split('\n').slice(1).map(r=>Number(r.split(',')[1])),[1.8,1.3,2.1]);assert.match(csv,/20170008805.pdf/);assert.match(read('sources/20170008805.txt'),/average spread rate 1.3 mm\/s/);});
test('relay preserves original result, body and upstream target without forwarding cookies',async()=>{
 const body=JSON.stringify({inputs:{hazard:'electrical',voltage_v:'28'}}),out={derived:[{value:112.5}],screeningIndex:{value:2},summary:{text:'Original'}};
 const res=await handleRequest(new Request('https://copy.test/api/assess?evil=1',{method:'POST',headers:{cookie:'secret','authorization':'Bearer private'},body}),async(url,opts)=>{assert.equal(url,'https://astroflare.onrender.com/api/assess');assert.equal(opts.body,body);assert.equal(opts.headers.cookie,undefined);assert.equal(opts.headers.authorization,undefined);return Response.json(out);});assert.deepEqual(await res.json(),out);
});
test('relay validates route, methods, payload limit and errors',async()=>{
 assert.equal((await handleRequest(new Request('https://x/api/nope'))).status,404);
 assert.equal((await handleRequest(new Request('https://x/api/assess'))).status,405);
 assert.equal((await handleRequest(new Request('https://x/api/assess',{method:'POST',body:'x'.repeat(262145)}))).status,413);
 const fail=await handleRequest(new Request('https://x/api/status'),async()=>{throw Error('down')});assert.equal(fail.status,502);assert.match((await fail.json()).error,/temporarily unavailable/);
});
test('assets, documentation, CSV and health work without the engine',async()=>{
 for(const path of ['/','/documentation','/verification','/measurements.csv','/healthz','/source.zip'])assert.equal((await handleRequest(new Request('https://x'+path))).status,200);
 assert.equal((await handleRequest(new Request('https://x/not-a-page'))).status,404);
});
function boot(){const calls=[],errors=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));const dom=new JSDOM(read('public/index.html'),{url:'https://copy.test',runScripts:'dangerously',virtualConsole:vc,beforeParse(w){w.structuredClone=structuredClone;w.scrollTo=()=>{};w.fetch=async(path,opts)=>{calls.push({path,opts});if(path==='/api/guide/flow')return Response.json(JSON.parse(read('test/fixture-flow.json')));if(path==='/api/guide/profile')return Response.json(JSON.parse(read('test/fixture-profile.json')));if(path==='/api/report')return Response.json(JSON.parse(read('test/fixture-report.json')));if(path==='/api/assess')return Response.json(JSON.parse(read('demo.json')).assessment);if(path==='/api/status')return Response.json({analysis:{explanation:{available:false}}});return handleRequest(new Request('https://copy.test'+path,opts));};}});return {dom,calls,errors,w:dom.window,d:dom.window.document};}
const ready=()=>new Promise(r=>setTimeout(r,25));
test('demo opens immediate populated original results, explorer leaves screening unchanged, save/load works',async()=>{
 const {dom,calls,errors,w,d}=boot();await ready();
 assert.match(d.getElementById('stage').textContent,/What mission are you assessing/);
 d.getElementById('demoBtn').click();assert.match(d.getElementById('stage').textContent,/HYPOTHETICAL DEMO/);assert.match(d.getElementById('stage').textContent,/Key findings/);
 assert.equal(calls.filter(c=>c.path==='/api/assess').length,0);assert.equal(calls.filter(c=>c.path==='/api/nasa/flares').length,0);
 assert.doesNotMatch(d.getElementById('stage').textContent,/Most consequential unresolved issue/);assert.match(d.getElementById('stage').textContent,/Unanswered input fields/);assert.match(d.getElementById('stage').textContent,/Scientific evidence limits/);
 const summary=d.querySelector('.status-label').textContent;
 d.getElementById('saveBtn').click();assert.ok(w.localStorage.getItem('astroflareSession'));
 d.getElementById('researchBtn').click();assert.match(d.getElementById('stage').textContent,/NASA combustion research explorer/);
 d.getElementById('research-question').value='electrical wire ventilation';d.querySelector('#stage form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 assert.match(d.querySelector('.research-grid h3').textContent,/ETFE/);
 const third=d.getElementById('compare-saffire6');third.click();assert.match(d.getElementById('compare-status').textContent,/at most two/);
 d.getElementById('compare-etfe').click();d.getElementById('compare-saffire6').click();assert.match(d.getElementById('compare-status').textContent,/2 of 2/);
 assert.equal(d.querySelectorAll('input[type=checkbox]:checked').length,2);
 assert.equal(d.querySelectorAll('.measurement-bar').length,3);
 const resultButton=[...d.querySelectorAll('#stepper button')].find(x=>/Results/.test(x.textContent));resultButton.click();assert.equal(d.querySelector('.status-label').textContent,summary);
 assert.equal(calls.filter(c=>c.path==='/api/assess').length,0);
 d.getElementById('loadBtn').click();await new Promise(r=>setTimeout(r,1500));assert.match(d.getElementById('stage').textContent,/Check the mission profile|Review|working assumptions/i);assert.ok(d.getElementById('ackBox'));d.getElementById('ackBox').click();d.getElementById('runBtn').click();await ready();assert.equal(calls.filter(c=>c.path==='/api/assess').length,1);assert.doesNotMatch(d.getElementById('stage').textContent,/HYPOTHETICAL DEMO · All inputs/);const prepare=[...d.querySelectorAll('button')].find(b=>b.textContent==='Prepare report');prepare.click();await ready();assert.match(d.getElementById('stage').textContent,/Assessment report/);assert.doesNotMatch(d.getElementById('stage').textContent,/Most consequential unresolved issue/);
 assert.deepEqual(errors.map(e=>e.message),[]);dom.window.close();
});
test('research explorer remains usable while upstream unavailable and shows no-match state',async()=>{
 const {dom,d,w,errors}=boot();await ready();d.getElementById('researchBtn').click();d.getElementById('research-question').value='bananas';d.querySelector('#stage form').dispatchEvent(new w.Event('submit',{cancelable:true}));assert.match(d.getElementById('stage').textContent,/No recognized topic matches/);assert.equal(d.querySelectorAll('.research-grid article').length,3);assert.deepEqual(errors,[]);dom.window.close();
});
