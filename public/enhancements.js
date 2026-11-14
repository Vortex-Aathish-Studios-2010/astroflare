  let researchQuestion = 'How does ventilation affect flame spread in microgravity?', selectedResearch = ['saffire12','etfe'];
  function openDemo() {
    S.demo=true; S.mission={description:'HYPOTHETICAL DEMO: four crew, 180-day deep-space transit; electrical overheating.',destination:'Deep-space transit',aiInterpretation:false};
    S.goal='investigate'; S.answers={};
    Object.entries(DEMO.inputs).forEach(([k,v])=>S.answers[k]={value:v,unknown:false,basis:'assumption',source:'example'});
    S.assessment=structuredClone(DEMO.assessment);S.explain=null;S.log=[];S.pinned=null;S.flow=null;S.reportMd=null;S.dirty=false;
    goTo('results');
  }
  function sourceLink(r,label) {return el('a',{href:'https://ntrs.nasa.gov/citations/'+r.source,target:'_blank',rel:'noopener noreferrer',text:label||'NASA original record ↗'});}
  function researchChart() {
    const box=el('div',{class:'card'},[el('h2',{text:'Measured flame spread · Saffire fabric tests'}),el('p',{class:'lede',text:'Reported average flame-spread rates in microgravity, at 20 cm/s airflow. Unit: millimetres per second (mm/s).'})]);
    const rows=[['I · 1-1 · concurrent',1.8,'40.6 cm wide · 21.7% O₂'],['I · 1-2 · opposed',1.3,'40.6 cm wide · 21.7% O₂'],['II · 2-5 · concurrent',2.1,'5 cm wide · 22.1% O₂']];
    const plot=el('div',{class:'measurement-chart',role:'img','aria-label':'Average flame spread: Saffire I concurrent 1.8, Saffire I opposed 1.3, Saffire II concurrent 2.1 millimetres per second. Axis begins at zero.'});
    rows.forEach(r=>plot.appendChild(el('div',{class:'measurement-row'},[el('div',{},[el('strong',{text:r[0]}),el('div',{class:'small',text:r[2]})]),el('div',{class:'bar-track'},[el('div',{class:'measurement-bar',style:'width:'+r[1]/2.5*100+'%'})]),el('strong',{text:String(r[1])})])));
    plot.appendChild(el('div',{class:'axis',text:'0                                     1                                     2                2.5 mm/s'}));box.appendChild(plot);
    box.appendChild(el('p',{class:'notice warn',text:'Widths, oxygen fractions and flow directions differ. This chart describes reported tests; it does not isolate a causal effect or predict fire risk. No uncertainty for these spread-rate averages is supplied in the cited summary; error bars are therefore omitted.'}));
    box.appendChild(el('p',{class:'small'},['Source file: 20170008805.pdf · slide 21 and Table I. SIBAL cotton/fiberglass fabric, orbital microgravity. Total pressure is not specified in this excerpt. ',sourceLink(RESEARCH[0],'Read original NASA report ↗'),' · ',el('a',{href:'/measurements.csv',download:'saffire-measurements.csv',text:'Download measurements & conditions (CSV)'})]));return box;
  }
  function renderResearch(st) {
    const card=el('div',{class:'card'},[el('h2',{text:'NASA combustion research explorer'}),el('p',{class:'lede',text:'Find experiments relevant to your research question. Three curated NASA-hosted original reports, verified on 14 November 2026. Research relevance is separate from the assessment and never changes its fire-screening index.'})]);
    const form=el('form',{class:'row'}),label=el('label',{class:'lbl',for:'research-question',text:'Your research question'}),input=el('input',{id:'research-question',type:'text',maxlength:'1000',placeholder:'e.g. How does weak airflow affect electrical wire flames?'});input.value=researchQuestion;
    card.appendChild(label);form.appendChild(el('div',{style:'flex:1 1 280px'},[input]));form.appendChild(el('button',{class:'btn primary',type:'submit',text:'Rank experiments'}));form.addEventListener('submit',e=>{e.preventDefault();researchQuestion=input.value.trim();renderStage();});card.appendChild(form);
    card.appendChild(el('details',{class:'sub'},[el('summary',{text:'How relevance is ranked'}),el('p',{class:'small',text:'Transparent keyword matching: one relevance point for each recognized topic shared by your question and an experiment, counted once per topic. Topics: electrical wiring, ventilation/flow, solid materials, microgravity, flame spread, oxygen/atmosphere, and smoke/products. Ties retain catalogue order. This is neither a scientific quality score nor a fire-risk score. It searches only these three records; unmatched questions receive no inferred match.'})]));st.appendChild(card);
    const ranked=rankResearch(researchQuestion);if(!ranked.some(r=>r.points))st.appendChild(el('p',{class:'notice',role:'status',text:'No recognized topic matches. Showing catalogue order; try terms such as wire, smoke, oxygen or ventilation.'}));
    const results=el('div',{class:'research-grid'});
    ranked.forEach((r,i)=>{const c=el('article',{class:'card'},[el('div',{class:'small',text:r.points?'Relevance position '+(i+1)+' · '+r.points+' matched topic'+(r.points===1?'':'s'):'No topic match'}),el('h3',{text:r.name}),el('p',{class:'small',text:r.year+' · '+r.facility}),el('p',{text:r.scope}),el('p',{class:'match-note',text:'Why this position: '+(r.matched.length?r.matched.join('; '):'no recognized topics')+'. Ties use catalogue order.'}),el('p',{class:'small',text:r.conditions}),sourceLink(r)]);
      const check=el('input',{type:'checkbox',id:'compare-'+r.id});check.checked=selectedResearch.includes(r.id);check.addEventListener('change',()=>{if(check.checked&&selectedResearch.length>=2){check.checked=false;const msg=document.getElementById('compare-status');msg.textContent='Select at most two experiments. Uncheck one first.';return;}selectedResearch=check.checked?[...selectedResearch,r.id]:selectedResearch.filter(x=>x!==r.id);renderStage();});
      c.appendChild(el('label',{class:'compare-label',for:'compare-'+r.id},[check,' Compare this experiment']));results.appendChild(c);});st.appendChild(results);
    const comparison=el('section',{class:'card'},[el('h2',{text:'Compare experiments side by side'}),el('p',{id:'compare-status',class:'small',role:'status',text:selectedResearch.length+' of 2 selected. Use the checkboxes above.'})]);
    const chosen=selectedResearch.map(id=>RESEARCH.find(r=>r.id===id));
    if(chosen.length){const fields=[['facility','Facility / gravity'],['material','Material'],['conditions','Test conditions'],['measures','Measurements'],['limits','Transfer limits'],['locator','Source location']];comparison.appendChild(table(['Metadata',...chosen.map(r=>r.name)],fields.map(([k,l])=>el('tr',{},[el('th',{scope:'row',text:l}),...chosen.map(r=>el('td',{text:r[k]}))])).concat([el('tr',{},[el('th',{scope:'row',text:'Original source'}),...chosen.map(r=>el('td',{},[sourceLink(r),el('div',{class:'small',text:r.file})]))])])));}
    st.appendChild(comparison);st.appendChild(researchChart());
  }
  function renderEvidenceGaps(a) {
    const box=el('div',{class:'card'},[el('h2',{text:'Missing answers and evidence limits'})]);
    const missing=a.inputs.missing||[];
    box.appendChild(el('h3',{text:'Unanswered input fields · '+missing.length}));
    box.appendChild(el('p',{class:'small',text:'These are missing scenario inputs, not unanswered scientific questions. The count does not measure research uncertainty.'}));
    if(missing.length)box.appendChild(el('ul',{class:'plain'},missing.map(x=>el('li',{text:typeof x==='string'?x:x.label||x.id||x.field}))));else box.appendChild(el('p',{text:'No missing fields reported by the engine for this assessment.'}));
    box.appendChild(el('h3',{text:'Scientific evidence limits'}));
    box.appendChild(el('p',{text:'The cited literature provides general findings, not validation of this design. Calculated quantities alone do not establish a design-specific ignition threshold here. Material, geometry, atmosphere and gravity must match before results can transfer.'}));
    box.appendChild(el('p',{class:'small',text:'This is a description of the evidence available to Astroflare, not a claim that these questions remain unresolved across all science. Findings are not ranked by consequence.'}));return box;
  }
