// Pure deterministic retrieval: no model calls and no fire-risk inputs.
const LUNAR_QUESTION='Which NASA experiments can inform a review of solid-material flammability in a ventilated lunar habitat?';
const TOPICS={solid:{label:'solid materials',words:['solid','solids','material','materials','fabric','cotton','fiberglass','pmma','silicone','fuel','fuels']},flame:{label:'flame spread / flammability',words:['flame','flames','spread','spreading','burn','burning','flammability','combustion']},flow:{label:'ventilation / airflow',words:['flow','airflow','ventilation','ventilated','vent','velocity','opposed','concurrent']},oxygen:{label:'oxygen / atmosphere',words:['oxygen','o2','atmosphere','enriched','concentration']},microgravity:{label:'microgravity',words:['microgravity','weightless','freefall','orbital']},smoke:{label:'combustion gases',words:['smoke','co','monoxide','gas','gases','products']}};
function tokensFor(q){return new Set((q.toLowerCase().match(/[a-z0-9]+/g)||[]));}
function topicsFor(q){const t=tokensFor(q);return Object.keys(TOPICS).filter(k=>TOPICS[k].words.some(w=>t.has(w)));}
function filterSummary(records){
 const ids=new Set(records.map(r=>r.id)),excluded=PSI_DATA.records.filter(r=>!ids.has(r.id));
 return `${records.length} of ${PSI_DATA.records.length} investigations match. Included (${records.length}): ${records.map(r=>r.name).join(', ')||'none'}. Excluded (${excluded.length}): ${excluded.map(r=>r.name).join(', ')||'none'}. ${records.length?'Top result: '+records[0].name+'.':'No experiment in the curated set matches these filters.'}`;
}
function rankResearch(question,filters={material:'any',gravity:'any',airflow:'any'},scenario={gravity:'lunar'}){
 const topics=topicsFor(question),tokens=tokensFor(question);const material=['pmma','fabric','silicone'].find(x=>tokens.has(x))||(tokens.has('cotton')||tokens.has('fiberglass')?'fabric':null);
 return PSI_DATA.records.filter(r=>
  (filters.material==='any'||filters.material==='solid'||r.materials.includes(filters.material))&&
  (filters.gravity==='any'||r.gravity===filters.gravity)&&
  (filters.airflow==='any'||filters.airflow==='forced'&&r.flowMode==='forced'||filters.airflow==='variable'&&r.coverage==='variable'||filters.airflow==='20'&&r.flowValues.includes(20)||r.directions.includes(filters.airflow))
 ).map(r=>{const matched=topics.filter(k=>r.tags.includes(k));const components=matched.map(k=>({label:TOPICS[k].label,points:2}));
  if(topics.includes('flow')&&r.coverage==='variable')components.push({label:'variable-flow investigation coverage',points:1});
  if(material&&r.materials.includes(material))components.push({label:'specific material '+material,points:2});
  if(material===null&&filters.material!=='any'&&filters.material!=='solid'&&r.materials.includes(filters.material))components.push({label:'selected material '+filters.material,points:2});
  if(scenario.gravity===r.gravity)components.push({label:'scenario gravity match',points:1});
  const mismatch=scenario.gravity!=='any'&&r.gravity!==scenario.gravity;
  return {...r,matched:matched.map(k=>TOPICS[k].label),points:components.reduce((a,x)=>a+x.points,0),components,gravityMismatch:mismatch};
 }).sort((a,b)=>b.points-a.points||a.order-b.order);
}
function overviewEvidenceAnswer(question,records){
 if(!records.length)return {gap:true,text:'No investigation matches the current filters. Reset a filter to see the closest NASA experiments.',citations:[]};
 if(/\b(safe|safest|probability|certify|certification|threshold|prediction|predict|battery|lithium|human|survive)\b/i.test(question))return {gap:true,text:'These NASA records report measured flame behaviour under stated conditions. For safe operating limits, fire prediction, habitat certification, batteries or health, start from the original NASA sources. The ranking here shows research relevance.',citations:records.slice(0,2).map(r=>r.id)};
 if(/\d/.test(question)&&/\b(at|for|when|predict|estimate|rate)\b/i.test(question)||/lunar|moon/i.test(question)&&/\b(rate|speed|velocity|threshold)\b/i.test(question))return {gap:true,text:'These records report measured values for the conditions NASA tested. No lunar-surface rate appears in them, so read each original test row for its exact conditions and use microgravity rates as reference points for new lunar tests.',citations:records.slice(0,2).map(r=>r.id)};
 const topics=topicsFor(question);
 if(!topics.length)return {gap:true,text:'This question is outside the topics in the curated NASA records. Try asking about a material, airflow, oxygen, microgravity or combustion gases.',citations:[]};
 const matched=records.filter(r=>topics.some(t=>r.tags.includes(t)));
 if(!matched.length)return {gap:true,text:'No record in the current filters covers this topic. Reset a filter to widen the search.',citations:[]};
 let text=matched.slice(0,2).map(r=>`[${r.id}] ${topics.includes('flow')?r.airflow+' ':''}${topics.includes('oxygen')?r.oxygen+' ':''}${topics.includes('smoke')||topics.includes('flame')?r.outcome+' ':''}${r.interpretation}`).join('\n\n');
 if(/lunar|moon|gravity/i.test(question))text+='\n\nLunar applicability: these are microgravity investigations, not lunar surface tests. Buoyancy, material geometry and ventilation must be evaluated at lunar gravity before transferring a result.';
 return {gap:false,text,citations:matched.slice(0,2).map(r=>r.id)};
}
// Resolve investigation and physical quantity before considering dashboard relevance.
function evidenceIntent(question){
 const q=question.toLowerCase().replace(/[–—]/g,'-');const ids=new Set();let unknownName=null;
 for(const match of q.matchAll(/\bsaffire[\s-]*(iii|ii|i|3|2|1)\b/g)){const n={i:1,ii:2,iii:3,'1':1,'2':2,'3':3}[match[1]];if(n===3)unknownName='Saffire III';else ids.add(n===2?'PSI-99':'PSI-98');}
 for(const match of q.matchAll(/\bpsi[\s-]*(\d+)\b/g)){const id='PSI-'+match[1];if(PSI_DATA.records.some(r=>r.id===id))ids.add(id);else unknownName=id;}
 if(/\bbass[\s-]*(ii|2)\b/.test(q))ids.add('PSI-25');
 const measures=[];
 if(/\bspread(?:ing)?\b/.test(q)&&/\b(rate|speed|velocity|fast|quickly|rapidly)\b/.test(q)||/\bflame[- ]speed\b/.test(q))measures.push('spreadRate');
 if(/\bburn(?:ing)?\b/.test(q)&&/\b(time|duration|long|last|lasted|seconds)\b/.test(q))measures.push('burnTime');
 if(/\b(airflow|air-flow|ventilation)\b/.test(q)||/\bair\s+(flow|speed|velocity)\b|\bflow\s+(rate|speed|velocity)\b/.test(q))measures.push('airflow');
 if(/\bcarbon monoxide\b|\bco\b/.test(q))measures.push('carbonMonoxide');
 if(/\boxygen\b|\bo2\b/.test(q))measures.push('oxygen');
 const run=q.match(/\b(?:run|sample|test)\s+(?:number\s+)?([a-z]\d+[a-z]?|\d+-\d+)\b/i)?.[1]?.toUpperCase();
 return {ids:[...ids],unknownName,measures,run,lunar:/\b(lunar|moon)\b/.test(q)};
}
function evidenceAnswer(question,records){
 const material=/\bsilicone\b/i.test(question)?'silicone':/\bpmma\b/i.test(question)?'pmma':/\bsibal\b|\bcotton\b|\bfiberglass\b/i.test(question)?'fabric':null;
 const intent=evidenceIntent(question),named=intent.ids.map(id=>PSI_DATA.records.find(r=>r.id===id)).map(r=>material?scenarioRecord(r,material):r);
 if(material)records=records.filter(r=>r.materials.includes(material)).map(r=>scenarioRecord(r,material));
 const gap=(text,rs=named)=>({gap:true,text,citations:rs.map(r=>r.id),sources:rs.map(r=>({id:r.id,row:null,file:r.sourceFile,url:r.downloadUrl})),mode:'deterministic'});
 if(intent.unknownName)return gap('The curated dataset does not include '+intent.unknownName+'. No measurement has been inferred.',[]);
 if(intent.ids.length>1)return gap('Please ask about one investigation at a time so its measurement and conditions stay attached to the correct source.');
 if(intent.lunar&&intent.measures.includes('spreadRate'))return gap('The curated studies were conducted in microgravity. NASA’s PSI database does not yet include a lunar-gravity flame-spread measurement; the LUCI and FM2 experiments are expected to add one.',named.length?named:PSI_DATA.records.slice(0,2));
 if(named.length&&/\b(safe|safest|probability|certify|certification|threshold|prediction|predict)\b/i.test(question))return gap('The selected evidence cannot establish a safe operating limit, predict a fire or certify a habitat.');
 if(!named.length&&!intent.measures.includes('spreadRate'))return overviewEvidenceAnswer(question,records);
 if(intent.measures.length!==1)return named.length?gap('Which measurement do you need: flame-spread rate, burn duration, airflow, oxygen or carbon monoxide?'):overviewEvidenceAnswer(question,records);
 if(/\b(?:at|under)\s+\d|\b(?:predict|estimate|calculate|extrapolate)\b/i.test(question))return gap('The curated evidence does not support a new numeric prediction for the requested conditions. Inspect the original test rows; no interpolation has been made.');
 const measure=intent.measures[0];
 if(named[0]?.id==='PSI-98'&&measure==='spreadRate'&&(!intent.run||['1-1','1-2'].includes(intent.run))&&(!material||material==='fabric')){
  const r=named[0],c=r.companion,rows=c.runs.filter(run=>!intent.run||run.id===intent.run);
  return {gap:false,mode:'deterministic',text:r.name+'’s selected PSI table does not report a flame-spread rate.\n\nNASA’s companion presentation reports average rates: '+rows.map(run=>'sample '+run.id+' — '+run.spreadRate+', '+run.direction.toLowerCase()+' flow').join('; ')+'. '+(rows.length===2?'Both used':'The specimen used')+' SIBAL fabric in microgravity at 20 cm/s.\n\nTable I (page 29) gives O₂ as '+rows.map(run=>run.oxygen+' for '+run.id).join(' and ')+'. These values come from the companion presentation, not the PSI CSV.',citations:[r.id,c.id],sources:[{id:r.id,row:null,file:r.sourceFile,url:r.downloadUrl},{id:c.id,row:'samples '+rows.map(run=>run.id).join(' and ')+' · Table I, page 29',file:c.file,url:c.url,recordUrl:c.source}]};
 }
 // A generic spread-rate lookup retrieves only records that have that quantity.
 const candidates=named.length?named:records.filter(r=>r.runs.some(x=>x.outcome.spreadRate&&x.outcome.spreadRate!=='Not reported'));
 if(!candidates.length)return gap('The currently retrieved PSI records do not report a flame-spread rate. Change the filters or name Saffire II.',[]);
 const r=candidates[0],selected=intent.run?r.runs.find(x=>x.id.toUpperCase()===intent.run):r.runs.find(x=>measure==='spreadRate'?x.outcome.spreadRate&&x.outcome.spreadRate!=='Not reported':true)||(material?r.runs[0]:undefined);
 if(intent.run&&!selected)return gap(r.name+' run '+intent.run+' is not among the selected curated rows. No measurement has been inferred.',[r]);
 if(!selected)return gap(r.name+'’s selected PSI table does not report a flame-spread rate.',[r]);
 const run=selected,raw=run.raw;let value,first,conditions;
 if(measure==='spreadRate'){
  value=run.outcome.spreadRate;
  if(!value||value==='Not reported')return gap(r.name+'’s selected PSI table does not report a flame-spread rate for run '+run.id+'.',[r]);
  first=r.name+' reported a flame spread rate of '+value+' for run '+run.id+'.';
  conditions='Conditions: '+run.material+'; microgravity; '+run.airflow+' '+run.direction.toLowerCase()+' flow; approximately '+run.oxygen.replace(/^[~\s]+/,'')+'% O₂ (derived per table Note 1).';
 }else if(measure==='burnTime'){
  value=run.outcome.burnTime;if(!value)return gap(r.name+'’s selected PSI table does not report a burn duration for run '+run.id+'.',[r]);
  if(!/\d/.test(value))return gap(r.name+' run '+run.id+' reports burn duration qualitatively as “'+value+'”, not as a numeric time.',[r]);
  first=r.name+' reported a burn duration of '+value+' for run '+run.id+'.';
 }else if(measure==='airflow'){
  value=run.airflow;if(value==='Not reported'||!value)return gap(r.name+'’s selected PSI row does not report a calibrated airflow velocity. Fan-display settings are not converted to cm/s.',[r]);
  first=r.name+' reported airflow of '+value+' for run '+run.id+'.';
 }else if(measure==='carbonMonoxide'){
  if(run.outcome.finalCO==null)return gap(r.name+'’s selected PSI table does not report a carbon monoxide concentration for run '+run.id+'.',[r]);
  first=r.name+' reported final CO of '+run.outcome.finalCO+' ppm for run '+run.id+' (initial CO: '+run.outcome.initialCO+' ppm).';
 }else if(measure==='oxygen'){
  value=run.oxygenInitial||run.oxygen;if(!value)return gap(r.name+'’s selected PSI row does not report oxygen concentration.',[r]);
  first=r.name+' reported '+(run.oxygenInitial?'initial O₂':'O₂')+' of '+value+' '+(run.oxygenUnit||'%')+' for run '+run.id+'.';
 }
 conditions=conditions||'Conditions: '+run.material+'; microgravity; '+(run.airflow==='Not reported'?'calibrated airflow Not reported':run.airflow+(run.direction?' '+run.direction.toLowerCase()+' flow':''))+'.';
 const source={id:r.id,row:run.id,file:r.sourceFile,url:r.downloadUrl};
 return {gap:false,text:first+'\n\n'+conditions,citations:[r.id],sources:[source],mode:'deterministic',measurement:measure,run:run.id,sourceColumn:measure==='spreadRate'?'?-g Spread Length':null};
}

