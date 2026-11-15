import pathlib,json,re,zipfile,io,base64,html as _html
p=pathlib.Path(__file__).parent
FOOTER='''<footer class="wrap small site-footer">
<p><strong>How this site runs.</strong> AstroFlare is one service on Render: this web interface, a Python assessment engine and an optional AI explanation service (FreeLLMAPI using Google Gemini models), all in the same container. Results come from fixed rules and cited NASA sources. AI text is optional, checked and labelled.</p>
<p><strong>Sources and credits.</strong> Experiment records: NASA Physical Sciences Informatics (BASS-II, PSI-25; Saffire I, PSI-98; Saffire II, PSI-99). Literature: NASA Technical Reports Server. Homepage photograph: NASA Glenn Research Center, image GRC-1998-C-00485, a candle flame in normal gravity (left) and in microgravity (right). Typefaces: Instrument Serif and Instrument Sans (SIL Open Font License). Research explorer by Vortex Aathish Studios; guided screening engine from the original AstroFlare project. AstroFlare is an independent project built on public NASA data.</p>
<p><strong>Learn more from NASA.</strong> <a href="https://psi.nasa.gov/physci/repo/search?q=combustion" target="_blank" rel="noopener noreferrer">PSI combustion data repository</a> &middot; <a href="https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/" target="_blank" rel="noopener noreferrer">NASA combustion science</a> &middot; <a href="https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/" target="_blank" rel="noopener noreferrer">A Researcher&rsquo;s Guide to ISS Combustion Science</a> &middot; <a href="https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/" target="_blank" rel="noopener noreferrer">Fire aboard Mir</a></p>
<p><a href="/documentation">Documentation, sources and limitations</a> &middot; <a href="/source.zip" download="astroflare-source.zip">Download the source code</a></p>
</footer>'''
(p/"dist/server").mkdir(parents=True,exist_ok=True)
h=(p/'sources/original-interface.html').read_text()
h=re.sub(r'let[-\s\u2011\u2013]through energy(?: of the fault)?(?: \((?:I²t|I2t)\))?', 'fault current integral (I²t)', h, flags=re.I)
h=h.replace('<title>Astroflare | Guided hazard assessment</title>','<title>Astroflare | Assessment & NASA combustion research</title>')
h=h.replace('<div class="row noprint">','<div class="row noprint">\n    <button class="btn small-btn" id="demoBtn" type="button">Open hypothetical demo</button>\n    <button class="btn small-btn" id="researchBtn" type="button">NASA research</button>\n    <button class="btn small-btn" id="labsBtn" type="button">For research labs</button>',1)
assert h.count('</header>')==1
h=h.replace('</header>','</header>\n<p class="tool-key" id="tool-key"><strong>Research explorer</strong> (Lunar habitat demo, NASA research) searches NASA records in your browser. <strong>Mission screening</strong> sends your answers to the assessment engine on this site&rsquo;s server.</p>',1)
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
    $("researchBtn").addEventListener("click", function () { openResearch(); });
    $("saveBtn").addEventListener''',1)
h=h.replace('S.stage = "mission"; S.reached = { mission: true };','S.demo=false; S.stage = "mission"; S.reached = { mission: true };')
h=h.replace('S.assessment = null; S.interp = null;','S.demo=false; S.assessment = null; S.interp = null;')
h=h.replace('    bindControls();\n    Promise.all([api("/api/schema"), api("/api/status").catch(function () { return null; })]).then(function (r) {\n      S.schema = r[0].schema; S.guide = r[0].guide; S.examples = r[0].examples; S.methodology = r[0].methodology; S.aiAvailable = !!(r[1] && r[1].analysis && r[1].analysis.explanation.available);\n      renderMethod(); goTo("mission");\n    }).catch(function (e) { $("stage").appendChild(el("div", { class: "card" }, [el("h2", { text: "Astroflare could not start" }), el("p", { text: e.message })])); });\n    loadFlares();', '''    S.schema=BOOTSTRAP.schema; S.guide=BOOTSTRAP.guide; S.examples=BOOTSTRAP.examples; S.methodology=BOOTSTRAP.methodology;
    bindControls(); renderMethod(); goTo("mission");
    api("/api/status").then(r=>{S.aiAvailable=AI_ENABLED && !!(r.analysis && r.analysis.explanation && r.analysis.explanation.available);}).catch(()=>{S.aiAvailable=false;});''')
h=h.replace('  function start() {','  let started=false;\n  function start() {\n    if(started)return; started=true;')
h=h.replace('S.reportMd = r.markdown; S.reportJson = r.report;', 'S.reportMd = r.markdown.replace(/Most consequential unresolved issue/gi, "One condition to review (not ranked)"); S.reportJson = JSON.parse(JSON.stringify(r.report).replace(/Most consequential unresolved issue/gi, "One condition to review (not ranked)"));')
h=h.replace('  function renderMission(st) {','''  function renderMission(st) {
    const intro=el("div",{class:"card demo-intro"},[el("h2",{text:"New here? See a finished example first"}),el("p",{class:"lede",text:"Open a ready-made example to see what a finished screening looks like, or describe your own mission below and AstroFlare will guide you through six short steps."})]);
    const demo=el("button",{type:"button",class:"btn primary",text:"Open hypothetical demo results"});demo.addEventListener("click",openDemo);
    const research=el("button",{type:"button",class:"btn",text:"Explore NASA combustion research"});research.addEventListener("click",()=>openResearch());
    intro.appendChild(el("div",{class:"row"},[demo,research]));intro.appendChild(el("ol",{class:"how-steps"},[el("li",{text:"Describe your mission in your own words, or skip and answer questions."}),el("li",{text:"Pick the fire hazard you want to look at."}),el("li",{text:"Answer short question groups. “I don’t know” is always allowed."}),el("li",{text:"Get the conditions worth reviewing, what is missing, and the NASA sources."})]));intro.appendChild(el("p",{class:"small mt",text:"The example uses illustrative inputs. Your answers are sent to the AstroFlare assessment engine on this site’s server, which applies fixed rules and cited sources."}));st.appendChild(intro);''')
# The solar-activity appendix is unrelated to cabin fire research, so it is not part of the page at all.
start=h.index('  <details class="sec noprint" id="envSec">');end=h.index('  <details class="sec method',start)
h=h[:start]+h[end:]
h=h.replace('    $("flareRetry").addEventListener("click", loadFlares);\n','',1)  # its button left with the appendix
fs=h.index('  // ---------------------------------------------------------------- NASA solar activity');fe=h.index('  function renderMethod()',fs);h=h[:fs]+h[fe:]  # the unused solar loader goes too
h=h.replace('</div>\n<script>', '</div>\n'+FOOTER+'\n<script>',1)
css='''
.demo-intro {background:var(--accent-soft);border-color:#bfd0e2}
.research-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.research-grid h3{margin:8px 0}.research-grid p{margin-top:10px}.match-note{font-size:13px;color:var(--accent)}.compare-label{display:block;border-top:1px solid var(--line);margin-top:16px;padding-top:12px;cursor:pointer}.measurement-row{display:grid;grid-template-columns:200px 1fr 35px;align-items:center;gap:12px;margin:18px 0}.bar-track{background:#eef1f5;height:24px}.measurement-bar{background:#2b5d8a;height:100%}.axis{margin-left:212px;white-space:pre;font:11px var(--mono);color:var(--muted);overflow:hidden}.measurement-chart{padding:8px 0}.research-grid .card{margin-bottom:0}th[scope=row]{min-width:120px}.tablewrap td{min-width:180px}.btn{min-height:40px}footer details{margin-top:16px}
@media(max-width:900px){.research-grid{grid-template-columns:1fr}.measurement-row{grid-template-columns:145px 1fr 30px;gap:8px}.axis{margin-left:153px}.brand-sub{max-width:230px}.top .row{width:100%}}@media(max-width:400px){.measurement-row{grid-template-columns:110px 1fr 28px;font-size:12px}.axis{margin-left:118px}.top .btn{flex:1 1 auto}}'''
h=h.replace('</style>',css+'\n</style>',1)
# Research-first upgrade; preserve the same project, legacy assessment and relay.
h=h.replace('<title>Astroflare | Assessment & NASA combustion research</title>','<title>AstroFlare | Flame in Freefall evidence explorer</title>')
h=h.replace('Guided hazard screening for mission leads','Flame in Freefall · NASA PSI evidence')
h=h.replace('<button class="btn small-btn" id="demoBtn" type="button">Open hypothetical demo</button>', '<button class="btn small-btn" id="homeBtn" type="button">Home</button><button class="btn small-btn" id="demoBtn" type="button">Lunar habitat demo</button><button class="btn small-btn" id="missionBtn" type="button">Mission screening</button>')
h=h.replace('$("demoBtn").addEventListener("click", openDemo);','$("demoBtn").addEventListener("click", openLunarDemo);$("homeBtn").addEventListener("click",()=>goTo("home"));$("labsBtn").addEventListener("click",()=>openLabs());$("missionBtn").addEventListener("click",()=>goTo("mission"));')
h=h.replace('research: renderResearch }','research: renderResearch, home: renderHome, labs: renderLabs }')
h=h.replace('S.stage = stage; S.reached[stage] = true;', 'S.stage = stage; document.body.classList.toggle("research-active", stage === "research" || stage === "home"); S.reached[stage] = true;')
h=h.replace('st.querySelector("h2")','st.querySelector("h1,h2")')
h=h.replace('bindControls(); renderMethod(); goTo("mission");','bindControls(); renderMethod(); goTo(location.hash === "#lunar-demo" ? "research" : "home");')
h=h.replace('class: "tablewrap"', 'class: "tablewrap", tabindex: "0", role: "region", "aria-label": "Scrollable comparison or data table"')
h=h.replace('</style>',(p/'public/font-faces.css').read_text()+'\n'+(p/'public/explorer.css').read_text()+'\n'+(p/'public/theme.css').read_text()+'\n</style>',1)
h=h.replace('<div class="brand-name">ASTROFLARE</div>','<div class="brand-name">AstroFlare</div>')

# Judge reliability: stage history, persistent report errors and explicit recovery.
h=h.replace('    renderStepper(); renderContext(); renderStage();', '    renderStepper(); renderContext(); renderStage(); syncNavigation(stage);',1)
h=h.replace('goTo(location.hash === "#lunar-demo" ? "research" : "home");','restoreNavigation();')
h=h.replace('S.stage = "report"; S.reportMd = null;', 'S.stage = "report"; S.reportMd = null; S.reportErr = null;')
h=h.replace('S.reportErr = null; } else busy(p, "Assembling the report"); card.appendChild(p);', '''} else busy(p, "Assembling the report"); card.appendChild(p);
      if(S.reportErr){const retry=el("button",{type:"button",class:"btn primary",text:"Retry report"});retry.addEventListener("click",prepareReport);const back=el("button",{type:"button",class:"btn",text:"Back to results"});back.addEventListener("click",()=>goTo("results"));const research=el("button",{type:"button",class:"btn",text:"Open NASA lunar demo"});research.addEventListener("click",openLunarDemo);card.appendChild(el("div",{class:"row"},[retry,back,research]));}''')

h=h.replace('then(function (b) { clearTimeout(timer); return b; }', 'then(function (b) { clearTimeout(timer); return correctAssessmentTerminology(b); }')
h=h.replace('  function askQuestion(text) {', '''  function askQuestion(text) {
    if(!AI_ENABLED||!S.aiAvailable){const action=/missing|unknown|gap/i.test(text)?"missing":/calculation|calculated|power|current|I²t/i.test(text)?"calc":/source|evidence|citation/i.test(text)?"evidence":/verify|verification/i.test(text)?"verify":/index/i.test(text)?"index":/influence|matters most/i.test(text)?"influence":null;if(action)return investigate(action);pushLog({kind:"note",text:"The optional AI service is not available right now. Use the calculation, missing-input, verification or source tools above; no generated answer has been requested."});return;}
''')
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
payload='const AI_ENABLED=true;\n'+(p/'public/terminology.js').read_text()+'\nconst PSI_DATA='+json.dumps(dataset)+';\n'+'const BOOTSTRAP=correctAssessmentTerminology('+json.dumps(bootstrap)+');\nconst DEMO=correctAssessmentTerminology('+json.dumps(demo)+');\n'+(p/'public/research.js').read_text()
h=h.replace('<script>','<script>\n'+payload,1)
h=h.replace('  // ---------------------------------------------------------------- start\n', (p/'public/enhancements.js').read_text()+'\n'+(p/'public/explorer.js').read_text()+'\n'+(p/'public/guided.js').read_text()+'\n'+(p/'public/labs.js').read_text()+'\n'+(p/'public/projects.js').read_text()+'\n'+(p/'public/motion.js').read_text()+'\n'+(p/'public/plate.js').read_text()+'\n'+(p/'public/reliability.js').read_text()+'\n'+(p/'public/experience.js').read_text()+'\n  // ---------------------------------------------------------------- start\n')
(p/'public/index.html').write_text(h)
def md_inline(s):
    s=_html.escape(s,quote=False)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])',r'<em>\1</em>',s)
    s=re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',lambda m:'<a href="%s">%s</a>'%(m.group(2).replace('"','%22'),m.group(1)),s)
    s=re.sub(r'(?<!["=>])(https?://[^\s<]+[^\s<.,;:)])',r'<a href="\1">\1</a>',s)
    return s
def md_to_html(text):
    out,lines,i=[],text.replace('\r\n','\n').split('\n'),0;toc=[]
    while i<len(lines):
        l=lines[i]
        if l.startswith('```'):
            j=i+1;buf=[]
            while j<len(lines) and not lines[j].startswith('```'):buf.append(lines[j]);j+=1
            out.append('<pre><code>'+_html.escape('\n'.join(buf),quote=False)+'</code></pre>');i=j+1;continue
        m=re.match(r'(#{1,4})\s+(.*)',l)
        if m:
            n=len(m.group(1));slug=re.sub(r'[^a-z0-9]+','-',m.group(2).lower()).strip('-')[:60]
            if n==2:toc.append((slug,m.group(2)))
            out.append('<h%d id="%s">%s</h%d>'%(n,slug,md_inline(m.group(2)),n));i+=1;continue
        if l.startswith('|') and i+1<len(lines) and re.match(r'^\|[\s:|-]+\|$',lines[i+1].strip()):
            cells=lambda r:[c.strip() for c in r.strip().strip('|').split('|')]
            head=cells(l);rows=[];j=i+2
            while j<len(lines) and lines[j].startswith('|'):rows.append(cells(lines[j]));j+=1
            out.append('<div class="tablewrap" tabindex="0" role="region" aria-label="Table"><table><thead><tr>'+''.join('<th>%s</th>'%md_inline(c) for c in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>%s</td>'%md_inline(c) for c in r)+'</tr>' for r in rows)+'</tbody></table></div>');i=j;continue
        if re.match(r'^\s*([-*]|\d+\.)\s+',l):
            ordered=bool(re.match(r'^\s*\d+\.',l));items=[];j=i
            while j<len(lines) and re.match(r'^\s*([-*]|\d+\.)\s+',lines[j]):items.append(re.sub(r'^\s*([-*]|\d+\.)\s+','',lines[j]));j+=1
            tag='ol' if ordered else 'ul';out.append('<%s>%s</%s>'%(tag,''.join('<li>%s</li>'%md_inline(x) for x in items),tag));i=j;continue
        if not l.strip():i+=1;continue
        buf=[l];j=i+1
        while j<len(lines) and lines[j].strip() and not re.match(r'^(#|\||```|\s*([-*]|\d+\.)\s)',lines[j]):buf.append(lines[j]);j+=1
        out.append('<p>%s</p>'%md_inline(' '.join(x.strip() for x in buf)));i=j
    return '\n'.join(out),toc
DOC_CSP="default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"
def doc_page(title,markdown,intro):
    body,toc=md_to_html(markdown)
    nav='<nav class="doc-toc" aria-label="On this page"><p class="lbl">On this page</p><ol>'+''.join('<li><a href="#%s">%s</a></li>'%(s,md_inline(t)) for s,t in toc[:24])+'</ol></nav>' if toc else ''
    css=(p/'public/font-faces.css').read_text()+'\n'+(p/'public/theme.css').read_text()+'\n'+(p/'public/docs.css').read_text()
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s · AstroFlare</title><style>%s</style></head><body class="doc-page">'
            '<a class="skip" href="#doc-main">Skip to content</a><header class="top"><div class="brand"><a class="brand-name" href="/">AstroFlare</a></div>'
            '<nav class="doc-nav" aria-label="Main"><a href="/">Home</a><a href="/#lunar-demo">Lunar habitat demo</a><a href="/#mission">Mission screening</a><a href="/#research">NASA research</a><a href="/#labs">For research labs</a><a href="/documentation" %s>Documentation</a></nav></header>'
            '<main id="doc-main" class="wrap doc-wrap"><p class="doc-kicker">%s</p>%s<div class="doc-body">%s</div></main>%s</body></html>')%(_html.escape(title),css,'aria-current="page"' if title=='Documentation' else '',_html.escape(intro),nav,body,FOOTER)
assets={'/release-checks.json':{'body':(p/'RELEASE_CHECKS.json').read_text(),'type':'application/json; charset=utf-8'},'/control-audit':{'body':doc_page('Control audit',(p/'CONTROL_AUDIT.md').read_text(),'Earlier release record: every control and its verification'),'type':'text/html; charset=utf-8','csp':DOC_CSP},'/verification':{'body':doc_page('Verification',(p/'VERIFICATION.md').read_text(),'Earlier release record: verification results and limits'),'type':'text/html; charset=utf-8','csp':DOC_CSP},'/':{'body':h,'type':'text/html; charset=utf-8'},'/measurements.csv':{'body':(p/'public/measurements.csv').read_text(),'type':'text/csv; charset=utf-8'},'/documentation':{'body':doc_page('Documentation',(p/'README.md').read_text(),'How AstroFlare works, its sources, limits and deployment'),'type':'text/html; charset=utf-8','csp':DOC_CSP}}
scripts=re.findall(r'<script>(.*?)</script>',h,re.S)
assert len(scripts)==1,'the page must have exactly one inline script for its CSP'
import hashlib
script_hash=base64.b64encode(hashlib.sha256(scripts[0].encode('utf-8')).digest()).decode()
assets['/']['csp']="default-src 'self'; script-src 'self' 'sha256-"+script_hash+"'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"
assets['/dataset.json']={'body':(p/'public/dataset.json').read_text(),'type':'application/json; charset=utf-8'}
for id in ['PSI-25','PSI-98','PSI-99']:
    assets['/sources/'+id+'-table.csv']={'body':base64.b64encode((p/'sources'/(id+'-table.csv')).read_bytes()).decode(),'base64':True,'type':'text/csv; charset=utf-8'}
for img in (p/'public').glob('*.jpg'):
    assets['/'+img.name]={'body':base64.b64encode(img.read_bytes()).decode(),'base64':True,'type':'image/jpeg'}
for font in (p/'public').glob('*.ttf'):
    assets['/'+font.name]={'body':base64.b64encode(font.read_bytes()).decode(),'base64':True,'type':'font/ttf'}
bundle=io.BytesIO()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    files=['build.py','worker.js','server.mjs','package.json','package-lock.json','README.md','VERIFICATION.md','render.yaml','CONTROL_AUDIT.md','RELEASE_CHECKS.json','.github/workflows/ci.yml','demo.json','.gitignore']
    files += ['Dockerfile','.dockerignore']
    files += [str(f.relative_to(p)) for d in ['sources','test','public'] for f in (p/d).glob('*') if f.is_file() and f.name not in ['source.zip','index.html']]
    files += [str(f.relative_to(p)).replace('\\','/') for f in (p/'engine').rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
    for f in sorted(files):
        info=zipfile.ZipInfo(f,date_time=(2026,11,14,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(p/f).read_bytes())
assets['/source.zip']={'body':base64.b64encode(bundle.getvalue()).decode(),'base64':True,'type':'application/zip'}
(p/'public/source.zip').write_bytes(bundle.getvalue())
(p/'dist/server/index.js').write_text('const ASSETS='+json.dumps(assets)+';\n'+(p/'worker.js').read_text())
print('Built faithful interface and Worker API relay')
