  // Guided walkthrough at the top of the lunar habitat demo: choose a material → see NASA's observation → understand
  // the evidence gap. Every value is read from the curated PSI record; nothing is rounded, extrapolated or filled in.
  const GUIDE={material:'sibal'};
  const GUIDE_MATERIALS={
    sibal:{run:'2-5',label:'SIBAL',long:'SIBAL (cotton-fiberglass fabric)',
      headline:run=>({value:run.outcome.spreadRate,caption:'Flame spread rate measured in Saffire II, sample '+run.id}),
      extra:run=>[['Burn time',run.outcome.burnTime]],
      scope:'This is the value NASA measured for this sample under the conditions listed here.'},
    silicone:{run:'2-1',label:'Silicone',long:'Silicone',
      headline:run=>({value:run.outcome.burnTime,caption:'How NASA described the burn of Saffire II sample '+run.id+' (no spread rate was reported)'}),
      extra:run=>[['Flame spread rate',run.outcome.spreadRate]],
      scope:'“Insignificant” is NASA’s qualitative description of this burn. The measured spread rate for the other material, SIBAL fabric, is shown in the SIBAL view.'}
  };
  function guideRecord(){return PSI_DATA.records.find(r=>r.id==='PSI-99');}
  function renderGuideObservation(){
    const r=guideRecord(),m=GUIDE_MATERIALS[GUIDE.material],run=r&&r.runs.find(x=>x.id===m.run);
    const box=el('div',{class:'guide-observation',id:'guide-observation','aria-live':'polite'});
    if(!run){box.appendChild(el('p',{class:'notice warn',text:'This sample is missing from the curated dataset, so nothing is shown for it.'}));return box;}
    const h=m.headline(run);
    box.appendChild(el('p',{class:'guide-value'},[el('span',{class:'guide-number',id:'guide-value',text:h.value}),el('span',{class:'guide-caption',text:h.caption})]));
    const facts=[['Material tested',run.material],['Gravity',r.gravityLabel],['Airflow',run.airflow+', '+run.direction.toLowerCase()+' flow'],['Oxygen',run.oxygen+' '+run.oxygenUnit+' (worked out from measured CO₂, see CSV note 1)'],...m.extra(run)];
    box.appendChild(el('dl',{class:'guide-facts',id:'guide-conditions'},facts.flatMap(([k,v])=>[el('dt',{text:k}),el('dd',{text:v})])));
    box.appendChild(el('p',{class:'guide-scope',id:'guide-scope',text:m.scope}));
    box.appendChild(el('p',{class:'small guide-source',id:'guide-source'},['Source: NASA PSI-99 (Saffire II) · '+r.sourceFile+' · row '+run.id+' · ',psiLink(r,'Open NASA record ↗'),' · ',el('a',{href:r.downloadUrl,target:'_blank',rel:'noopener noreferrer',text:'Original CSV ↗'}),' · ',el('a',{href:'/sources/PSI-99-table.csv',download:r.sourceFile,text:'Download pinned copy'})]));
    return box;
  }
  function setGuideMaterial(key){
    if(!GUIDE_MATERIALS[key]||GUIDE.material===key)return;GUIDE.material=key;
    const old=document.getElementById('guide-observation');if(old)old.replaceWith(renderGuideObservation());
    document.querySelectorAll('.guide-switch button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.material===key)));
    const status=document.getElementById('guide-status');if(status)status.textContent='Showing '+GUIDE_MATERIALS[key].long+'. Measurement, test conditions and source row updated.';
    if(typeof syncNavigation==='function')syncNavigation('research',true);
  }
  function renderGuidedIntro(st){
    const g=el('section',{class:'card guided',id:'guided-intro','aria-labelledby':'guided-title'});
    g.appendChild(el('p',{class:'eyebrow',text:'Lunar habitat demo · 3 steps'}));
    g.appendChild(el('h1',{id:'guided-title',text:'What does NASA know about fabric and silicone fires in low gravity?'}));
    g.appendChild(el('p',{class:'lede',text:'A lunar habitat team wants to know how two cabin materials behave in a fire. Follow the three steps. Everything shown comes straight from a NASA experiment table.'}));
    const steps=el('ol',{class:'guide-steps'});
    const s1=el('li',{class:'guide-step'},[el('h2',{text:'Choose a material'})]);
    const sw=el('div',{class:'guide-switch',role:'group','aria-label':'Material'});
    Object.entries(GUIDE_MATERIALS).forEach(([key,m])=>{const b=el('button',{type:'button',class:'btn',id:'guide-'+key,text:m.long});b.dataset.material=key;b.setAttribute('aria-pressed',String(GUIDE.material===key));b.addEventListener('click',()=>setGuideMaterial(key));sw.appendChild(b);});
    s1.appendChild(sw);s1.appendChild(el('p',{class:'small',id:'guide-status',role:'status',text:'Both materials were burned in the same NASA experiment, Saffire II, so you can switch between them.'}));
    const s2=el('li',{class:'guide-step'},[el('h2',{text:'See NASA’s observation'}),renderGuideObservation()]);
    const rec=guideRecord(),o2=key=>{const run=rec&&rec.runs.find(x=>x.id===GUIDE_MATERIALS[key].run);return run?run.oxygen.replace(/^~\s*/,'')+'%':'not reported';};
    const s3=el('li',{class:'guide-step'},[el('h2',{text:'See where it applies and what comes next'}),
      el('ul',{class:'gap-list'},[
        el('li',{},[el('strong',{text:'Gravity. '}),'Both samples burned in microgravity, inside a spacecraft. Lunar gravity is the natural next test: NASA expects the LUCI and FM2 experiments to add partial-gravity data, and microgravity and Earth-gravity results can bracket what to expect in between.']),
        el('li',{},[el('strong',{text:'Oxygen. '}),'These runs had about '+o2('sibal')+' (SIBAL) and '+o2('silicone')+' (silicone) oxygen. A Moon base is expected to use 30% oxygen or more at 10.2 psi or less, so testing at those levels is the next step.'])]),
      el('p',{class:'guide-gap',text:'Next step: test these materials under lunar conditions.'}),
      el('p',{class:'small',text:'Moon-base atmosphere and partial-gravity data status: NASA Space Apps 2026 “Flame in Freefall” challenge brief.'})]);
    steps.appendChild(s1);steps.appendChild(s2);steps.appendChild(s3);g.appendChild(steps);
    g.appendChild(el('div',{class:'row guide-next'},[el('a',{class:'btn primary',href:'#evidence-ask-panel',text:'Ask a question about this evidence'}),el('a',{class:'btn',href:'#comparison',text:'Compare two experiments'}),el('a',{class:'btn',href:'#advanced-tools',text:'Advanced filters and tables'})]));
    st.appendChild(g);
  }
  function renderResearchHelp(st){
    st.appendChild(el('section',{class:'card guided guided-compact',id:'research-help'},[el('p',{class:'eyebrow',text:'NASA research · how to use'}),el('h1',{text:'Search NASA’s fire experiments with your own question'}),
      el('ol',{class:'how-steps'},[el('li',{text:'Write your question in plain words below, for example “How does airflow change flame spread on fabric?”.'}),el('li',{text:'Narrow the results with the filters (material, gravity, airflow).'}),el('li',{text:'Open the NASA source, compare two experiments, or ask for a cited answer.'})]),
      el('p',{class:'small',text:'Want a worked example first? Use “Lunar habitat demo” in the top menu.'})]));
  }
