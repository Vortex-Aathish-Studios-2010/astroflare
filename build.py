import pathlib,json,re,zipfile,io,base64
p=pathlib.Path(__file__).parent
(p/"dist/server").mkdir(parents=True,exist_ok=True)
h=(p/'sources/original-interface.html').read_text()
h=re.sub(r'let[-\s\u2011\u2013]through energy(?: of the fault)?(?: \((?:I²t|I2t)\))?', 'fault current integral (I²t)', h, flags=re.I)
h=h.replace('<title>Astroflare | Guided hazard assessment</title>','<title>Astroflare | Assessment & NASA combustion research</title>')
h=h.replace('<div class="row noprint">','<div class="row noprint">\n    <button class="btn small-btn" id="demoBtn" type="button">Open hypothetical demo</button>\n    <button class="btn small-btn" id="researchBtn" type="button">NASA research</button>',1)
h=h.replace('    const e = document.createElement(tag);','    const e = document.createElement(tag);\n    if (props && typeof props.text === "string") props.text = props.text.replace(/Most consequential unresolved issue/gi, "One condition to review (not ranked)");')
h=h.replace('report: renderReportStage }','report: renderReportStage, research: renderResearch }')
h=h.replace('    const a = S.assessment;\n    if (S.dirty)', '''    const a = S.assessment;
    if (S.demo) st.appendChild(el("div", {class:"notice warn",role:"status",text:"HYPOTHETICAL DEMO · All inputs are illustrative assumptions, not spacecraft data. These populated results were returned by the original Astroflare engine on 14 November 2026 ("+DEMO.engineVersion+"). Edit answers and run again for a fresh remote assessment."}));
    if (S.dirty)''',1)
h=h.replace('    st.appendChild(renderOverview(a));','    st.appendChild(renderOverview(a));\n    st.appendChild(renderEvidenceGaps(a));',1)
h=h.replace('st.appendChild(renderFindings(a)); st.appendChild(renderInvestigate(a));','st.appendChild(renderFindings(a)); st.appendChild(secDetails("Investigate, compare answers and ask questions", renderInvestigate(a)));')
h=h.replace('    (a.summary.paragraphs || [a.summary.text]).forEach(function (t) { card.appendChild(el("p", { text: t })); });','    (a.summary.paragraphs || [a.summary.text]).filter(t => !/Most consequential unresolved issue/i.test(t)).forEach(function (t) { card.appendChild(el("p", { text: t })); });')
h=h.replace('["gap", "Information gaps"]','["gap", "Unanswered input fields"]')
h=h.replace('gap: "Information gap"','gap: "Unanswered input"')
h=h.replace('S.assessment = a; S.explain', 'S.demo = false; S.assessment = a; S.explain')
h=h.replace('    $("saveBtn").addEventListener', '''    $("demoBtn").addEventListener("click", openDemo);
    $("researchBtn").addEventListener("click", function () { goTo("research"); });
    $("envSec").addEventListener("toggle", function () { if(this.open && !this.dataset.loaded) {this.dataset.loaded="true";loadFlares();} });
    $("saveBtn").addEventListener''',1)
h=h.replace('S.stage = "mission"; S.reached = { mission: true };','S.demo=false; S.stage = "mission"; S.reached = { mission: true };')
h=h.replace('S.assessment = null; S.interp = null;','S.demo=false; S.assessment = null; S.interp = null;')
h=h.replace('    bindControls();\n    Promise.all([api("/api/schema"), api("/api/status").catch(function () { return null; })]).then(function (r) {\n      S.schema = r[0].schema; S.guide = r[0].guide; S.examples = r[0].examples; S.methodology = r[0].methodology; S.aiAvailable = !!(r[1] && r[1].analysis && r[1].analysis.explanation.available);\n      renderMethod(); goTo("mission");\n    }).catch(function (e) { $("stage").appendChild(el("div", { class: "card" }, [el("h2", { text: "Astroflare could not start" }), el("p", { text: e.message })])); });\n    loadFlares();', '''    S.schema=BOOTSTRAP.schema; S.guide=BOOTSTRAP.guide; S.examples=BOOTSTRAP.examples; S.methodology=BOOTSTRAP.methodology;
    bindControls(); renderMethod(); goTo("mission");
    api("/api/status").then(r=>{S.aiAvailable=AI_ENABLED && !!(r.analysis && r.analysis.explanation && r.analysis.explanation.available);}).catch(()=>{});''')
