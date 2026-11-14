  const ANSWERS=latestOnlyAnswers();
  function reducedMotion(){return typeof window.matchMedia==='function'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;}
  function animateArrival(element){if(element&&typeof element.animate==='function'&&!reducedMotion())element.animate([{opacity:.45,transform:'translateY(7px)'},{opacity:1,transform:'none'}],{duration:180,easing:'ease-out'});}
  function preserveView(update,focusId){
    const x=window.scrollX,y=window.scrollY,active=document.activeElement,id=focusId||active?.id,start=active?.selectionStart,end=active?.selectionEnd;
    const open=[...document.querySelectorAll('details[id][open]')].map(d=>d.id);const previous=new Map([...document.querySelectorAll('[data-rank-id]')].map(e=>[e.dataset.rankId,e.getBoundingClientRect()]));
    update();open.forEach(id=>{const d=document.getElementById(id);if(d)d.open=true;});
    const next=id&&document.getElementById(id);if(next){next.focus({preventScroll:true});if(next.setSelectionRange&&start!=null)try{next.setSelectionRange(start,end);}catch{}}
    window.scrollTo({left:x,top:y,behavior:'instant'});
    if(!reducedMotion())document.querySelectorAll('[data-rank-id]').forEach(e=>{const old=previous.get(e.dataset.rankId),now=e.getBoundingClientRect();if(old&&old.height&&now.height&&e.animate){const dy=old.top-now.top;if(Math.abs(dy)>1)e.animate([{transform:'translateY('+dy+'px)'},{transform:'none'}],{duration:200,easing:'ease-out'});}});
  }
  function refreshResearch(focusId){preserveView(()=>renderStage(),focusId);syncNavigation('research',true);}
  function refreshAnswerPanel(){
    if(S.stage!=='research')return;
    preserveView(()=>{const old=document.getElementById('evidence-ask-panel');if(!old)return;const holder=el('div');renderEvidenceAsk(holder,rankResearch(EXPLORER.question,EXPLORER.filters,EXPLORER.scenario));old.replaceWith(holder.firstElementChild);});
  }
  function submitEvidenceQuestion(text){
    const question=text.trim();if(!question){cancelEvidence();EXPLORER.askDraft=text;EXPLORER.askStatus='empty';refreshAnswerPanel();return;}
    const records=rankResearch(EXPLORER.question,EXPLORER.filters,EXPLORER.scenario).map(r=>scenarioRecord(r,EXPLORER.filters.material));
    return ANSWERS.submit(question,q=>evidenceAnswer(q,records),q=>{EXPLORER.ask=q;EXPLORER.askDraft=q;EXPLORER.submittedQuestion=q;EXPLORER.answer=null;EXPLORER.askStatus='loading';refreshAnswerPanel();},(answer,q)=>{EXPLORER.answer=answer;EXPLORER.askStatus='ready';EXPLORER.submittedQuestion=q;refreshAnswerPanel();animateArrival(document.getElementById('evidence-answer'));},(error,q)=>{EXPLORER.answer=evidenceAnswer(q,records);EXPLORER.askStatus='ready';EXPLORER.submittedQuestion=q;refreshAnswerPanel();});
  }
  function cancelEvidence(){ANSWERS.cancel();EXPLORER.answer=null;EXPLORER.askStatus='idle';EXPLORER.submittedQuestion='';}
  function renderDecision(records){
    const d=researchDecision(records,EXPLORER.filters,EXPLORER.scenario);d.text=d.text.replace(LUNAR_QUESTION,EXPLORER.question);
    const panel=el('aside',{class:'card decision-panel',id:'research-decision','aria-labelledby':'decision-heading'},[el('p',{class:'eyebrow',text:'RESEARCH DECISION / PROPOSED FOLLOW-UP'}),el('h2',{id:'decision-heading',text:'What should we test next?'})]);
    panel.appendChild(el('p',{class:'evidence-choice',id:'evidence-choice',text:d.rationale}));
    [['What NASA measured',d.measured],['What’s missing for this scenario',d.missing],['Next research step',d.step]].forEach(([heading,text],i)=>panel.appendChild(el('section',{class:'decision-section'},[el('span',{class:'decision-number','aria-hidden':'true',text:'0'+(i+1)}),el('div',{},[el('h3',{text:heading}),el('p',{text})])])));
    panel.appendChild(el('p',{class:'small',text:'Variable to study: '+d.variable+'. Hold material, atmosphere, geometry and ignition fixed; define missing test inputs first.'}));
    const fixed=el('details',{class:'sub',id:'research-fixed'},[el('summary',{text:'Variable & fixed conditions for the proposed study'}),el('p',{text:'Study: '+d.variable+'.'}),el('p',{text:'Hold fixed: '+d.fixed})]);panel.appendChild(fixed);
    d.citations.forEach(c=>panel.appendChild(el('p',{class:'small'},[el('a',{href:c.url,target:'_blank',rel:'noopener noreferrer',text:'Original NASA table · '+c.id+' · row '+c.row+' ↗'})])));
    const copy=el('button',{type:'button',id:'copy-research-brief',class:'btn primary',text:'Copy research brief + citations'}),status=el('span',{class:'small',id:'brief-copy-status',role:'status'});
    const fallback=el('textarea',{id:'research-brief-text',readonly:'true','aria-label':'Research brief with citations',hidden:true});fallback.value=d.text;
    copy.addEventListener('click',async()=>{try{if(!navigator.clipboard?.writeText)throw Error('clipboard unavailable');await navigator.clipboard.writeText(d.text);status.textContent='Research brief copied with citations.';}catch{fallback.hidden=false;fallback.focus({preventScroll:true});fallback.select();status.textContent='Clipboard access failed. Select and copy the brief below (Ctrl/Cmd+C).';}});panel.appendChild(el('div',{class:'row mt'},[copy,status]));panel.appendChild(fallback);return panel;
  }
  function instrumentLayout(st,ranked,grid){
    const top=grid.firstElementChild,comparison=document.getElementById('comparison');const row=el('div',{class:'decision-layout'}),left=el('div',{class:'lead-evidence'});
    if(top){top.classList.add('top-evidence');const why=top.querySelector('.why-rank strong');if(why)why.textContent='Why this ranked first: ';left.appendChild(top);}
    else left.appendChild(el('section',{class:'card empty-state'},[el('h2',{text:'No matching evidence'}),el('p',{text:'The selected filters leave no material-matched NASA baseline.'})]));
    const strip=el('ol',{class:'rank-strip','aria-label':'Investigation relevance order'});ranked.forEach((r,i)=>strip.appendChild(el('li',{'data-rank-id':r.id},[el('span',{class:'mono',text:'0'+(i+1)}),el('strong',{text:r.name}),el('span',{class:'small',text:r.points+' relevance pts'}),psiLink(r,'NASA ↗')])));left.appendChild(strip);row.appendChild(left);row.appendChild(renderDecision(ranked));
    st.insertBefore(row,grid);grid.remove();
    const rest=el('details',{class:'sec additional-evidence',id:'additional-evidence'},[el('summary',{text:'Other ranked investigations & detailed run notes ('+Math.max(0,ranked.length-1)+')'})]);const inner=el('div',{class:'in'});while(grid.firstChild)inner.appendChild(grid.firstChild);rest.appendChild(inner);if(comparison)comparison.after(rest);
    const facts=top?.querySelector('.evidence-facts');if(facts){const detail=el('details',{class:'sub',id:'top-result-conditions'},[el('summary',{text:'All documented conditions & measurement notes'})]);facts.before(detail);detail.appendChild(facts);}
    if(top){const outcome=top.querySelector('.evidence-kind');if(outcome)top.querySelector('.why-rank').after(outcome);}
  }

  // Persist only the research view in same-origin history; no mission inputs are added to URLs.
  let navigationReady=false,navigationRestoring=false;
  function syncNavigation(stage,replace=false){
    if(navigationRestoring)return;
    const state={astroflare:true,stage,explorer:stage==='research'?{question:EXPLORER.question,filters:{...EXPLORER.filters},scenario:{...EXPLORER.scenario},selected:[...EXPLORER.selected]}:null};
    const hash=stage==='home'?'':stage==='research'?'#lunar-demo':'#'+stage;
    const method=!navigationReady||replace||history.state?.stage===stage?'replaceState':'pushState';
    history[method](state,'',location.pathname+location.search+hash);navigationReady=true;
  }
  function restoreNavigation(){
    const saved=history.state?.astroflare?history.state:null;
    let stage=saved?.stage||(location.hash==='#lunar-demo'?'research':location.hash==='#mission'?'mission':'home');
    if(!['home','research','mission'].includes(stage)&&!canVisit(stage))stage='mission';
    if(stage==='research'&&saved?.explorer){const e=saved.explorer;EXPLORER.question=e.question;EXPLORER.filters={...e.filters};EXPLORER.scenario={...e.scenario};EXPLORER.selected=[...e.selected];EXPLORER.change='Research view restored. Original evidence and source links remain available.';}
    cancelEvidence();navigationRestoring=true;goTo(stage);navigationRestoring=false;syncNavigation(stage,true);
  }
  window.addEventListener('popstate',restoreNavigation);
  document.addEventListener('click',event=>{const a=event.target.closest?.('a[href^="#"]');if(!a)return;const target=document.getElementById(a.getAttribute('href').slice(1));if(!target)return;event.preventDefault();if(!target.hasAttribute('tabindex'))target.setAttribute('tabindex','-1');target.focus({preventScroll:true});target.scrollIntoView?.({block:'start',behavior:'auto'});});
