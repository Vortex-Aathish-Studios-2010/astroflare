import fs from 'node:fs';import test from 'node:test';import assert from 'node:assert/strict';import vm from 'node:vm';import {journalChecks} from './journal-helpers.mjs';
const read=f=>fs.readFileSync(new URL('../'+f,import.meta.url),'utf8'),html=read('public/index.html');
for(const width of [1280,390])test('journal plate and scientific audit regression at DOM width '+width,async()=>{await journalChecks(html,width)});
test('I²t presentation correction preserves all numeric values and units; raw source stays intact',()=>{
 const c=vm.createContext({});vm.runInContext(read('public/terminology.js')+';globalThis.correct=correctAssessmentTerminology;',c);const original=JSON.parse(read('test/fixture-report.json')),corrected=c.correct(original);assert.doesNotMatch(JSON.stringify(corrected),/let[-\s]through energy/i);assert.match(corrected.markdown,/fault current integral \(I²t\)/);assert.match(original.markdown,/let-through energy/i);
 const before=original.report.assessment.derived.map(r=>({value:r.value,unit:r.unit})),after=corrected.report.assessment.derived.map(r=>({value:r.value,unit:r.unit}));assert.equal(JSON.stringify(after),JSON.stringify(before));const quantity=corrected.report.assessment.derived.find(r=>r.unit==='A²·s');assert.equal(quantity.value,112.5);assert.equal(quantity.label,'fault current integral (I²t)');
});
test('journal styling uses local requested fonts and no gradients, halos or looping plate animation',()=>{const css=read('public/explorer.css');assert.doesNotMatch(css,/gradient\(|blur\(|flame-orb/);assert.match(css,/Instrument Serif/);assert.match(css,/Instrument Sans/);assert.match(css,/@media\(max-width:740px\)/);assert.match(css,/@media\(prefers-reduced-motion:reduce\)/);assert.match(html,/const AI_ENABLED=true/);});

test('screening AI explanation follows the service status: available turns it on, unavailable keeps it clearly off',async()=>{
 const {bootJudge,pause}=await import('./judge-helpers.mjs');
 for(const available of [true,false]){const {dom,d,errors}=bootJudge(html,{fetcher:async path=>{if(path==='/api/status')return Response.json({analysis:{explanation:{available}}});throw Error('Remote service deliberately offline');}});try{await pause();await pause();d.getElementById('screeningDemoBtn').click();assert.equal(d.getElementById('explainBtn').disabled,!available);if(!available)assert.match(d.getElementById('explainStatus').textContent,/Not available/);assert.deepEqual(errors,[]);}finally{dom.window.close();}}
});