h=h.replace('  function start() {','  let started=false;\n  function start() {\n    if(started)return; started=true;')
h=h.replace('S.reportMd = r.markdown; S.reportJson = r.report;', 'S.reportMd = r.markdown.replace(/Most consequential unresolved issue/gi, "One condition to review (not ranked)"); S.reportJson = JSON.parse(JSON.stringify(r.report).replace(/Most consequential unresolved issue/gi, "One condition to review (not ranked)"));')
h=h.replace('  function renderMission(st) {','''  function renderMission(st) {
    const intro=el("div",{class:"card demo-intro"},[el("h2",{text:"Explore a complete assessment in one click"}),el("p",{class:"lede",text:"Try an illustrative electrical-overheating scenario, or find NASA combustion experiments for your own research question."})]);
    const demo=el("button",{type:"button",class:"btn primary",text:"Open hypothetical demo results"});demo.addEventListener("click",openDemo);
    const research=el("button",{type:"button",class:"btn",text:"Explore NASA combustion research"});research.addEventListener("click",()=>goTo("research"));
    intro.appendChild(el("div",{class:"row"},[demo,research]));intro.appendChild(el("p",{class:"small mt",text:"Demo inputs are hypothetical assumptions. Research relevance is separate from fire-risk screening."}));st.appendChild(intro);''')
# Keep solar context out of the main assessment; fetch only when explicitly expanded.
start=h.index('  <details class="sec noprint" id="envSec">');end=h.index('  <details class="sec method',start)
solar=h[start:end].replace('Loading</span>','Not loaded</span>').replace('Solar activity, last 30 days (context only)','Optional appendix: solar activity (unrelated to cabin fire screening)')
h=h[:start]+h[end:]
h=h.replace('</div>\n<script>', '</div>\n<footer class="wrap small"><p>Interface copied from <a href="https://astroflare.onrender.com/">Astroflare</a>. Fresh assessments use its original remote engine. No assessment engine is hosted in this copy. <a href="/documentation">Sources, limitations & deployment</a> · <a href="/source.zip" download="astroflare-source.zip">Download source code</a>.</p>'+solar+'</footer>\n<script>',1)
css='''
.demo-intro {background:var(--accent-soft);border-color:#bfd0e2}
.research-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.research-grid h3{margin:8px 0}.research-grid p{margin-top:10px}.match-note{font-size:13px;color:var(--accent)}.compare-label{display:block;border-top:1px solid var(--line);margin-top:16px;padding-top:12px;cursor:pointer}.measurement-row{display:grid;grid-template-columns:200px 1fr 35px;align-items:center;gap:12px;margin:18px 0}.bar-track{background:#eef1f5;height:24px}.measurement-bar{background:#2b5d8a;height:100%}.axis{margin-left:212px;white-space:pre;font:11px var(--mono);color:var(--muted);overflow:hidden}.measurement-chart{padding:8px 0}.research-grid .card{margin-bottom:0}th[scope=row]{min-width:120px}.tablewrap td{min-width:180px}.btn{min-height:40px}footer details{margin-top:16px}
@media(max-width:900px){.research-grid{grid-template-columns:1fr}.measurement-row{grid-template-columns:145px 1fr 30px;gap:8px}.axis{margin-left:153px}.brand-sub{max-width:230px}.top .row{width:100%}}@media(max-width:400px){.measurement-row{grid-template-columns:110px 1fr 28px;font-size:12px}.axis{margin-left:118px}.top .btn{flex:1 1 auto}}'''
h=h.replace('</style>',css+'\n</style>',1)
# Research-first upgrade; preserve the same project, legacy assessment and relay.
h=h.replace('<title>Astroflare | Assessment & NASA combustion research</title>','<title>AstroFlare | Flame in Freefall evidence explorer</title>')
h=h.replace('Guided hazard screening for mission leads','Flame in Freefall · NASA PSI evidence')
h=h.replace('<button class="btn small-btn" id="demoBtn" type="button">Open hypothetical demo</button>', '<button class="btn small-btn" id="homeBtn" type="button">Home</button><button class="btn small-btn" id="demoBtn" type="button">Lunar habitat demo</button><button class="btn small-btn" id="missionBtn" type="button">Mission screening</button>')
h=h.replace('$("demoBtn").addEventListener("click", openDemo);','$("demoBtn").addEventListener("click", openLunarDemo);$("homeBtn").addEventListener("click",()=>goTo("home"));$("missionBtn").addEventListener("click",()=>goTo("mission"));')
h=h.replace('research: renderResearch }','research: renderResearch, home: renderHome }')
h=h.replace('S.stage = stage; S.reached[stage] = true;', 'S.stage = stage; document.body.classList.toggle("research-active", stage === "research" || stage === "home"); S.reached[stage] = true;')
h=h.replace('st.querySelector("h2")','st.querySelector("h1,h2")')
h=h.replace('bindControls(); renderMethod(); goTo("mission");','bindControls(); renderMethod(); goTo(location.hash === "#lunar-demo" ? "research" : "home");')
h=h.replace('class: "tablewrap"', 'class: "tablewrap", tabindex: "0", role: "region", "aria-label": "Scrollable comparison or data table"')
h=h.replace('Interface copied from', 'Screening interface adapted from')
h=h.replace('</style>',(p/'public/font-faces.css').read_text()+'\n'+(p/'public/explorer.css').read_text()+'\n</style>',1)

