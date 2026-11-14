  // Keep original numerical services; own navigation, cancellation and recovery here.
  let screenEpoch=0,flowSequence=0;
  const screenTasks=new Map(),screenRequests=new Set();
  function beginTask(kind){const task={kind,epoch:screenEpoch,sequence:(screenTasks.get(kind)||0)+1};screenTasks.set(kind,task.sequence);return task;}
  function currentTask(task){return task.epoch===screenEpoch&&screenTasks.get(task.kind)===task.sequence;}
  function cancelScreenTasks(){screenEpoch++;flowSequence++;S.log?.forEach(entry=>{if(entry.kind==='pending'){entry.kind='note';entry.text='Request cancelled after navigation. Run the tool again when ready.';}});screenRequests.forEach(c=>c.abort());screenRequests.clear();}
  function screenStatus(text){let p=$('screening-pending');if(!p){p=el('p',{id:'screening-pending',class:'notice',role:'status','aria-live':'polite'});$('stage').prepend(p);}p.textContent=text;}
  function screenError(error){const p=$('screening-pending');if(p)p.remove();$('stage').prepend(el('p',{class:'notice bad',role:'alert',text:error.message}));}
  async function api(path,options,ms){
    const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),ms||20000);screenRequests.add(ctl);
    try{
      let res;try{res=await fetch(path,{cache:'no-store',...(options||{}),signal:ctl.signal});}catch(error){throw new Error(error?.name==='AbortError'?'The request was cancelled or took too long. Your answers are unchanged; retry when ready.':'The screening service could not be reached. Your answers are unchanged. Retry later or open the NASA lunar demo.');}
      let body;try{body=await res.json();}catch{body=null;}
      if(!res.ok){let message=body?.error||'The screening service returned HTTP '+res.status+'. Your answers are kept; retry later or open the NASA lunar demo.';if(res.status===429){const retry=res.headers?.get('Retry-After');message='The screening service is receiving too many requests. Your answers are kept. '+(/^\d+$/.test(retry||'')?'Retry after '+retry+' seconds. ':'Wait a moment, then retry. ')+'The NASA lunar demo remains available.';}const error=new Error(message);error.fields=body?.fields;error.code=body?.code;throw error;}
      if(!body||typeof body!=='object')throw new Error('The screening service sent an unexpected response. Your answers are kept; retry later.');
      return correctAssessmentTerminology(body);
    }finally{clearTimeout(timer);screenRequests.delete(ctl);}
  }
  function goTo(stage,opts){
    if(stage==='report'&&S.assessment&&!S.reportMd&&!S.reportErr&&!opts?.preparing)return prepareReport();
    cancelScreenTasks();if(stage!=='research')cancelEvidence();
    if(!['home','research','mission','problem','info','review','running','results','report'].includes(stage))stage='home';
    if(stage==='info'&&!S.flow||stage==='review'&&!S.profile||['results','report'].includes(stage)&&!S.assessment)stage='mission';
    S.stage=stage;document.body.classList.toggle('research-active',stage==='research'||stage==='home');S.reached[stage]=true;if(opts?.step)S.viewStep=opts.step;
    renderStepper();renderContext();renderStage();syncNavigation(stage);const h=$('stage').querySelector('h1,h2');if(h){h.tabIndex=-1;h.focus({preventScroll:true});}window.scrollTo({top:0,behavior:'auto'});
  }
  function collectVisibleDrafts(){
    if($('missionText'))S.mission.description=$('missionText').value.trim();
    if($('infoForm')){const step=S.flow?.steps.find(s=>s.id===S.viewStep);if(step)collectStep(step,false);}
    if($('qText')){const q=$('qText').value.trim();if(q)S.answers.question={value:q,unknown:false,basis:null,source:'typed'};else delete S.answers.question;const hazard=document.querySelector('input[name=hazard]:checked');if(hazard)S.answers.hazard={value:hazard.value,unknown:false,basis:null,source:'typed'};const goal=document.querySelector('input[name=goal]:checked');if(goal)S.goal=goal.value;}
  }
  function validStoredSession(s){return s&&typeof s==='object'&&!Array.isArray(s)&&s.mission&&typeof s.mission.description==='string'&&s.answers&&typeof s.answers==='object'&&!Array.isArray(s.answers)&&Object.entries(s.answers).every(([key,a])=>S.schema.fields.some(f=>f.id===key)&&a&&typeof a==='object'&&(a.value==null||['string','number'].includes(typeof a.value)));}
  async function readDescription(){
    const text=$('missionText').value.trim(),box=$('interpBox');if(!text){clear(box).appendChild(el('p',{class:'notice warn',text:'Write a mission description first, or skip this step.'}));return;}
    const task=beginTask('read');S.mission.description=text;$('readBtn').disabled=true;busy(box,'Reading your description with deterministic rules…');
    try{const r=await post('/api/guide/interpret',{text,ai:false});if(!currentTask(task))return;S.interp={data:r.interpretation,aiNote:null,aiPending:false,picks:{},hazardPick:null,aiMerged:false};initPicks();renderInterp();if(AI_ENABLED&&S.aiAvailable)refineWithAi(text);}catch(e){if(currentTask(task)){clear(box).appendChild(el('p',{class:'notice bad',role:'alert',text:e.message}));}}finally{if(currentTask(task)&&$('readBtn'))$('readBtn').disabled=false;}
  }
  async function refreshFlow(){const epoch=screenEpoch,sequence=++flowSequence;const f=await post('/api/guide/flow',{answers:answersPayload(),goal:S.goal});if(epoch!==screenEpoch||sequence!==flowSequence)throw new Error('Obsolete question request cancelled.');S.flow=f;return f;}
  async function showInfo(stepId){
    if(!hasValue(S.answers.hazard))return goTo('problem');const task=beginTask('info');if($('problemNext'))$('problemNext').disabled=true;if($('problemErr'))$('problemErr').textContent='';screenStatus('Loading the mission questions…');
    try{const f=await refreshFlow();if(!currentTask(task))return;const steps=f.steps.filter(s=>s.id!=='problem');let id=stepId||S.viewStep;if(!steps.some(s=>s.id===id))id=f.current&&f.current!=='problem'?f.current:null;if(!id)return showReview();S.viewStep=id;goTo('info',{step:id});}catch(e){if(currentTask(task)){goTo('problem');$('problemErr').textContent=e.message;}}
  }
  async function continueInfo(step){
    const button=$('infoNext');if(button.disabled)return;collectStep(step,true);const task=beginTask('continue');button.disabled=true;$('infoForm').setAttribute('aria-busy','true');screenStatus('Validating this group of answers…');
    try{const f=await refreshFlow();if(!currentTask(task))return;const cur=f.steps.find(s=>s.id===step.id);if(cur.questions.some(q=>q.error)){renderStage();renderContext();const bad=document.querySelector('.q .err');if(bad){bad.setAttribute('tabindex','-1');bad.focus({preventScroll:true});bad.scrollIntoView?.({block:'center'});}return;}const steps=visibleSteps(),i=steps.findIndex(s=>s.id===step.id),next=steps.slice(i+1).find(s=>!s.complete)||steps.find(s=>!s.complete);if(next){S.viewStep=next.id;goTo('info',{step:next.id});}else await showReview();}catch(e){if(currentTask(task)){button.disabled=false;$('infoForm')?.removeAttribute('aria-busy');screenError(e);}}
  }
  async function showReview(){
    const task=beginTask('review');screenStatus('Preparing your mission profile…');
    try{const f=await refreshFlow();if(!currentTask(task))return;if(!f.readyToReview){const n=f.steps.find(s=>s.id!=='problem'&&!s.complete);return n?showInfo(n.id):goTo('problem');}const p=await post('/api/guide/profile',{answers:answersPayload(),goal:S.goal,mission:missionPayload()});if(!currentTask(task))return;S.profile=p;S.ack=false;goTo('review');}catch(e){if(currentTask(task)){screenError(e);if($('infoNext'))$('infoNext').disabled=false;if($('problemNext'))$('problemNext').disabled=false;$('infoForm')?.removeAttribute('aria-busy');}}
  }
  async function runAssessment(){
    const task=beginTask('assessment'),inputs=engineInputs(),basis=basisMap(),pinned=S.pinned;S.stage='running';renderStage();
    try{const a=await post('/api/assess',{inputs,basis});if(!currentTask(task))return;S.demo=false;S.assessment=a;S.explain=null;S.reportMd=null;S.dirty=false;
      if(pinned){try{const r=await post('/api/compare',{baseline:pinned.inputs,baselineBasis:pinned.basis,current:inputs,currentBasis:basis});if(currentTask(task))pushLog({kind:'compare',comparison:r.comparison,from:pinned.id});}catch(e){if(currentTask(task))pushLog({kind:'error',message:'Assessment completed, but baseline comparison failed. '+e.message});}}
      if(!currentTask(task))return;goTo('results');if(S.goal==='influence')investigate('influence');else if(S.goal==='gaps')investigate('missing');
    }catch(e){if(currentTask(task)){goTo('review');screenError(new Error(e.fields?'Some inputs need attention: '+e.fields.map(f=>f.message).join(' '):'The assessment could not be completed. '+e.message+' Your answers are kept; you can run it again.'));}}
  }
  async function prepareReport(){
    S.reportMd=null;S.reportErr=null;goTo('report',{preparing:true});const task=beginTask('report'),n=narrativeFor(S.assessment);
    try{const r=await post('/api/report',{inputs:engineInputs(),basis:basisMap(),mission:missionPayload(),explain:false,includeInfluence:true,narrative:n?.status==='included'?n:null},60000);if(!currentTask(task))return;S.reportMd=r.markdown.replace(/Most consequential unresolved issue/gi,'One condition to review (not ranked)');S.reportJson=JSON.parse(JSON.stringify(r.report).replace(/Most consequential unresolved issue/gi,'One condition to review (not ranked)'));renderStage();screenStatus('Report ready. Download Markdown or JSON, or print the report.');}catch(e){if(currentTask(task)){S.reportErr=e.message;renderStage();}}
  }
  function openCustomResearch(){goTo('research');$('question-editor').open=true;$('research-question').focus({preventScroll:true});$('research-question').select();}

  async function investigate(action,extra){
    const epoch=screenEpoch,body={inputs:engineInputs(),basis:basisMap(),mission:missionPayload(),action,...(extra||{})};
    const pending=pushLog({kind:'pending',label:'Retrieving '+action+' from the screening service…'});
    try{const response=await post('/api/investigate',body,30000);if(epoch===screenEpoch)replaceLog(pending.id,response);}catch(error){if(epoch===screenEpoch)replaceLog(pending.id,{kind:'error',message:error.message});}
  }

  async function navigateInfoBack(step,index,steps){
    collectStep(step,false);if(index===0)return goTo('problem');
    const task=beginTask('back'),buttons=[...document.querySelectorAll('#infoForm button')];buttons.forEach(b=>b.disabled=true);screenStatus('Loading the previous question group…');
    try{await refreshFlow();if(currentTask(task))goTo('info',{step:steps[index-1].id});}catch(error){if(currentTask(task)){buttons.forEach(b=>b.disabled=false);screenError(error);}}
  }
