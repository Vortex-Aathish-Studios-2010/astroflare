// Verified document metadata, not a comprehensive experiment database.
const RESEARCH = [
 {id:'saffire12',name:'Saffire I & II · large-scale flame spread',year:'2017 report',facility:'Uncrewed Cygnus spacecraft; orbital microgravity',material:'SIBAL cotton/fiberglass fabric; additional silicone and PMMA samples',conditions:'Fabric comparison: 20 cm/s airflow; 21.7% initial O₂ for Saffire I, 22.1% for Saffire II (ISS readings). Sample widths differ.',measures:'Average flame-spread rate (mm/s); flame power estimates (W).',scope:'Large-scale material burning, flame spread and ventilation effects.',limits:'Different widths and initial oxygen fractions confound a direct size-effect comparison. These tests do not validate a spacecraft design.',source:'20170008805',file:'20170008805.pdf',locator:'Slides 20–21; Table I',tags:['material','flow','microgravity','flame']},
 {id:'etfe',name:'ETFE insulated wire · weak opposed flow',year:'2004 NTRS record / 2003 proceedings',facility:'JAMIC 10-second dropshaft and NASA KC-135 aircraft',material:'ETFE-insulated copper wire, AWG28; 0.32 mm core, 0.15 mm insulation thickness',conditions:'Duct flow controlled over 0–30 cm/s; varied oxygen concentration and N₂ or CO₂ dilution. Illustrated flame photographs use 35% O₂ with CO₂.',measures:'Flame-spread behavior and rate versus external flow; no digitized measurements included here.',scope:'Wire-insulation combustion under weak ventilation and different diluents.',limits:'Short microgravity time and thin, oxygen-enriched samples limit transfer to operational wiring systems. This is a NASA-hosted partner study, not an ISS flight experiment.',source:'20040053553',file:'20040053553.pdf',locator:'Proceedings pp. 177–181; Experimental section p. 178',tags:['wire','flow','microgravity','flame','oxygen']},
 {id:'saffire6',name:'Saffire VI · combustion products and fire growth',year:'2024 paper',facility:'Orbiting Cygnus spacecraft; final Saffire flight',material:'Cotton/fiberglass sheet, thick PMMA and other configurations; paper focuses on selected tests',conditions:'Reduced-pressure, oxygen-adjusted spacecraft atmosphere; conditions vary by sample (paper Table 1).',measures:'Gas concentrations, temperature and oxygen-consumption heat-release estimates.',scope:'Practical-scale fire growth and hazardous combustion products, including smoke/gas monitoring.',limits:'Preliminary, selected-test results; not a complete flight dataset. Conditions must be matched by sample before quantitative comparison.',source:'20240002981',file:'Saffire-ICES-2024-ICES-365-accepted final.pdf',locator:'ICES-2024-365, pp. 1–7; Table 1',tags:['smoke','material','microgravity','oxygen','flame']}
];
const TOPICS = {
 wire:{label:'electrical wiring',words:['wire','wires','wiring','electrical','etfe','insulation','arc']},
 flow:{label:'ventilation / flow',words:['flow','airflow','ventilation','velocity','vent','opposed','concurrent']},
 material:{label:'solid materials',words:['material','materials','fabric','cotton','fiberglass','pmma','polymer','solid']},
 microgravity:{label:'microgravity',words:['microgravity','micro','gravity','orbital','spacecraft','space']},
 flame:{label:'flame spread',words:['flame','flames','spread','spreading','combustion','burning','flammability']},
 oxygen:{label:'oxygen / atmosphere',words:['oxygen','o2','enriched','pressure','dilution','co2']},
 smoke:{label:'smoke / combustion products',words:['smoke','detection','detector','gas','gases','toxic','products','monoxide']}
};
function rankResearch(question) {
 const tokens=new Set(question.toLowerCase().match(/[a-z0-9]+/g)||[]);
 const topics=Object.keys(TOPICS).filter(k=>TOPICS[k].words.some(w=>tokens.has(w)));
 return RESEARCH.map((r,index)=>{const matched=topics.filter(k=>r.tags.includes(k));return {...r,matched:matched.map(k=>TOPICS[k].label),points:matched.length,order:index};}).sort((a,b)=>b.points-a.points||a.order-b.order);
}
if(typeof module!=='undefined')module.exports={RESEARCH,TOPICS,rankResearch};
