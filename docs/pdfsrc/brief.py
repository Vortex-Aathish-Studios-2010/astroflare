import json
from common import *
import assessment as A

S = json.load(open(ROOT / 'engine/evidence/sources.json', encoding='utf-8'))
D = json.load(open(ROOT / 'public/dataset.json', encoding='utf-8'))
srcs = S['sources']
claims = sum(len(x.get('claims', [])) for x in srcs)

flow = '<svg viewBox="0 0 720 118" width="100%">'
steps = [('1', 'Mission', 'describe it'), ('2', 'Problem', 'pick a hazard'), ('3', 'Information', 'answer, with basis'), ('4', 'Review', 'check and confirm'), ('5', 'Results', 'findings, sources'), ('6', 'Investigate', 'ask, compare'), ('7', 'Report', 'download')]
for i, (n, t, s) in enumerate(steps):
    x = 4 + i * 102
    flow += '<rect x="%d" y="30" width="94" height="58" fill="none" stroke="#111" stroke-width="1"/>' % x
    flow += '<rect x="%d" y="22" width="26" height="8" fill="%s"/>' % (x, '#b9ddf3' if i % 2 == 0 else '#b9e6c5')
    flow += svg_text(x + 8, 52, t, 13, 700) + svg_text(x + 8, 68, s, 9.5, 400, '#555') + svg_text(x + 8, 82, n, 9, 600, '#767676')
    if i < 6:
        flow += '<path d="M%d 59 h8" stroke="#111" stroke-width="1"/>' % (x + 94)
flow += '</svg>'

body = cover('Project brief  ·  NASA Space Apps 2026  ·  Flame in Freefall', 'AstroFlare',
             'A plain-language screening and evidence tool for fire safety on crewed spacecraft.',
             [('Live site', 'astroflare.onrender.com'), ('Version', 'Engine 2026.10.21-2<br>Document of %s' % DATE), ('Status', 'Live and tested.<br>Pull request open.')])

body += '''<section>
<h1>At a glance</h1>
<p class="lede">AstroFlare helps a mission lead find out which fire-safety conditions on a crewed spacecraft deserve a specialist's attention, and which real NASA experiments say something about them. It does this with fixed, readable rules and cited sources, not with guesses.</p>
<div class="cols3">%s%s%s</div><div class="cols3">%s%s%s</div>
<h2>In one paragraph</h2>
<p>Fire behaves differently in space. Flames in microgravity are rounder, burn at different rates and can be harder to detect, and everything that shapes a fire (oxygen, pressure, ventilation, the materials in the room) is set by the spacecraft rather than by a planet. Turning a mission idea into the right review questions normally needs a safety specialist. AstroFlare does the first pass. A user describes a mission in ordinary words, answers a short guided set of questions, and receives a list of conditions to review, the information still missing, and the NASA sources behind each point. Alongside this, a research explorer matches a user's question to three public NASA combustion experiments and shows what they measured, under which conditions, and what they do not say.</p>
<p>It never says a design is safe, never gives a probability, and never hides what it does not know. An optional AI writes short plain-language explanations, but every sentence it produces is checked by code before anyone sees it, and the page always shows the deterministic, cited answer first.</p>
<h2>What is in this document</h2>%s
</section>''' % (
    stat('3', 'NASA PSI experiments curated'), stat(str(len(srcs)), 'NASA documents in the evidence library', True), stat(str(claims), 'recorded, citable statements'),
    stat(str(len(A.FIELDS)), 'guided inputs across six groups', True), stat('4', 'hazards screened'), stat('2', 'tools, one site'),
    toc(['The problem', 'Aim and principles', 'Our solution', 'The research explorer', 'Mission screening', 'The evidence', 'Where AI is used', 'What AstroFlare is not', 'Who it is for', 'How it is delivered', 'Status and history', 'Limits and next steps']))

