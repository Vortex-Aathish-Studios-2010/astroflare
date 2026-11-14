// Pure deterministic retrieval: no model calls and no fire-risk inputs.
const LUNAR_QUESTION='Which NASA experiments can inform a review of solid-material flammability in a ventilated lunar habitat?';
const TOPICS={solid:{label:'solid materials',words:['solid','solids','material','materials','fabric','cotton','fiberglass','pmma','silicone','fuel','fuels']},flame:{label:'flame spread / flammability',words:['flame','flames','spread','spreading','burn','burning','flammability','combustion']},flow:{label:'ventilation / airflow',words:['flow','airflow','ventilation','ventilated','vent','velocity','opposed','concurrent']},oxygen:{label:'oxygen / atmosphere',words:['oxygen','o2','atmosphere','enriched','concentration']},microgravity:{label:'microgravity',words:['microgravity','weightless','freefall','orbital']},smoke:{label:'combustion gases',words:['smoke','co','monoxide','gas','gases','products']}};
function tokensFor(q){return new Set((q.toLowerCase().match(/[a-z0-9]+/g)||[]));}
function topicsFor(q){const t=tokensFor(q);return Object.keys(TOPICS).filter(k=>TOPICS[k].words.some(w=>t.has(w)));}
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
function evidenceAnswer(question,records){
 if(!records.length)return {gap:true,text:'Evidence gap: no investigations match the current filters. Reset a filter to retrieve evidence.',citations:[]};
 if(/\b(safe|safest|probability|certify|certification|threshold|prediction|predict|battery|lithium|human|survive)\b/i.test(question))return {gap:true,text:'Evidence gap: these records cannot establish a safe operating limit, predict a fire, certify a lunar habitat, or answer battery/health questions. The ranking is research relevance only.',citations:records.slice(0,2).map(r=>r.id)};
 if(/\d/.test(question)&&/\b(at|for|when|predict|estimate|rate)\b/i.test(question)||/lunar|moon/i.test(question)&&/\b(rate|speed|velocity|threshold)\b/i.test(question))return {gap:true,text:'Evidence gap: no numeric prediction is supported for the requested conditions. No lunar-surface rate is measured in these records. Inspect each original test row; do not interpolate or transfer a microgravity rate to a lunar habitat.',citations:records.slice(0,2).map(r=>r.id)};
 const topics=topicsFor(question);
 if(!topics.length)return {gap:true,text:'Evidence gap: this question has no supported topic in the curated records. Try material, airflow, oxygen, microgravity or combustion gases. No answer has been inferred.',citations:[]};
 const matched=records.filter(r=>topics.some(t=>r.tags.includes(t)));
 if(!matched.length)return {gap:true,text:'Evidence gap: no currently filtered record covers the recognized topic.',citations:[]};
 let text=matched.slice(0,2).map(r=>`[${r.id}] ${topics.includes('flow')?r.airflow+' ':''}${topics.includes('oxygen')?r.oxygen+' ':''}${topics.includes('smoke')||topics.includes('flame')?r.outcome+' ':''}${r.interpretation}`).join('\n\n');
 if(/lunar|moon|gravity/i.test(question))text+='\n\nLunar applicability: these are microgravity investigations, not lunar surface tests. Buoyancy, material geometry and ventilation must be evaluated at lunar gravity before transferring a result.';
 return {gap:false,text,citations:matched.slice(0,2).map(r=>r.id)};
}
