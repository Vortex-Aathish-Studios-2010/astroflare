  function openDemo() {
    S.demo=true; S.mission={description:'HYPOTHETICAL DEMO: four crew, 180-day deep-space transit; electrical overheating.',destination:'Deep-space transit',aiInterpretation:false};
    S.goal='investigate'; S.answers={};
    Object.entries(DEMO.inputs).forEach(([k,v])=>S.answers[k]={value:v,unknown:false,basis:'assumption',source:'example'});
    S.assessment=JSON.parse(JSON.stringify(DEMO.assessment));S.explain=null;S.log=[];S.pinned=null;S.flow=null;S.reportMd=null;S.dirty=false;
    goTo('results');
  }
  function renderEvidenceGaps(a) {
    const box=el('div',{class:'card'},[el('h2',{text:'Missing answers and evidence limits'})]);
    const missing=a.inputs.missing||[];
    box.appendChild(el('h3',{text:'Unanswered input fields · '+missing.length}));
    box.appendChild(el('p',{class:'small',text:'These are missing scenario inputs, not unanswered scientific questions. The count does not measure research uncertainty.'}));
    if(missing.length)box.appendChild(el('ul',{class:'plain'},missing.map(x=>el('li',{text:typeof x==='string'?x:x.label||x.id||x.field}))));else box.appendChild(el('p',{text:'No missing fields reported by the engine for this assessment.'}));
    box.appendChild(el('p',{class:'notice',text:'Electrical terminology: fault current integral (I²t) has units A²·s; it is not energy in joules. Resistive energy also requires resistance and the current history. Numerical results and units come from the original engine.'}));
    box.appendChild(el('h3',{text:'Scientific evidence limits'}));
    box.appendChild(el('p',{text:'The cited literature provides general findings, not validation of this design. Calculated quantities alone do not establish a design-specific ignition threshold here. Material, geometry, atmosphere and gravity must match before results can transfer.'}));
    box.appendChild(el('p',{class:'small',text:'This is a description of the evidence available to Astroflare, not a claim that these questions remain unresolved across all science. Findings are not ranked by consequence.'}));return box;
  }
