import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {bootJudge,pause,choose} from './judge-helpers.mjs';
const html=fs.readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
const text=(d,id)=>d.getElementById(id).textContent;

test('landing page: demo is the recommended first step, with a preview and a labs link',async()=>{
 const {dom,d,errors}=bootJudge(html);try{await pause();
  assert.match(d.querySelector('.recommended').textContent,/Recommended first step/);
  assert.equal(d.getElementById('lunar-demo').classList.contains('primary'),true);
  assert.equal(d.getElementById('lunar-demo').textContent,'Run the lunar habitat demo');
  assert.ok(d.querySelector('.will-get'));
  assert.match(d.body.textContent,/Turn NASA combustion evidence into your next research question/);
  const p=d.querySelector('.home-preview').textContent;assert.match(p,/Ranked experiment/);assert.match(p,/2\.1 mm\/s flame spread/);assert.match(p,/Measured for this run/);assert.match(p,/From microgravity to the Moon/);
  assert.match(d.getElementById('tool-key').textContent,/Research explorer.*Mission screening/);
  assert.ok(d.getElementById('labsBtn'));assert.equal(d.querySelectorAll('#registration,#checkout,form[action]').length,0);
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('For research labs: six criteria, planned features labelled, pricing hypothesis, validation targets, no checkout',async()=>{
 const {dom,d,w,errors}=bootJudge(html);try{await pause();
  d.getElementById('labsBtn').click();await pause();
  assert.equal(d.getElementById('labsBtn').getAttribute('aria-current'),'page');assert.equal(d.getElementById('homeBtn').getAttribute('aria-current'),null);assert.equal(w.location.hash,'#labs');
  const crit=text(d,'labs-criteria');for(const k of ['Customer','Buyer','Problem','Value','Revenue','Validation'])assert.match(crit,new RegExp(k));
  assert.match(crit,/University combustion and materials-science researchers/);assert.match(crit,/Our pilot targets are listed below/);
  assert.match(text(d,'labs-hypothesis'),/starts with university research labs/);
  assert.match(text(d,'labs-journey'),/material-flammability investigation/);
  assert.match(text(d,'offer-public'),/Free · Available now/);assert.match(text(d,'offer-workspace'),/Planned/);
  for(const f of ['shared projects','reviewer comments','version history','reviewed additions'])assert.match(text(d,'offer-workspace'),new RegExp('Planned: '+f));
  assert.equal(text(d,'pricing-statement'),'Proposed pilot pricing: US$49 per lab/month. We will test this price with research teams before launching subscriptions.');
    const v=text(d,'labs-validation');for(const q of ['identify relevant evidence correctly','distinguish measurements from missing evidence','with and without AstroFlare','return to saved projects','budget holder pay'])assert.match(v,new RegExp(q));
  assert.match(v,/three labs and ten observed research-review tasks/);assert.match(v,/hosting, support/);
  assert.doesNotMatch(d.getElementById('labs-page').textContent,/\$[0-9,]+ ?(million|billion|k\b)|market size of|saves? [0-9]+%/i);
  assert.equal(d.querySelectorAll('#labs-page input,#labs-page form,#labs-page [href*=checkout]').length,0);
  d.getElementById('labs-demo').click();await pause();assert.match(text(d,'research-decision'),/2\.1 mm\/s/);assert.equal(d.getElementById('demoBtn').getAttribute('aria-current'),'page');
  w.history.back();await pause();assert.ok(d.getElementById('labs-page'));assert.equal(d.getElementById('labsBtn').getAttribute('aria-current'),'page');
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('direct link to #labs opens the labs page',async()=>{
 const {dom,d}=bootJudge(html,{url:'https://astroflare.test/#labs'});try{await pause();assert.ok(d.getElementById('labs-page'));assert.equal(d.getElementById('labsBtn').getAttribute('aria-current'),'page');}finally{dom.window.close();}
});

test('no contact address, enquiry form or email link is published',async()=>{
 const {dom,d,errors}=bootJudge(html);try{await pause();d.getElementById('labsBtn').click();await pause();assert.equal(d.querySelectorAll('a[href^=mailto],#pilot,form[action]').length,0);assert.doesNotMatch(d.getElementById('labs-page').textContent,/contact address|Discuss a research pilot/);assert.doesNotMatch(html,/CONTACT_EMAIL/);assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

async function exports(w){const blobs=[],names=[];w.URL.createObjectURL=blob=>{blobs.push(blob);return 'blob:t/'+blobs.length};w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=function(){names.push(this.download)};
 const read=blob=>new Promise((res,rej)=>{const r=new w.FileReader();r.onload=()=>res(r.result);r.onerror=rej;r.readAsText(blob)});return {blobs,names,read};}

test('research projects: save, change, reopen restores filters + ranking + comparison + takeaway; exports separate measured/gaps/proposed',async()=>{
 const {dom,d,w,errors}=bootJudge(html);try{await pause();
  w.localStorage.setItem('astroflareSession','{"mission-save":"untouched"}');
  d.getElementById('demoBtn').click();await pause();
  assert.match(text(d,'project-storage-note'),/Saved on this browser only\./);
  // empty name: refused with a message, nothing stored
  d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));assert.match(text(d,'project-status'),/Give the project a name/);assert.equal(w.localStorage.getItem('astroflareResearchProjects'),null);
  // project 1: silicone, opposed
  choose(d,w,'filter-material','silicone');choose(d,w,'filter-airflow','opposed');
  const ex=await exports(w);
  d.getElementById('project-name').value='Silicone opposed';d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));
  assert.match(text(d,'project-status'),/Saved “Silicone opposed” on this browser only/);
  const saved=JSON.parse(w.localStorage.getItem('astroflareResearchProjects'));assert.equal(saved.length,1);const p=saved[0];
  assert.equal(p.datasetVersion,'2026-11-14.2');assert.deepEqual(p.filters,{material:'silicone',gravity:'any',airflow:'opposed'});assert.equal(p.scenario.gravity,'lunar');assert.ok(p.sourceRuns.includes('PSI-99:2-1'));assert.ok(p.brief.text.length>50);assert.ok(p.brief.citations.length>=1);
  assert.equal(w.localStorage.getItem('astroflareSession'),'{"mission-save":"untouched"}');
  // change everything, then reopen
  d.getElementById('restore-lunar-preset').click();await pause();assert.equal(d.getElementById('filter-material').value,'any');
  choose(d,w,'filter-material','fabric');assert.match(text(d,'research-decision'),/2\.1 mm\/s/);
  d.getElementById('open-'+p.id).click();await pause();
  assert.equal(d.getElementById('filter-material').value,'silicone');assert.equal(d.getElementById('filter-airflow').value,'opposed');assert.equal(d.getElementById('scenario-gravity').value,'lunar');
  assert.match(text(d,'filter-status'),/1 of 3/);assert.match(text(d,'filter-status'),/Project “Silicone opposed” restored/);
  assert.match(text(d,'research-decision'),/Insignificant/);assert.doesNotMatch(text(d,'research-decision'),/2\.1 mm/);
  assert.ok(d.getElementById('comparison').textContent.includes('Silicone'));assert.equal(d.querySelectorAll('input[id^=compare-]:checked').length,p.selected.length);
  assert.match(text(d,'project-status'),/Opened “Silicone opposed”/);
  // exports
  d.getElementById('md-'+p.id).click();d.getElementById('json-'+p.id).click();
  assert.equal(ex.names[0],'astroflare-silicone-opposed.md');assert.equal(ex.names[1],'astroflare-silicone-opposed.json');
  const md=await ex.read(ex.blobs[0]),json=JSON.parse(await ex.read(ex.blobs[1]));
  for(const h of ['## Research question and scenario','## Measured evidence (reported by NASA)','## Next conditions to test','## Proposed research (a suggestion, not a result)','## Citations'])assert.ok(md.includes(h),h);
  assert.match(md,/Insignificant/);assert.match(md,/do not convert|not .{0,40}zero|Insignificant/i);assert.doesNotMatch(md,/2\.1 mm\/s/);
  assert.match(md,/dataset version 2026-11-14\.2/);assert.match(md,/psi\.nasa\.gov/);assert.match(md,/Research relevance ranking/);assert.match(md,/its own test conditions/);assert.match(md,/independent project built on public NASA PSI data/);
  assert.equal(json.kind,'astroflare-research-project');assert.deepEqual(json.filters,p.filters);assert.match(json.note,/Research relevance ranking/);
  // a SIBAL project keeps the 2.1 mm/s with its material and run
  d.getElementById('restore-lunar-preset').click();await pause();d.getElementById('project-name').value='SIBAL fabric';d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));
  const fab=JSON.parse(w.localStorage.getItem('astroflareResearchProjects')).find(x=>x.name==='SIBAL fabric');d.getElementById('md-'+fab.id).click();const md2=await ex.read(ex.blobs[2]);
  assert.match(md2,/2\.1 mm\/s for run 2-5/);assert.match(md2,/SIBAL/);assert.match(md2,/under its own conditions/);assert.match(md2,/PSI-99:2-5/);
  // overwrite by name, then delete
  d.getElementById('project-name').value='sibal FABRIC';d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));assert.equal(JSON.parse(w.localStorage.getItem('astroflareResearchProjects')).length,2);assert.match(text(d,'project-status'),/Updated/);
  d.getElementById('del-'+p.id).click();assert.equal(JSON.parse(w.localStorage.getItem('astroflareResearchProjects')).length,1);assert.match(text(d,'project-status'),/Deleted/);
  assert.equal(w.localStorage.getItem('astroflareSession'),'{"mission-save":"untouched"}');
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('research projects: damaged, hostile and blocked storage fail with clear messages',async()=>{
 let {dom,d,w,errors}=bootJudge(html,{beforeParse(w){w.localStorage.setItem('astroflareResearchProjects','{not json');}});try{await pause();d.getElementById('demoBtn').click();await pause();
  assert.match(d.getElementById('project-list').textContent,/could not be read.*mission-screening save is not affected/);
  d.getElementById('project-name').value='After damage';d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));assert.match(text(d,'project-status'),/Saved “After damage”/);assert.equal(JSON.parse(w.localStorage.getItem('astroflareResearchProjects')).length,1);assert.deepEqual(errors,[]);}finally{dom.window.close();}
 // entries with impossible filters or unknown investigations are ignored, never applied
 ({dom,d,w,errors}=bootJudge(html,{beforeParse(w){w.localStorage.setItem('astroflareResearchProjects',JSON.stringify([{id:'x',name:'bad',question:'q',filters:{material:'<img onerror=1>',gravity:'any',airflow:'any'},scenario:{gravity:'lunar'},selected:[]},{id:'y',name:'bad2',question:'q',filters:{material:'any',gravity:'any',airflow:'any'},scenario:{gravity:'lunar'},selected:['PSI-00']}]));}}));try{await pause();d.getElementById('demoBtn').click();await pause();assert.equal(d.querySelectorAll('.project-item').length,0);assert.doesNotMatch(d.getElementById('research-projects').innerHTML,/onerror/);assert.deepEqual(errors,[]);}finally{dom.window.close();}
 // storage that throws on write
 ({dom,d,w,errors}=bootJudge(html,{beforeParse(w){w.Storage.prototype.setItem=function(){throw new Error('QuotaExceededError')};}}));try{await pause();d.getElementById('demoBtn').click();await pause();d.getElementById('project-name').value='Blocked';d.getElementById('project-form').dispatchEvent(new w.Event('submit',{cancelable:true}));assert.match(text(d,'project-status'),/would not save the project/);assert.equal(d.getElementById('project-status').className.includes('bad'),true);assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('keyboard: labs, project name and save are reachable form controls with labels',async()=>{
 const {dom,d}=bootJudge(html);try{await pause();d.getElementById('demoBtn').click();await pause();
  const label=d.querySelector('label[for=project-name]');assert.ok(label);assert.equal(d.getElementById('save-project').type,'submit');assert.equal(d.getElementById('project-status').getAttribute('role'),'status');
  for(const id of ['labsBtn','homeBtn','demoBtn','researchBtn','missionBtn'])assert.equal(d.getElementById(id).tagName,'BUTTON');}finally{dom.window.close();}
});

test('mission screening offers a clear choice: quick (default, 3 questions) or full (20 to 29)',async()=>{
 const {dom,d,w,errors}=bootJudge(html);try{await pause();
  d.getElementById('missionBtn').click();d.getElementById('skipBtn').click();await pause();
  const quick=d.getElementById('goal_quick'),full=d.getElementById('goal_investigate');
  assert.ok(quick&&full,'both options are offered');assert.equal(quick.checked,true,'quick is the default');assert.equal(full.checked,false);
  const page=d.getElementById('stage').textContent;assert.match(page,/How much detail do you want to give\?/);assert.match(page,/Quick, 3 questions/);assert.match(page,/Full, 20 to 29 questions/);
  assert.ok(d.getElementById('goal_gaps')&&d.getElementById('goal_influence'),'the existing goals are kept');
  full.click();full.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(d.getElementById('goal_investigate').checked,true);assert.equal(d.getElementById('goal_quick').checked,false);
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('every in-page link on every research page leads to an element that exists',async()=>{
 const routes=new Set(['#labs','#lunar-demo','#research','#mission']);
 const {dom,d,errors}=bootJudge(html);try{await pause();
  for(const open of [()=>{},()=>d.getElementById('labsBtn').click(),()=>d.getElementById('demoBtn').click(),()=>d.getElementById('researchBtn').click(),()=>d.getElementById('missionBtn').click()]){
   open();await pause();const bad=[...d.querySelectorAll('#stage a[href^="#"], header a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>h.length>1&&!routes.has(h)&&!d.getElementById(h.slice(1)));
   assert.deepEqual(bad,[],'dangling in-page links');
   const buttons=[...d.querySelectorAll('#stage button')].filter(b=>!b.textContent.trim()&&!b.getAttribute('aria-label'));assert.equal(buttons.length,0,'buttons without a name');}
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});

test('scope is stated plainly but not highlighted: relevance is not safety effectiveness, values keep their conditions, AI is labelled',async()=>{
 const {dom,d,w,errors}=bootJudge(html);try{await pause();d.getElementById('researchBtn').click();await pause();
  const scope=d.getElementById('research-scope');assert.match(scope.textContent,/not a measure of safety effectiveness/);assert.match(scope.textContent,/all run in microgravity/);assert.match(scope.textContent,/“Insignificant” for silicone run 2-1/);assert.match(scope.textContent,/AI-generated interpretations are labelled/);
  assert.equal(scope.closest('details').open,false,'sits in a collapsed disclosure, not a headline');
  assert.equal(d.querySelectorAll('#stage .notice.warn').length,0,'no warning-styled boxes on the research pages');
  d.getElementById('demoBtn').click();await pause();assert.equal(d.querySelectorAll('#stage .notice.warn').length,0);
  assert.match(text(d,'research-decision'),/2\.1 mm\/s/);assert.match(text(d,'research-decision'),/Next conditions to test/);
  assert.deepEqual(errors,[]);}finally{dom.window.close();}
});