body += '''<section class="page"><h1>1. The problem</h1>
<p class="lede">Fire is one of the most serious hazards on a spacecraft, and one of the least intuitive.</p>
<p>A fire aboard a crewed vehicle cannot be fled and cannot be left to burn out. The crew shares a small, sealed volume with a fixed air supply, and help is hours to days away. Safety work therefore starts long before launch, with a question every mission team eventually has to answer: <i>which conditions in our design should a fire-safety specialist look at first, and what do we still not know?</i></p>
<h3>Why that question is hard</h3>
<ul>
<li><b>Space changes how fire behaves.</b> Without gravity, hot gas does not rise. Flames can be spherical or weak, can spread slowly or unexpectedly, and smoke may not travel to the detector the way it does on Earth. Earth intuition is a poor guide.</li>
<li><b>The environment is a design choice.</b> Oxygen fraction, cabin pressure, ventilation flow, and the ability to shut that flow off all change fire risk, and they differ between a transit vehicle, a lunar habitat and a space station.</li>
<li><b>The evidence is scattered and thin.</b> Relevant knowledge sits in dozens of NASA reports and a handful of in-orbit experiments, written for specialists, in different units and with different gaps. Full-scale fires in orbit are almost never run.</li>
<li><b>Early-stage teams lack a specialist.</b> Students, researchers and new mission leads need to prepare a credible safety discussion, but turning a concept into the right questions usually needs expertise they do not have yet.</li>
<li><b>Overconfident tools are dangerous.</b> A tool that outputs a single "risk score" invites people to trust a number that no experiment has validated.</li>
</ul>
%s
</section>''' % note('<b>The challenge this project answers.</b> NASA Space Apps 2026, "Flame in Freefall": make combustion research from the International Space Station useful and understandable. AstroFlare turns public NASA experiment records and technical literature into something a non-specialist can query, compare and cite.', True)

body += '''<section class="page"><h1>2. Aim and principles</h1>
<p class="lede">To help people ask better fire-safety questions sooner, and to show exactly where the answers come from.</p>
<h3>The aim, stated plainly</h3>
<p>Given a hypothetical crewed mission, AstroFlare should (1) list the conditions a qualified safety team should review first, (2) say what information is missing, (3) connect every point to a cited NASA source, and (4) point the user to the real experiments that are most relevant, with their conditions and limits intact.</p>
<h3>The principles that shape every decision</h3>%s
<p>Each principle is enforced by code and tests, not left as a promise. For example, the engine refuses to compute its single index unless every needed input was supplied, the AI checker rejects any number that is not already in the results, and the evidence answers show the original NASA table and row for every figure.</p>
</section>''' % table(['Principle', 'What it means in practice'], [
    ('Screening, not judgement', 'Output is a list of questions for specialists. There is no go/no-go, no certification, no claim a design is safe.'),
    ('No invented numbers', 'No probability, severity, margin or confidence is ever estimated. A single heuristic index exists but is labelled uncalibrated and unvalidated.'),
    ('Unknown stays unknown', 'A blank answer becomes "unknown" and is reported as a gap. Nothing is silently defaulted.'),
    ('Say how you know', 'Each answer can carry its basis: specification, test, analysis, estimate or assumption. Weak bases are flagged in the limitations.'),
    ('Show the source', 'Every sourced finding cites recorded statements from NASA documents; every figure in the explorer links to the original NASA table and row.'),
    ('Deterministic first, AI second', 'Everything that produces a result is ordinary code. The optional AI only explains, and its text is checked and labelled.'),
    ('Plain language', 'Written for a mission lead, not a combustion scientist. Terms are explained where they appear.'),
    ('Honest about limits', 'The limits are shown on the page, in every report, and in the AI rules, not hidden in a footnote.')])

body += '''<section class="page"><h1>3. Our solution</h1>
<p class="lede">One site with two tools that share the same evidence: a NASA evidence explorer, and a guided mission-screening workflow.</p>
<div class="cols"><div>
<h3>Tool 1: the research explorer</h3>
<p>Answers: <i>which NASA experiments can inform my question, and what exactly did they measure?</i></p>
<ul><li>One-click lunar-habitat demo, or a user's own question</li><li>Ranks three NASA PSI experiments with a transparent points rule</li><li>Filters by material, gravity and airflow evidence</li><li>Side-by-side comparison of two experiments</li><li>A cited "what should we test next?" proposal</li><li>Ask a question and get the exact measurement, with the NASA table row</li></ul></div>
<div><h3>Tool 2: mission screening</h3>
<p>Answers: <i>for my mission, which conditions deserve review, and what is missing?</i></p>
<ul><li>Describe the mission in plain words; AstroFlare shows what it understood, with your own words quoted</li><li>Seven guided stages with a short question set that adapts to your answers</li><li>Calculations with formulas and limits</li><li>Findings grouped into five layers of defence</li><li>Investigate, compare and ask follow-up questions</li><li>Download a full report</li></ul></div></div>
<h3>How the parts fit together</h3>
<p>The visitor uses a web page. Behind it sit a Python assessment engine (all rules, calculations and validation), a library of 14 NASA documents, three curated experiment data sets, and an optional AI service reached only through the engine. Everything runs as one free Render service at <b>astroflare.onrender.com</b>.</p>
%s</section>''' % note('<b>Why two tools?</b> The explorer is the fastest way to see what real experiments say. The screening workflow is the way to turn a specific mission into review questions. Both refuse to produce a verdict, and both let the user open the source behind any statement.')

