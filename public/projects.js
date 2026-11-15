  // Research projects: name, save, reopen and export an evidence review. Stored in this browser only; mission-screening
  // saves use a different key and are never read or changed here.
  const PROJECTS_KEY='astroflareResearchProjects',PROJECTS_MAX=25;
  const PROJECT_FILTERS={material:['any','fabric','pmma','silicone','gas'],gravity:['any','microgravity','lunar','earth'],airflow:['any','forced','variable','20','concurrent','opposed','quiescent']};
  const PROJECT_SCENARIO_GRAVITY=['lunar','microgravity','earth','any'];
  const PROJECTS={status:'',statusKind:'',lastSavedId:null};
  function projectsRead(){try{const raw=localStorage.getItem(PROJECTS_KEY);if(!raw)return {list:[],error:''};const data=JSON.parse(raw);if(!Array.isArray(data))throw Error('shape');return {list:data.filter(projectValid),error:data.length&&!data.filter(projectValid).length?'Saved projects on this browser could not be read.':''};}catch{return {list:[],error:'Saved projects on this browser could not be read, so none are shown. Your mission-screening save is not affected.'};}}
  function projectsWrite(list){try{localStorage.setItem(PROJECTS_KEY,JSON.stringify(list));return true;}catch{return false;}}
  function projectValid(p){
    const ids=PSI_DATA.records.map(r=>r.id);
    return p&&typeof p==='object'&&typeof p.id==='string'&&typeof p.name==='string'&&typeof p.question==='string'&&p.filters&&Object.keys(PROJECT_FILTERS).every(k=>PROJECT_FILTERS[k].includes(p.filters[k]))&&p.scenario&&PROJECT_SCENARIO_GRAVITY.includes(p.scenario.gravity)&&Array.isArray(p.selected)&&p.selected.length<=2&&p.selected.every(id=>ids.includes(id));
  }
  function projectRecords(question,filters,scenario){return rankResearch(question,filters,scenario).map(r=>scenarioRecord(r,filters.material));}
  function projectSnapshot(name){
    const records=projectRecords(EXPLORER.question,EXPLORER.filters,EXPLORER.scenario);
    const d=researchDecision(records,EXPLORER.filters,EXPLORER.scenario);d.text=d.text.replace(LUNAR_QUESTION,EXPLORER.question);
    const used=[...new Set(records.flatMap(r=>EXPLORER.selected.includes(r.id)?r.runs.map(x=>r.id+':'+x.id):[]))];
    return {kind:'astroflare-research-project',formatVersion:1,id:'p'+Date.now().toString(36)+Math.random().toString(36).slice(2,6),name,savedAt:new Date().toISOString(),datasetVersion:PSI_DATA.version,
      question:EXPLORER.question,filters:{...EXPLORER.filters},scenario:{...EXPLORER.scenario},selected:[...EXPLORER.selected],guideMaterial:GUIDE.material,
      ranking:records.map((r,i)=>({rank:i+1,id:r.id,name:r.name,points:r.points})),sourceRuns:used,
      brief:{measured:d.measured,missing:d.missing,proposedNextStep:d.step,variable:d.variable,holdFixed:d.fixed,citations:d.citations.map(c=>({id:c.id,row:c.row,url:c.url})),text:d.text},
      note:'Research relevance ranking. Saved on this browser only.'};
  }
  function projectMarkdown(p){
    const rec=id=>PSI_DATA.records.find(r=>r.id===id),L=[];
    L.push('# '+p.name,'','*AstroFlare research project · saved '+p.savedAt.slice(0,10)+' · dataset version '+p.datasetVersion+'*','');
    L.push('## Research question and scenario','',p.question,'','- Scenario gravity: '+p.scenario.gravity,'- Material filter: '+p.filters.material,'- Experiment gravity filter: '+p.filters.gravity,'- Airflow filter: '+p.filters.airflow,'');
    L.push('## Experiments considered (research relevance ranking)','');p.ranking.forEach(r=>L.push(r.rank+'. '+r.name+' ('+r.id+'), '+r.points+' relevance points'));
    L.push('','Selected for comparison: '+(p.selected.map(id=>{const r=rec(id);return r?r.name+' ('+id+')':id;}).join(', ')||'none'));
    if(p.sourceRuns.length)L.push('','Runs in the compared investigations: '+p.sourceRuns.join(', '));
    L.push('','## Measured evidence (reported by NASA)','',p.brief.measured,'','This describes what the cited experiment reported under its own conditions.','');
    L.push('## Next conditions to test','',p.brief.missing,'');
    L.push('## Proposed research (a suggestion, not a result)','',p.brief.proposedNextStep,'','- Variable to study: '+p.brief.variable,'- Hold fixed: '+p.brief.holdFixed,'');
    L.push('## Citations','');p.brief.citations.forEach(c=>L.push('- NASA PSI '+c.id+', row '+c.row+': '+c.url));
    const ids=[...new Set([...p.ranking.map(r=>r.id)])];ids.forEach(id=>{const r=rec(id);if(r)L.push('- '+r.name+' record: '+r.source+' (file v'+r.fileVersion+', verified '+r.verifiedOn+')');});
    L.push('','---','Research relevance ranking, not a measure of safety effectiveness. Each measurement is reported for its own test conditions (microgravity unless stated). AstroFlare is an independent project built on public NASA PSI data.');
    return L.join('\n')+'\n';
  }
  function projectSlug(name){return (name||'project').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,40)||'project';}
  function setProjectStatus(text,kind){PROJECTS.status=text;PROJECTS.statusKind=kind||'';const s=document.getElementById('project-status');if(s){s.textContent=text;s.className='project-status '+(kind||'');}}
  function saveProject(name){
    name=(name||'').trim().replace(/\s+/g,' ').slice(0,80);
    if(!name){setProjectStatus('Give the project a name first. Nothing was saved.','bad');const i=document.getElementById('project-name');if(i){i.setAttribute('aria-invalid','true');i.focus();}return false;}
    const {list}=projectsRead(),existing=list.findIndex(p=>p.name.toLowerCase()===name.toLowerCase()),snap=projectSnapshot(name);
    if(existing>=0)snap.id=list[existing].id;
    const next=existing>=0?list.map((p,i)=>i===existing?snap:p):[snap,...list].slice(0,PROJECTS_MAX);
    if(!projectsWrite(next)){setProjectStatus('This browser would not save the project (storage is blocked or full). You can still download it with the export buttons after saving is available, or copy the research brief.','bad');return false;}
    PROJECTS.lastSavedId=snap.id;refreshProjectList();setProjectStatus((existing>=0?'Updated “':'Saved “')+name+'” on this browser only.','ok');return true;
  }
  function openProject(id){
    const p=projectsRead().list.find(x=>x.id===id);if(!p){setProjectStatus('That project could not be found or is damaged.','bad');return;}
    EXPLORER.question=p.question;EXPLORER.questionDraft=p.question;EXPLORER.filters={...p.filters};EXPLORER.scenario={...p.scenario};EXPLORER.selected=[...p.selected];if(GUIDE_MATERIALS[p.guideMaterial])GUIDE.material=p.guideMaterial;
    const note=p.datasetVersion!==PSI_DATA.version?' The evidence collection has been updated since (saved '+p.datasetVersion+', now '+PSI_DATA.version+'); ranking uses the current records.':'';
    EXPLORER.change='Project “'+p.name+'” restored: question, filters, ranking, comparison and takeaway were rebuilt together.'+note;EXPLORER.ask='';EXPLORER.askDraft='';cancelEvidence();
    PROJECTS.status='Opened “'+p.name+'”.'+note;PROJECTS.statusKind='ok';refreshResearch('project-status');
  }
  function deleteProject(id){const {list}=projectsRead(),p=list.find(x=>x.id===id);if(!p)return;if(projectsWrite(list.filter(x=>x.id!==id))){refreshProjectList();setProjectStatus('Deleted “'+p.name+'” from this browser.','ok');}else setProjectStatus('This browser would not update saved projects.','bad');}
  function exportProject(id,kind){
    const p=projectsRead().list.find(x=>x.id===id);if(!p){setProjectStatus('That project could not be found or is damaged.','bad');return;}
    try{if(kind==='md')download('astroflare-'+projectSlug(p.name)+'.md','text/markdown',projectMarkdown(p));else download('astroflare-'+projectSlug(p.name)+'.json','application/json',JSON.stringify(p,null,2)+'\n');setProjectStatus('Downloaded the '+(kind==='md'?'Markdown':'JSON')+' export of “'+p.name+'”.','ok');}
    catch{setProjectStatus('The download could not start in this browser.','bad');}
  }
  function refreshProjectList(){const old=document.getElementById('project-list');if(old)old.replaceWith(renderProjectList());}
  function renderProjectList(){
    const {list,error}=projectsRead(),box=el('div',{id:'project-list'});
    if(error)box.appendChild(el('p',{class:'notice warn',role:'alert',text:error}));
    if(!list.length){box.appendChild(el('p',{class:'small',id:'project-empty',text:'No saved projects yet. Name the current review above and choose Save project.'}));return box;}
    const ul=el('ul',{class:'project-items'});
    list.forEach(p=>{const b=(label,fn,extra)=>{const x=el('button',{type:'button',class:'btn small-btn',text:label,'aria-label':label+': '+p.name});if(extra)x.id=extra+p.id;x.addEventListener('click',fn);return x;};
      ul.appendChild(el('li',{class:'project-item','data-project-id':p.id},[el('div',{},[el('strong',{text:p.name}),el('p',{class:'small',text:'Saved '+p.savedAt.slice(0,10)+' · '+(p.selected.length?'comparing '+p.selected.join(' and '):'no comparison')+' · dataset '+p.datasetVersion})]),el('div',{class:'row'},[b('Open',()=>openProject(p.id),'open-'),b('Markdown',()=>exportProject(p.id,'md'),'md-'),b('JSON',()=>exportProject(p.id,'json'),'json-'),b('Delete',()=>deleteProject(p.id),'del-')])]));});
    box.appendChild(ul);return box;
  }
  function renderProjects(st){
    const box=el('section',{class:'card projects',id:'research-projects','aria-labelledby':'projects-title'},[el('h2',{id:'projects-title',text:'Research projects'}),el('p',{class:'lede',text:'Save this review, come back to it later and export it as a document.'}),el('p',{class:'storage-note',id:'project-storage-note',text:'Saved on this browser only.'})]);
    const form=el('form',{id:'project-form',class:'project-form'});form.appendChild(el('label',{class:'lbl',for:'project-name',text:'Project name'}));
    const name=el('input',{id:'project-name',type:'text',maxlength:'80',autocomplete:'off',placeholder:'For example: SIBAL fabric, lunar cabin review'});name.addEventListener('input',()=>name.removeAttribute('aria-invalid'));
    const save=el('button',{type:'submit',class:'btn primary',id:'save-project',text:'Save project'});form.appendChild(el('div',{class:'row'},[el('div',{style:'flex:1 1 280px'},[name]),save]));
    form.addEventListener('submit',e=>{e.preventDefault();saveProject(name.value);});box.appendChild(form);
    box.appendChild(el('p',{class:'project-status '+PROJECTS.statusKind,id:'project-status',role:'status','aria-live':'polite',tabindex:'-1',text:PROJECTS.status}));
    box.appendChild(renderProjectList());
    box.appendChild(el('p',{class:'small',text:'A project stores your question, filters, selected investigations, the source and run identifiers, the dataset version and the research brief with its citations. Exports separate measured evidence, gaps and proposed research. Your mission-screening save is kept separately.'}));
    st.appendChild(box);
  }
