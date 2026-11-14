import assert from 'node:assert/strict';
import {JSDOM,VirtualConsole} from 'jsdom';
export const origin='https://astroflare-research-2026.ajuponnu2009.chatgpt.site';
export const pause=()=>new Promise(r=>setTimeout(r,20));
export function bootJudge(html,{width=1280,historyState,url=origin+'/',fetcher=async()=>{throw Error('Remote service deliberately offline');}}={}){
 const errors=[],calls=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 const dom=new JSDOM(html,{url,runScripts:'dangerously',virtualConsole:vc,beforeParse(w){w.structuredClone=structuredClone;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};Object.defineProperty(w,'innerWidth',{value:width});w.matchMedia=query=>({matches:query.includes('reduced-motion'),media:query});w.fetch=async(path,opts)=>{calls.push(path);return fetcher(path,opts)};if(historyState)w.history.replaceState(historyState,'',url);}});
 return {dom,w:dom.window,d:dom.window.document,errors,calls};
}
export function choose(d,w,id,value){const f=d.getElementById(id);assert.ok(f,id);f.value=value;assert.equal(f.value,value);f.dispatchEvent(new w.Event('change'));}
export function submit(d,w,question,method='mouse'){const q=d.getElementById('evidence-ask');q.value=question;q.dispatchEvent(new w.Event('input'));if(method==='enter'){q.focus();q.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));}else d.getElementById('submit-evidence').click();}
const names={'PSI-25':'BASS-II','PSI-99':'Saffire II','PSI-98':'Saffire I'};
const all=['PSI-25','PSI-99','PSI-98'];
export function checkView(d,ids){
 assert.deepEqual([...d.querySelectorAll('[data-rank-id]')].map(e=>e.dataset.rankId),ids);
 assert.equal(d.querySelectorAll('.evidence-card').length,ids.length);
 const excluded=all.filter(x=>!ids.includes(x)),status=d.getElementById('filter-status').textContent;
 assert.ok(status.includes(`${ids.length} of 3 investigations match.`),status);
 assert.ok(status.includes(`Included (${ids.length}): ${ids.map(x=>names[x]).join(', ')||'none'}.`),status);
 assert.ok(status.includes(`Excluded (${excluded.length}): ${excluded.map(x=>names[x]).join(', ')||'none'}.`),status);
 if(ids.length)assert.equal(d.querySelector('.top-evidence h2').textContent,names[ids[0]]);
 const selected=[...d.querySelectorAll('input[id^=compare-]:checked')].map(e=>e.id.replace('compare-',''));
 assert.match(d.getElementById('compare-status').textContent,new RegExp('^'+selected.length+' of 2 selected'));
 assert.equal(d.querySelectorAll('#comparison > .tablewrap thead th').length,selected.length?selected.length+1:0);
 for(const id of selected){assert.ok(ids.includes(id));assert.ok(d.querySelector('#comparison > .tablewrap thead').textContent.includes(names[id]+' · '+id));}
 if(!ids.length){assert.match(d.getElementById('research-decision').textContent,/coverage gap/);assert.doesNotMatch(d.getElementById('research-decision').textContent,/2.1 mm/);}
}
export async function researchJudgeChecks(html,{width=1280}={}){
 const {dom,w,d,errors,calls}=bootJudge(html,{width});try{
 await pause();assert.ok(d.getElementById('lunar-demo'));const start=performance.now();d.getElementById('lunar-demo').click();const demoMs=performance.now()-start;checkView(d,all);assert.match(d.getElementById('research-decision').textContent,/2.1 mm\/s.*2-5/);assert.equal(d.querySelectorAll('input[id^=compare-]:checked').length,2);
 const matrix={material:{any:all,fabric:all,pmma:['PSI-25','PSI-99'],silicone:['PSI-99'],gas:[]},gravity:{any:all,microgravity:all,lunar:[],earth:[]},airflow:{any:all,forced:all,variable:['PSI-25'],'20':['PSI-99','PSI-98'],concurrent:all,opposed:all,quiescent:[]}};
 let filterCases=0;for(const [key,values] of Object.entries(matrix))for(const [value,ids] of Object.entries(values)){d.getElementById('demoBtn').click();choose(d,w,'filter-'+key,value);checkView(d,ids);filterCases++;}
 for(const [material,gravity,airflow,ids] of [['silicone','microgravity','20',['PSI-99']],['fabric','microgravity','forced',all],['pmma','microgravity','20',['PSI-99']],['silicone','lunar','20',[]],['silicone','microgravity','variable',[]]]){d.getElementById('demoBtn').click();choose(d,w,'filter-material',material);choose(d,w,'filter-gravity',gravity);choose(d,w,'filter-airflow',airflow);checkView(d,ids);filterCases++;}
 // Reproduced sequence: an already excluded BASS-II must still be listed.
 d.getElementById('demoBtn').click();choose(d,w,'filter-airflow','20');choose(d,w,'filter-material','silicone');checkView(d,['PSI-99']);assert.match(d.getElementById('filter-status').textContent,/Excluded \(2\): BASS-II, Saffire I/);assert.match(d.getElementById('research-decision').textContent,/2-1.*Insignificant/);assert.doesNotMatch(d.querySelector('.decision-layout').textContent+d.getElementById('comparison').textContent,/2.1 mm\/s/);
 d.getElementById('reset-research-filters').click();checkView(d,all);choose(d,w,'filter-gravity','lunar');checkView(d,[]);d.getElementById('restore-lunar-preset').click();checkView(d,all);assert.equal(d.querySelectorAll('input[id^=compare-]:checked').length,2);
 for(const gravity of ['microgravity','earth','any','lunar']){choose(d,w,'scenario-gravity',gravity);checkView(d,all);assert.equal(d.getElementById('filter-gravity').value,'any');if(gravity==='microgravity')assert.match(d.getElementById('research-decision').textContent,/Microgravity context matches/);if(gravity==='earth')assert.match(d.getElementById('research-decision').textContent,/earth/);}
 // Selection count and columns must agree for every comparison state.
 d.getElementById('demoBtn').click();d.getElementById('compare-PSI-98').click();assert.match(d.getElementById('compare-status').textContent,/Two selected/);assert.equal(d.getElementById('compare-PSI-98').checked,false);
 d.getElementById('compare-PSI-25').click();checkView(d,all);d.getElementById('compare-PSI-99').click();checkView(d,all);assert.match(d.getElementById('comparison').textContent,/Select up to two/);d.getElementById('compare-PSI-98').click();checkView(d,all);d.getElementById('compare-PSI-99').click();checkView(d,all);choose(d,w,'filter-material','silicone');checkView(d,['PSI-99']);
 const questions=[['What was the flame spread rate in Saffire II?',/Saffire II reported a flame spread rate of 2.1 mm\/s for run 2-5\./],['How fast did the flames spread in Saffire 2?',/2.1 mm\/s for run 2-5/],['What was the flame spread rate in PSI-99?',/2.1 mm\/s for run 2-5/],['What was the flame spread rate in Saffire I?',/selected PSI table does not report a flame-spread rate/],['What flame spread rate was measured in lunar gravity?',/microgravity.*no direct lunar-gravity/],['What was the flame spread rate for silicone in Saffire II?',/does not report.*run 2-1/],['Who won the football match?',/Evidence gap/]];
 for(const [question,expected] of questions){submit(d,w,question);assert.equal(d.getElementById('evidence-answer'),null);await pause();const a=d.getElementById('evidence-answer');assert.match(a.firstElementChild.textContent,expected);assert.equal(a.dataset.question,question);if(question.includes('silicone')||question.includes('lunar')||question.includes('Saffire I?'))assert.doesNotMatch(a.textContent,/2.1 mm\/s/);}
 for(let i=0;i<6;i++){submit(d,w,questions[3][0],'mouse');submit(d,w,questions[0][0],'enter');d.getElementById('evidence-example-1').click();assert.equal(d.getElementById('evidence-answer'),null);await pause();assert.match(d.getElementById('evidence-answer').textContent,/no direct lunar-gravity/);d.getElementById('evidence-example-2').click();d.getElementById('evidence-example-0').click();submit(d,w,questions[3][0],'enter');assert.equal(d.getElementById('evidence-answer'),null);await pause();assert.match(d.getElementById('evidence-answer').textContent,/Saffire I’s selected/);}
 for(const method of ['mouse','enter']){d.getElementById('evidence-example-0').click();submit(d,w,'  ',method);assert.equal(d.getElementById('evidence-answer'),null);await pause();assert.equal(d.getElementById('evidence-answer'),null);assert.match(d.getElementById('evidence-status').textContent,/Enter an evidence question/);}
 let copied='';Object.defineProperty(w.navigator,'clipboard',{configurable:true,value:{writeText:async t=>{copied=t}}});
 for(const material of ['any','silicone','gas']){d.getElementById('demoBtn').click();choose(d,w,'filter-material',material);d.getElementById('copy-research-brief').click();await pause();assert.match(copied,/scenario gravity: lunar/);assert.match(copied,/Next research step \(proposal, not performed\)/);assert.match(copied,/What is missing/);if(material==='any')assert.match(copied,/2.1 mm\/s[\s\S]*PSI-99 row 2-5/);if(material==='silicone'){assert.match(copied,/Insignificant[\s\S]*PSI-99 row 2-1/);assert.doesNotMatch(copied,/2.1 mm\/s/);}if(material==='gas'){assert.match(copied,/coverage gap/);assert.doesNotMatch(copied,/Source: PSI/);}assert.match(d.getElementById('brief-copy-status').textContent,/copied/);}
 Object.defineProperty(w.navigator,'clipboard',{value:{writeText:async()=>{throw Error('Permission denied');}}});d.getElementById('copy-research-brief').click();await pause();assert.match(d.getElementById('brief-copy-status').textContent,/Clipboard access failed/);assert.equal(d.getElementById('research-brief-text').hidden,false);assert.equal(d.activeElement.id,'research-brief-text');assert.match(d.getElementById('research-brief-text').value,/coverage gap/);
 d.getElementById('demoBtn').click();choose(d,w,'filter-material','silicone');const state=structuredClone(w.history.state),refreshURL=w.location.href;d.getElementById('homeBtn').click();assert.ok(d.getElementById('lunar-demo'));w.history.back();await pause();checkView(d,['PSI-99']);w.history.forward();await pause();assert.ok(d.getElementById('lunar-demo'));
 const reload=bootJudge(html,{width,url:refreshURL,historyState:state});await pause();checkView(reload.d,['PSI-99']);reload.dom.window.close();
 assert.deepEqual(errors,[]);assert.deepEqual(calls.filter(x=>x!='/api/status'),[]);
 return {width,mode:'fresh unauthenticated JSDOM; not a rendering browser',demoClickToCitedTakeawayMs:Math.round(demoMs),filterCases,comparisonStates:'0, 1, 2, rejected third, selected study filtered out',questionCases:questions.length,rapidSubmissionBatches:12,blankCancelsPending:true,briefCopyAndDeniedFallback:true,backForwardAndRefreshState:true,uncaughtDomErrors:errors.length};
 }finally{dom.window.close();}
}