// Display only material-matched curated rows; keep the original catalogue immutable.
function scenarioRecord(record,material='any'){
 if(material==='any'||material==='solid')return record;
 const runs=record.runs.filter(run=>material==='fabric'?/sibal|cotton|fiberglass/i.test(run.material):new RegExp(material,'i').test(run.material));
 const r={...record,runs,selectedMaterial:material,evidence:'Original PSI experimental table; selected rows '+runs.map(x=>x.id).join(', ')};
 if(!runs.length)return {...r,material:material.toUpperCase()+' is within this investigation’s scope; no selected curated row matches.',oxygen:'Not reported for selected material',airflow:'Not reported for selected material',outcome:'No measured outcome in the selected curated rows for '+material+'.',qualitative:'Investigation scope includes '+material+'; no outcome for that material is inferred from other specimens.',limits:'No material-matched outcome is present in the selected curated rows. Do not transfer an outcome from a different material.',evidence:'No selected curated row matches this material.',interpretation:'Retrieve and check the material-specific original runs before proposing a quantitative comparison.'};
 r.material=runs.map(run=>run.id+': '+run.material).join('; ');
 r.oxygen=runs.map(run=>run.id+': '+(run.oxygenInitial?run.oxygenInitial+'% by volume':run.oxygen+'% (table Note 1)')).join('; ');
 r.airflow=runs.map(run=>run.id+': '+run.airflow+(run.direction?' '+run.direction.toLowerCase():'')).join('; ');
 if(material==='silicone')return {...r,qualitativeOnly:true,limits:'Row 2-1 reports a qualitative silicone outcome in microgravity.',outcome:'Run 2-1: burn time reported as “Insignificant” (NASA’s qualitative description). Flame-spread rate: Not reported.',qualitative:'The source describes the burn as “Insignificant”.',interpretation:'This is the silicone result; the SIBAL spread rate belongs to run 2-5.'};
 r.outcome=runs.map(run=>run.outcome.spreadRate&&run.outcome.spreadRate!=='Not reported'?run.id+': flame spread '+run.outcome.spreadRate:run.outcome.finalCO!=null?run.id+': final CO '+run.outcome.finalCO+' ppm (initial '+run.outcome.initialCO+' ppm); spread rate Not reported':run.id+': burn time '+run.outcome.burnTime+'; spread rate Not reported').join('; ');
 return r;
}
function runCoverage(record,filters){
 const r=scenarioRecord(record,filters.material),flow=filters.airflow;
 const matches=r.runs.filter(run=>flow==='20'?parseFloat(run.airflow)===20:['concurrent','opposed'].includes(flow)?run.direction?.toLowerCase()===flow:true);
 const directionRequested=['concurrent','opposed'].includes(flow);
 const text=!matches.length?'Study-level match only. No curated run matches '+(filters.material==='any'?'the selected material':filters.material)+' and '+(directionRequested?flow+' flow':'the selected conditions')+' together. '+(r.runs.length?'Displayed '+r.runs.map(run=>'run '+run.id+(run.direction?' used '+run.direction.toLowerCase()+' flow':' has no reported run-level direction')).join('; ')+'. ':'No material-matched row is curated. ')+(directionRequested?'These displayed observations are not a measured '+flow+'-flow result for this selection.':''):'Curated run matches: '+matches.map(run=>run.id).join(', ')+'. '+(['variable','forced'].includes(flow)?'Flow scope is matched at investigation level; calibrated run velocity is only shown where reported.':'Conditions remain attached to each original row.');
 return {matches,text};
}
function researchDecision(records,filters,scenario){
 const empty=!records.length,material=filters.material,gravity=scenario.gravity==='lunar'?'lunar surface':scenario.gravity==='any'?'the proposed scenario':scenario.gravity;
 const saffire=records.find(r=>r.id==='PSI-99');let measured,missing,step,fixed,variable='gravity regime',source,run;
 if(empty){measured='No curated NASA investigation matches these filters.';missing='No curated experiment matches this selection. Reset a filter to see the closest NASA experiments.';variable='material / gravity / airflow coverage';fixed='Define the material, atmosphere, geometry and ignition protocol before any test.';step='Proposed research scoping: broaden one filter or locate a matching NASA record before choosing a numerical baseline.';}
 else if(saffire&&material==='silicone'){
  source=saffire;run='2-1';measured='Saffire II run 2-1: silicone burn time was reported as “Insignificant” (qualitative). No flame-spread rate is reported. Conditions: microgravity, 20 cm/s concurrent flow, approximately 21.5% O₂.';
  missing='Test this silicone specimen in '+gravity+' conditions, and record pressure, temperature and a numeric spread rate.';
  fixed='Silicone specimen geometry, approximately 21.5% O₂ and 20 cm/s concurrent airflow; choose and document common pressure, temperature and ignition conditions.';
  step='Proposed follow-up analysis: compare microgravity and '+gravity+' conditions with the same silicone configuration. Determine whether sustained spread occurs before comparing a rate; do not convert “Insignificant” into zero.';
 }else if(saffire&&(material==='any'||material==='solid'||material==='fabric')){
  source=saffire;run='2-5';measured='Saffire II reported a flame spread rate of 2.1 mm/s for run 2-5. Conditions: SIBAL cotton/fiberglass, microgravity, 20 cm/s concurrent flow, approximately 22.1% O₂ (derived per Note 1).';
  missing='Test this material in '+gravity+' conditions, and define the habitat’s pressure, temperature, geometry and ignition conditions.';
  fixed='SIBAL material, 20 cm/s concurrent airflow and approximately 22.1% O₂; resolve the source’s thickness ambiguity and define common geometry, pressure, temperature and ignition conditions.';
  step='Proposed follow-up analysis: develop and validate a matched-condition flame-spread model, then vary gravity from microgravity to '+gravity+'. Compare spread rate in mm/s; do not treat the NASA rate as a lunar prediction.';
 }else{
  source=records[0];run=source.runs[0]?.id;measured=source.name+': '+source.outcome;
  missing='Obtain a material-matched flame-spread measurement for '+gravity+' conditions; the selected rows report concentration and burn-duration data.';
  fixed='Selected material and specimen geometry, oxygen, pressure, temperature, airflow and ignition protocol; numerical settings must be sourced or explicitly chosen as proposed test inputs.';
  step='Proposed next step: retrieve the material-specific run files and measure or derive a traceable spread-rate baseline before a gravity-transfer analysis.';
 }
 if(scenario.gravity==='microgravity'&&!empty){variable='airflow velocity';step='Proposed follow-up analysis: vary airflow around the documented configuration, holding gravity, material, oxygen, geometry, pressure, temperature and ignition fixed. Validate any computed rate against matched measurements.';missing='Microgravity context matches, but exact specimen and habitat conditions still need to be matched; no safety validation follows.';}
 let coverage=source?runCoverage(source,filters):null;
 if(coverage&&!coverage.matches.some(x=>x.id===run)){
  missing=coverage.text+' '+missing;
  step='Proposed next step: retrieve and verify a '+(material==='any'?'material-matched':material)+' '+(['concurrent','opposed'].includes(filters.airflow)?filters.airflow+'-flow ':'')+'run before selecting a quantitative baseline. The displayed observation does not establish a measurement under both selected conditions.';
  variable='airflow direction / matched-run coverage';fixed='For a future comparison, hold the material, specimen geometry, oxygen, pressure, temperature, airflow speed and ignition protocol fixed. Verify these inputs in a run with the requested direction first; the displayed run is contextual evidence only.';
 }
 const rateBaseline=source?.id==='PSI-99'&&run==='2-5';
 const rationale=source?(records[0].id===source.id?source.name+' ranks first and supplies the supporting '+(rateBaseline?'measured spread rate':'observation')+' used below.':records[0].name+' ranks first for the broad question; '+source.name+' supplies the '+(rateBaseline?'measured spread rate':'supporting observation')+' used in the proposed follow-up.'):'No study matches these filters, so there is no supporting measurement for a follow-up baseline.';
 const citations=source?[{id:source.id,row:run,url:source.downloadUrl,record:source.source}]:[];
 const text=['ASTROFLARE — PROPOSED RESEARCH BRIEF','Question: '+LUNAR_QUESTION,'Selected material: '+material+'; scenario gravity: '+scenario.gravity+'; experiment gravity filter: '+filters.gravity+'; airflow filter: '+filters.airflow,'Evidence choice: '+rationale,coverage?.text,'What NASA measured: '+measured,'What is missing: '+missing,'Next research step (proposal, not performed): '+step,'Variable to study: '+variable,'Hold fixed: '+fixed,...citations.map(c=>'Source: '+c.id+(c.row?' row '+c.row:'')+' | '+c.url+' | '+c.record),'No lunar fire-risk prediction or certification is implied.'].filter(Boolean).join('\n\n');
 return {empty,measured,missing,step,variable,fixed,citations,text,rationale,coverage};
}
function latestOnlyAnswers(){let sequence=0;return {cancel(){sequence++;},submit(question,resolve,onPending,onResult,onError){const id=++sequence;onPending(question);return Promise.resolve().then(()=>resolve(question)).then(answer=>{if(id===sequence)onResult(answer,question);},error=>{if(id===sequence)onError(error,question);});}};}