body += '''<section class="page"><h1>4. The research explorer</h1>
<p class="lede">Start with a research question; end with the NASA records, conditions and gaps that bear on it.</p>
<h3>A one-click journey</h3>
<ol><li><b>Run the lunar habitat demo.</b> The question is pre-filled: <i>"Which NASA experiments can inform a review of solid-material flammability in a ventilated lunar habitat?"</i> The three experiments appear ranked.</li>
<li><b>Read why each ranked where it did.</b> The page lists every point: for example, solid materials +2, flame spread +2, ventilation +2, variable-flow coverage +1.</li>
<li><b>Filter.</b> Choose a material, an experiment gravity, or an airflow evidence level. Choosing "documented 20 cm/s" removes BASS-II, because its table has no calibrated airflow value, and says so.</li>
<li><b>Compare.</b> Select two experiments to see conditions, measurements and AstroFlare's interpretation in separate rows.</li>
<li><b>Read the proposed follow-up.</b> A panel states what NASA measured, what is missing for the scenario, and one proposed next research step, clearly marked as AstroFlare's proposal and not a NASA recommendation.</li>
<li><b>Ask a question.</b> For example "What was the flame spread rate in Saffire II?" returns <i>2.1 mm/s for run 2-5</i>, with its conditions and the original NASA table row. Asking about lunar gravity returns an honest gap: the experiments were in microgravity.</li>
<li><b>Optionally explain with AI.</b> A button under the answer asks for a short plain-language explanation, checked and labelled.</li></ol>
<h3>The ranking rule</h3>
<p>Relevance is a simple, published points rule, not a model: +2 per recognised question topic (solid materials, flame spread, ventilation, oxygen, microgravity, combustion gases), +1 for variable-flow coverage when airflow is asked about, +2 for a named supported material, +1 for an exact gravity match. Ties keep a fixed order. The default lunar question scores 7, 6 and 6. <b>The score is research relevance, not fire risk.</b></p>
<h3>Answers that refuse to overreach</h3>
<ul><li>A question naming one investigation is matched to that investigation only; "Saffire II" maps to PSI-99 and nothing else.</li>
<li>Requests for safe limits, predictions or certification return a gap message, not a number.</li>
<li>Missing measurements show "Not reported". Source inconsistencies are kept and disclosed, never silently corrected.</li></ul>
</section>'''