# Judge reliability: stage history, persistent report errors and explicit recovery.
h=h.replace('    renderStepper(); renderContext(); renderStage();', '    renderStepper(); renderContext(); renderStage(); syncNavigation(stage);',1)
h=h.replace('goTo(location.hash === "#lunar-demo" ? "research" : "home");','restoreNavigation();')
h=h.replace('S.stage = "report"; S.reportMd = null;', 'S.stage = "report"; S.reportMd = null; S.reportErr = null;')
h=h.replace('S.reportErr = null; } else busy(p, "Assembling the report"); card.appendChild(p);', '''} else busy(p, "Assembling the report"); card.appendChild(p);
      if(S.reportErr){const retry=el("button",{type:"button",class:"btn primary",text:"Retry report"});retry.addEventListener("click",prepareReport);const back=el("button",{type:"button",class:"btn",text:"Back to results"});back.addEventListener("click",()=>goTo("results"));const research=el("button",{type:"button",class:"btn",text:"Open NASA lunar demo"});research.addEventListener("click",openLunarDemo);card.appendChild(el("div",{class:"row"},[retry,back,research]));}''')

h=h.replace('then(function (b) { clearTimeout(timer); return b; }', 'then(function (b) { clearTimeout(timer); return correctAssessmentTerminology(b); }')
h=h.replace('  function askQuestion(text) {', '''  function askQuestion(text) {
    if(!AI_ENABLED){const action=/missing|unknown|gap/i.test(text)?"missing":/calculation|calculated|power|current|I²t/i.test(text)?"calc":/source|evidence|citation/i.test(text)?"evidence":/verify|verification/i.test(text)?"verify":/index/i.test(text)?"index":/influence|matters most/i.test(text)?"influence":null;if(action)return investigate(action);pushLog({kind:"note",text:"AI remains inactive pending the API key. Use the calculation, missing-input, verification or source tools above; no generated answer has been requested."});return;}
''')
h=h.replace('Not available on this installation. The assessment stands without it.', 'AI remains inactive pending the API key. The assessment stands without it.')
h=h.replace('.then(function (res) { return res.json()', '.then(function (res) { if(res.status===429)throw new Error("The screening service is receiving too many requests. Your answers are kept. Wait a moment, then retry; the NASA lunar demo remains available."); return res.json()')
# Guard original UI callbacks and collect drafts before local persistence.
h=h.replace('function () { try { localStorage.setItem(KEY', 'function () { try { collectVisibleDrafts(); localStorage.setItem(KEY')
h=h.replace('S.mission = Object.assign(S.mission, s.mission || {});', 'if(!validStoredSession(s)){note("The saved session is invalid. Your current answers are unchanged.");return;}cancelScreenTasks();S.mission = Object.assign(S.mission, s.mission || {});')
h=h.replace('refreshFlow().then(function () { renderStage(); renderContext(); });', 'refreshFlow().then(function () { renderStage(); renderContext(); }).catch(function(e){if(S.stage === "info")screenError(e);});')
h=h.replace('collectStep(step); if (idx === 0) goTo("problem"); else { S.viewStep = steps[idx - 1].id; refreshFlow().then(function () { renderStage(); renderContext(); }).catch(function(e){if(S.stage === "info")screenError(e);}); }', 'navigateInfoBack(step,idx,steps);')
h=h.replace('URL.revokeObjectURL(url);', 'setTimeout(function(){URL.revokeObjectURL(url);},1500);')
h=h.replace('api("/api/status").then(r=>', 'if(AI_ENABLED)api("/api/status").then(r=>')
h=h.replace('[S.stage] || renderMission)(st);', '[S.stage] || renderMission)(st); enhanceInterface();')
h=h.replace('<main id="stage" tabindex="-1" aria-live="polite"></main>', '<main id="stage" tabindex="-1" aria-live="polite"><section class="card startup-content"><p class="eyebrow">AstroFlare · NASA combustion research</p><h1>Find the experiments. Understand the evidence.</h1><p>The lunar demo and source-backed explorer are loading.</p><a class="btn primary" href="#lunar-demo">Run the lunar habitat demo</a> <a href="/documentation">Read the methodology and sources</a><noscript><p>Interactive filtering requires JavaScript. NASA sources and downloads remain available through the documentation.</p></noscript></section></main>')
h=h.replace('u.value = S.answers.pressure_unit', 'u.disabled=!!(a&&a.unknown);u.value = S.answers.pressure_unit')
# Everything needed for the immediate demo and research is local, including bootstrap schema.
bootstrap=json.loads((p/'sources/schema.json').read_text());demo=json.loads((p/'demo.json').read_text())
dataset=json.loads((p/'public/dataset.json').read_text())
payload='const AI_ENABLED=false;\n'+(p/'public/terminology.js').read_text()+'\nconst PSI_DATA='+json.dumps(dataset)+';\n'+'const BOOTSTRAP=correctAssessmentTerminology('+json.dumps(bootstrap)+');\nconst DEMO=correctAssessmentTerminology('+json.dumps(demo)+');\n'+(p/'public/research.js').read_text()
h=h.replace('<script>','<script>\n'+payload,1)
h=h.replace('  // ---------------------------------------------------------------- start\n', (p/'public/enhancements.js').read_text()+'\n'+(p/'public/explorer.js').read_text()+'\n'+(p/'public/motion.js').read_text()+'\n'+(p/'public/plate.js').read_text()+'\n'+(p/'public/reliability.js').read_text()+'\n'+(p/'public/experience.js').read_text()+'\n  // ---------------------------------------------------------------- start\n')
(p/'public/index.html').write_text(h)
assets={'/release-checks.json':{'body':(p/'RELEASE_CHECKS.json').read_text(),'type':'application/json; charset=utf-8'},'/control-audit':{'body':(p/'CONTROL_AUDIT.md').read_text(),'type':'text/plain; charset=utf-8'},'/verification':{'body':(p/'VERIFICATION.md').read_text(),'type':'text/plain; charset=utf-8'},'/':{'body':h,'type':'text/html; charset=utf-8'},'/measurements.csv':{'body':(p/'public/measurements.csv').read_text(),'type':'text/csv; charset=utf-8'},'/documentation':{'body':(p/'README.md').read_text() if (p/'README.md').exists() else 'Documentation in preparation','type':'text/plain; charset=utf-8'}}
assets['/dataset.json']={'body':(p/'public/dataset.json').read_text(),'type':'application/json; charset=utf-8'}
for id in ['PSI-25','PSI-98','PSI-99']:
    assets['/sources/'+id+'-table.csv']={'body':base64.b64encode((p/'sources'/(id+'-table.csv')).read_bytes()).decode(),'base64':True,'type':'text/csv; charset=utf-8'}
for font in (p/'public').glob('*.ttf'):
    assets['/'+font.name]={'body':base64.b64encode(font.read_bytes()).decode(),'base64':True,'type':'font/ttf'}
bundle=io.BytesIO()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    files=['build.py','worker.js','server.mjs','package.json','package-lock.json','README.md','VERIFICATION.md','render.yaml','CONTROL_AUDIT.md','RELEASE_CHECKS.json','.github/workflows/ci.yml','demo.json','.gitignore']
    files += [str(f.relative_to(p)) for d in ['sources','test','public'] for f in (p/d).glob('*') if f.is_file() and f.name not in ['source.zip','index.html']]
    for f in sorted(files):
        info=zipfile.ZipInfo(f,date_time=(2026,11,14,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(p/f).read_bytes())
assets['/source.zip']={'body':base64.b64encode(bundle.getvalue()).decode(),'base64':True,'type':'application/zip'}
(p/'public/source.zip').write_bytes(bundle.getvalue())
(p/'dist/server/index.js').write_text('const ASSETS='+json.dumps(assets)+';\n'+(p/'worker.js').read_text())
print('Built faithful interface and Worker API relay')