body += '''<section class="page"><h1>5. Mission screening</h1>
<p class="lede">Seven stages, one question group at a time, with your own words and your own confidence kept visible.</p>
%s
<table><thead><tr><th>Stage</th><th>What happens</th></tr></thead><tbody>
<tr><td><b>1 Mission</b></td><td>Describe the mission in free text. AstroFlare shows what it understood and the exact words each item came from. Nothing is used until ticked; guesses from context are tagged "inferred" and start unticked.</td></tr>
<tr><td><b>2 Problem</b></td><td>Choose one of four hazards (electrical overheating or arc; battery thermal event; cabin material ignition; persistent smoke) and a goal. Concerns it cannot model, such as radiation or decompression, are named instead of forced into a hazard.</td></tr>
<tr><td><b>3 Information</b></td><td>Small groups of questions, each with why it matters, units, an "I don't know" option and how the user knows the answer. Branching follows the hazard and earlier answers; an unknown fault current skips the clearing-time question and says why.</td></tr>
<tr><td><b>4 Review</b></td><td>A profile of what was entered, estimates, assumptions, unknowns and values AstroFlare derived. Any row can be edited without losing the rest; estimates and unknowns need an explicit acknowledgement.</td></tr>
<tr><td><b>5 Results</b></td><td>Overview, findings with reasoning and limits, calculations, uncertainty, next steps, five protective layers and the sources.</td></tr>
<tr><td><b>6 Investigate</b></td><td>Which answer matters most; show a calculation; open a cited source; what is missing; what to verify; try a different answer; compare with a pinned baseline; type a question.</td></tr>
<tr><td><b>7 Report</b></td><td>Download as Markdown or JSON, or print: inputs with basis, calculations, findings, evidence, missing information, limits, next steps and an AI-assistance disclosure.</td></tr></tbody></table>
<h3>What the user gets back</h3>
<p>Four kinds of finding, each labelled: a <b>plausible pathway</b> (never called a demonstrated failure), a <b>condition warranting review</b>, an <b>information gap</b>, or <b>context</b>. They are grouped under five layers of defence (prevent, detect, isolate and control, suppress and protect, respond and recover), so the user can see where coverage is thin. Six calculations are shown with formula and limits: nominal power, let-through energy (I squared t), oxygen partial pressure, air-turnover time, minimum round-trip communication delay and pressure-unit conversion.</p>
<p>The optional single number, the "preliminary screening index (heuristic)", is shown only when every input it needs was supplied. It is explicitly not a probability or a severity, and is meaningful only for comparing inputs for the same hazard.</p>
</section>''' % ('<figure>%s<figcaption>The seven stages. Going back or editing never restarts the assessment; answers stay in the page.</figcaption></figure>' % flow)

# evidence section
rows = [(x['id'], x['title'][:92] + ('…' if len(x['title']) > 92 else ''), x['date'][:4], x['issuer'][:44]) for x in srcs]
prows = []
for r in D['records']:
    prows.append((r['id'], r['name'], r['title'], '%s · v%s' % (r['gravityLabel'], r['version']), ', '.join(run['id'] for run in r['runs'])))
body += '''<section class="page"><h1>6. The evidence</h1>
<p class="lede">Two layers: a literature library for the screening findings, and original experiment tables for the explorer.</p>
<h3>Layer 1: the NASA literature library (%d documents, %d statements)</h3>
<p>Each finding in mission screening cites recorded statements from these documents. Only one (NASA-STD-3001 Technical Brief OCHMO-TB-008 Rev A) was read in full; the other 13 were read at abstract level only, and every citation says so. On 21 October 2026 each statement was re-read against its live NASA Technical Reports Server abstract with no mismatch, and all 14 records were confirmed live with matching titles. There is no literature search: a statement that cannot be found is reported as a limitation, never invented around.</p>
%s
<h3>Layer 2: three curated PSI experiments</h3>
<p>The explorer uses original experimental tables from NASA's Physical Sciences Informatics repository, retrieved on 14 November 2026. Each original CSV is stored byte for byte and pinned with a SHA-256 hash that a test re-checks.</p>
%s
%s
</section>''' % (len(srcs), claims, table(['Id', 'Title', 'Year', 'Issuer'], rows),
                  table(['PSI id', 'Experiment', 'Full name', 'Setting · table version', 'Curated rows'], prows),
                  note('<b>Source defects are kept, not corrected.</b> For example the Saffire II table labels a column as a length but the values carry mm/s units, and one Saffire I thickness disagrees between the table and NASA\'s report. AstroFlare discloses these and never overwrites raw source values.'))

body += '''<section class="page"><h1>7. Where AI is used</h1>
<p class="lede">AI writes words. Code decides what is true enough to show.</p>
<p>Everything that produces a result (validation, branching, calculations, rules, the index, sensitivity, comparisons, citations, report assembly) is ordinary deterministic code. The AI has four narrow, optional jobs, and every reply passes through a checker before a person sees it.</p>
%s
<h3>The checks, in plain terms</h3>
<ul><li><b>No new numbers.</b> Any number in an AI answer must already appear in the results or the NASA records.</li>
<li><b>No overclaiming.</b> Words that assert safety, validation, certification, probability or confidence are rejected unless clearly negated ("has not been validated").</li>
<li><b>No links or invented sources,</b> no filler, and no talk about how the text was produced.</li>
<li><b>Real references only.</b> An answer that claims to answer must cite at least one real finding, calculation, source or record.</li>
<li><b>Labelled.</b> Accepted text is always shown as automatically generated and not reviewed by a person.</li></ul>
%s
<h3>Which AI?</h3>
<p>The live site uses <b>FreeLLMAPI</b>, an open-source router that pools free-tier models, running privately beside the engine. It is asked for Google Gemini models in order (gemini-3.6-flash, then gemini-3.5-flash-lite, then gemini-3.5-flash) and falls back to the next when one fails or is rate-limited. The engine also supports Anthropic Claude as an alternative provider; that path is built and tested but has not been run against the live Anthropic API. Provider keys are held only in the hosting service's secret settings and never reach the browser.</p>
</section>''' % (
    table(['Job', 'What the AI may do', 'Where it appears'], [
        ('Read the mission', 'Propose values for nine fields and up to three clarifying questions, each quoting the user\'s words', 'Mission stage'),
        ('Explain the results', 'A short mission-specific summary, a note per finding and an uncertainty note', 'Results stage and report'),
        ('Answer a typed question', 'An answer limited to this assessment, citing ids, when the built-in tools do not cover it', 'Investigate stage'),
        ('Explain NASA evidence', 'A short explanation limited to the curated NASA PSI records, citing records or runs', 'Explorer, under an answer')]),
    note('<b>Checks test consistency, not truth.</b> Accepted text can still be subtly wrong, which is why it is labelled, and why the deterministic answer always appears first and never depends on the AI. If the AI is busy, down or rejected, one plain sentence says so and nothing else changes.', True))

body += '''<section class="page"><h1>8. What AstroFlare is not</h1>
<p class="lede">The limits are part of the product, stated on the page and enforced in code.</p>
%s
<h1 style="margin-top:12mm">9. Who it is for</h1>
%s
</section>''' % (
    table(['AstroFlare does not', 'Because'], [
        ('Connect to any spacecraft, sensor or alarm', 'It screens hypothetical scenarios and cannot detect or report a real fire.'),
        ('Estimate probability, severity, margin or confidence', 'No validated model exists behind it; any such number would be invented.'),
        ('Give a go/no-go, a clearance or a certification', 'Those belong to qualified safety authorities.'),
        ('Claim validation', 'No experiment, simulation or independent expert has checked its rules.'),
        ('Treat a proposed fix as working', 'A provision described as "specified" is never counted as "demonstrated".'),
        ('Default missing answers', 'A blank answer is "unknown" and is reported as a gap.'),
        ('Present microgravity results as lunar measurements', 'The curated experiments were in microgravity; lunar transfer is flagged as an unproven step.'),
        ('Call a short findings list "safe"', 'Few findings can simply mean few inputs were supplied.')]),
    table(['Who', 'How they use it'], [
        ('Mission leads and early-stage design teams', 'Prepare a fire-safety review agenda and see which information to gather first.'),
        ('Students and researchers', 'Find the relevant NASA experiments, see their exact measurements and limits, cite the original tables.'),
        ('Safety specialists', 'Use the cited findings and the report as a structured starting point; check every source themselves.'),
        ('Challenge judges and reviewers', 'Run the one-click demo, change a filter, open the original NASA record, and download the data and source code.')]))

body += '''<section class="page"><h1>10. How it is delivered</h1>
<p class="lede">A free, public website that works on any device and needs no account.</p>
%s
<h3>Built to be inspected</h3>
<p>The whole project, including the engine, the interface, the tests and the deployment files, is a single repository that anyone can download from the site itself as a source archive. The curated data set and every pinned NASA table are downloadable too. The page is designed to adapt to phones, tablets, laptops and ultra-wide screens, and to portrait and landscape orientations.</p>
<h1 style="margin-top:12mm">11. Status and history</h1>
%s
</section>''' % (
    table(['Item', 'Detail'], [
        ('Address', 'https://astroflare.onrender.com (free plan; wakes in about a minute after 15 minutes idle)'),
        ('Runs as', 'One Docker container: interface (Node), assessment engine (Python), private AI router (FreeLLMAPI)'),
        ('Cost', 'Free hosting; the AI uses free-tier model quotas, shared across all visitors with fixed per-minute limits'),
        ('Visitor data', 'None stored. The server is stateless and keeps no mission data; saved answers stay in the user\'s own browser only when asked'),
        ('Safeguards', 'Strict content-security policy, request size limits, per-visitor AI and analysis limits, private engine and router')]),
    table(['When', 'What'], [
        ('Original project', 'Python guided screening workflow, 14-document evidence library, optional AI (Anthropic or a local router).'),
        ('Research edition', 'Vortex Aathish Studios added the NASA PSI research explorer, curated and hash-pinned data, and a redesigned interface.'),
        ('Consolidation', 'The Python engine moved into the same repository; one Render service now serves the whole product with AI enabled.'),
        ('Interface redesign', 'A plain, typographic, light design with baby blue and baby green as small accents; fluid layout for any screen shape.'),
        ('Testing and hardening', 'Full test pass; a missing content-security policy was found and fixed; tests added.'),
        ('Now', 'Live at astroflare.onrender.com from a fork branch; pull request #1 open on the Vortex repository awaiting review and merge.')]))

body += '''<section class="page"><h1>12. Limits and next steps</h1>
<h3>Known limits</h3>
<ul><li><b>Not validated.</b> Rules, wording and index points are developer choices informed by a small set of documents; no experiment, simulation or independent expert has checked them.</li>
<li><b>Thin evidence.</b> 14 documents, 13 read at abstract level only, some decades old, one standard possibly superseded. The battery path has two sources and no model of cell chemistry or thermal propagation.</li>
<li><b>Microgravity is not the Moon.</b> The explorer's three experiments were done in orbit. Transfer to a lunar habitat is flagged, not asserted.</li>
<li><b>Answers are taken as reported.</b> "Verified" is something the user asserts; AstroFlare cannot check it.</li>
<li><b>Keyword reading is shallow.</b> Unusual wording can be missed, which is why every proposal shows its quote and needs a tick.</li>
<li><b>AI text can be wrong.</b> The checks catch unsupported numbers and forbidden claims, not subtle misstatements. It is labelled for that reason.</li>
<li><b>Free-tier volatility.</b> The AI depends on free model quotas; a model can go into cooldown, in which case the next model is used.</li></ul>
<h3>Next steps</h3>
%s
<h3>Glossary</h3>
%s
</section>''' % (
    table(['Priority', 'Step', 'Why'], [
        ('1', 'Merge pull request #1 and point the Render service at the Vortex repository', 'One original repository for the whole project'),
        ('2', 'Run the browser-simulation test suite in CI after approval', 'These 34 tests could not run on the development laptop'),
        ('3', 'Read the evidence library beyond abstracts, starting with the battery hazard', 'Strengthens the thinnest part'),
        ('4', 'Have a qualified fire-safety reviewer examine the rules and wording', 'Only independent review can move beyond "not validated"'),
        ('5', 'Add a lunar-gravity-relevant data source if one becomes available', 'Closes the biggest evidence gap the explorer reports')]),
    table(['Term', 'Meaning'], [
        ('PSI', 'NASA Physical Sciences Informatics: the public repository of experiment data used by the explorer'),
        ('BASS-II, Saffire I and II', 'NASA ISS and Cygnus experiments on burning solid materials in microgravity (PSI-25, PSI-98, PSI-99)'),
        ('Microgravity', 'Very low effective gravity, as on the International Space Station'),
        ('Concurrent / opposed flow', 'Air moving in the same direction the flame spreads, or against it'),
        ('Let-through energy (I squared t)', 'Energy passed by a faulted circuit before its protection clears; shown but never compared to an ignition limit'),
        ('Basis', 'How an answer is known: specification, test, analysis, estimate or assumption'),
        ('NTRS', 'NASA Technical Reports Server, where the literature records were checked'),
        ('FreeLLMAPI', 'Open-source router that pools free-tier AI models behind one interface'),
        ('CSP', 'Content-security policy: a browser rule limiting what scripts a page may run')]))

(ROOT / 'docs/AstroFlare-Project-Brief.html').write_text(page('AstroFlare: Project Brief', body, 'AstroFlare · Project Brief'), encoding='utf-8')
print('brief written', len(body))
