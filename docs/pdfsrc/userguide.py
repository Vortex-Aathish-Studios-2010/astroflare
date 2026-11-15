from common import *


def wire_header():
    s = '<svg viewBox="0 0 720 200" width="100%">'
    s += '<rect x="2" y="2" width="716" height="196" fill="none" stroke="#111"/>'
    s += svg_text(24, 40, 'AstroFlare', 22, 400, '#111', serif=True)
    for i, (t, x) in enumerate([('HOME', 300), ('LUNAR HABITAT DEMO', 358), ('MISSION SCREENING', 502), ('NASA RESEARCH', 636)]):
        s += svg_text(x, 38, t, 8.5, 600, '#111', 'start')
    s += '<rect x="300" y="43" width="26" height="3" fill="#b9ddf3"/>'
    s += svg_text(300, 62, 'SAVE IN THIS BROWSER      LOAD SAVED      START OVER', 8, 400, '#767676')
    for i, (t, x) in enumerate([('1. MISSION', 24), ('2. PROBLEM', 100), ('3. INFORMATION', 176), ('4. REVIEW', 282), ('5. RESULTS', 352), ('6. REPORT', 428)]):
        s += svg_text(x, 106, t, 8.5, 700 if i == 0 else 400, '#111' if i == 0 else '#aaa')
    s += '<rect x="24" y="110" width="60" height="3" fill="#b9ddf3"/>'
    s += '<rect x="24" y="130" width="430" height="52" fill="none" stroke="#111"/>' + svg_text(34, 150, 'The page content for the step you are on', 11, 400, '#555') + svg_text(34, 168, 'Buttons: Back  /  Continue', 9, 400, '#767676')
    for n, x, y in [(1, 6, 14), (2, 290, 24), (3, 290, 76), (4, 14, 102), (5, 462, 150)]:
        s += '<circle cx="%d" cy="%d" r="9" fill="#b9e6c5" stroke="#111"/>' % (x + 8, y) + svg_text(x + 8, y + 4, str(n), 10, 700, '#111', 'middle')
    s += svg_text(486, 154, '5  the working area', 9.5, 400, '#333')
    s += svg_text(486, 40, '1  the AstroFlare wordmark', 9.5, 400, '#333') + svg_text(486, 56, '2  main menu', 9.5, 400, '#333') + svg_text(486, 106, '3  save and restart tools', 9.5, 400, '#333')
    s += svg_text(486, 122, '4  progress through the six stages', 9.5, 400, '#333')
    s += '</svg>'
    return s


def wire_research():
    s = '<svg viewBox="0 0 720 330" width="100%">'
    s += '<rect x="2" y="2" width="716" height="326" fill="none" stroke="#111"/>'
    s += svg_text(18, 30, 'Lunar habitat / evidence workstation', 17, 400, '#111', serif=True)
    s += svg_text(18, 48, 'SCENARIO summary and your research question', 8.5, 400, '#555')
    s += '<rect x="18" y="58" width="70" height="3" fill="#b9ddf3"/>'
    s += '<rect x="18" y="70" width="112" height="22" fill="none" stroke="#111"/>' + svg_text(26, 85, 'VIEW COMPARISON (2)', 7.5, 700) + '<rect x="138" y="70" width="128" height="22" fill="none" stroke="#111"/>' + svg_text(146, 85, 'ASK ABOUT THE EVIDENCE', 7.5, 700)
    for i, t in enumerate(['MATERIAL / FUEL', 'EXPERIMENT GRAVITY', 'AIRFLOW EVIDENCE', 'SCENARIO GRAVITY']):
        x = 18 + i * 166
        s += svg_text(x, 116, t, 7.5, 700, '#555') + '<path d="M%d 134 h148" stroke="#111"/>' % x + svg_text(x, 130, 'Any ...', 9, 400, '#333')
    s += '<path d="M18 150 h684" stroke="#d9d7d2"/>'
    s += svg_text(18, 172, 'Ranked evidence: BASS-II, Saffire II, Saffire I', 12, 400, '#111', serif=True)
    s += '<rect x="18" y="182" width="340" height="104" fill="none" stroke="#111"/>' + svg_text(28, 202, 'Top result: why it ranked first,', 9.5, 400, '#333') + svg_text(28, 216, 'conditions, NASA links, Compare tick', 9.5, 400, '#333')
    s += '<rect x="384" y="182" width="318" height="104" fill="none" stroke="#111"/><rect x="384" y="182" width="318" height="4" fill="#b9e6c5"/>' + svg_text(394, 204, 'What should we test next?', 12, 400, '#111', serif=True) + svg_text(394, 220, 'measured / missing / next step', 9, 400, '#555') + svg_text(394, 236, 'COPY RESEARCH BRIEF + CITATIONS', 7.5, 700)
    s += svg_text(18, 306, 'Below: Compare investigations side by side   |   Ask about the evidence   |   Measurements   |   Methodology', 9, 400, '#555')
    for n, x, y in [(1, 292, 38), (2, 280, 80), (3, 650, 112), (4, 340, 168), (5, 366, 200), (6, 660, 168)]:
        pass
    marks = [(1, 410, 28), (2, 280, 81), (3, 690, 126), (4, 340, 172), (5, 366, 232), (6, 18, 318)]
    for n, x, y in marks[:5]:
        s += '<circle cx="%d" cy="%d" r="9" fill="#b9e6c5" stroke="#111"/>' % (x, y) + svg_text(x, y + 4, str(n), 10, 700, '#111', 'middle')
    s += '</svg>'
    return s


def keys(rows):
    return table(['Control', 'What it does'], rows)


body = cover("User's guide  ·  how to operate AstroFlare", 'AstroFlare', 'Every screen, button and function, in the order you will meet them.',
             [('Open it', 'astroflare.onrender.com<br>any phone, tablet or computer'), ('You need', 'A web browser.<br>No account, no install.'), ('Document of', DATE)])

body += '''<section><h1>1. Start here</h1>
<p class="lede">AstroFlare has two tools on one website. Use the research explorer to find out what NASA experiments say. Use mission screening to find out which fire-safety conditions in a mission deserve a specialist's attention.</p>
<div class="cols">
<div><h3>I want to find NASA evidence</h3><p>Go to <b>Lunar habitat demo</b> or <b>NASA research</b>. You get three NASA experiments ranked for your question, what each measured, and the exact table row behind every number.</p><p><b>Time needed:</b> two minutes for the demo.</p></div>
<div><h3>I want to screen a mission</h3><p>Go to <b>Mission screening</b>. You describe a mission, answer a short guided set of questions, and get a cited list of conditions to review, what is missing, and a report to download.</p><p><b>Time needed:</b> about ten minutes.</p></div></div>
<h3>Before you begin</h3>
<ul><li><b>It is a screening tool, not a safety verdict.</b> It never says a design is safe, never gives a probability, and has not been validated by experiment or by a safety authority. Treat its output as questions for a qualified team.</li>
<li><b>Everything is hypothetical.</b> It is not connected to any spacecraft. Use illustrative numbers if you are exploring.</li>
<li><b>First visit may take about a minute.</b> The free service sleeps when idle; the first page load wakes it. After that it is quick.</li>
<li><b>Nothing is stored about you or your mission.</b> Your answers live in your browser page. They are saved on your device only if you press <b>Save in this browser</b>.</li></ul>
<h3>Two-minute tour</h3>
<ol><li>Open the site and press <b>Run the lunar habitat demo</b>.</li><li>Read the ranked experiments and the line explaining why the first ranked first.</li>
<li>In <b>Ask about the evidence</b>, press <b>What was the flame spread rate in Saffire II?</b></li><li>Read the answer: the number, its conditions, and the link to the original NASA table.</li>
<li>Press <b>Explain with AI (optional)</b> if you want a plain-language explanation. It is labelled as automatically generated.</li></ol>
%s
</section>''' % note('<b>Where the numbers come from.</b> Every figure in the explorer links to the original NASA table and row. Every finding in mission screening cites recorded statements from the 14 NASA documents in the library. Use those links: they are the point of the tool.', True)

body += '''<section class="page"><h1>2. Getting around</h1>
<figure>%s<figcaption>The header and the working area. The mission stages appear when you are in Mission screening.</figcaption></figure>
%s
<h3>Working with the six stages</h3>
<p>Mission screening shows a row of six stages at the top: <b>1 Mission, 2 Problem, 3 Information, 4 Review, 5 Results, 6 Report</b>. The current stage is underlined in baby blue. Stages you have not reached are greyed out; stages you have finished stay clickable so you can go back.</p>
<div class="note"><b>Going back never loses your work.</b> Answers stay in the page while you move between stages. They are lost only if you close or refresh the tab, unless you pressed <b>Save in this browser</b> first.</div>
<h3>On a phone or tablet</h3>
<p>The layout adapts to the screen: the menu wraps onto two lines on narrow screens, tables scroll sideways inside their own area, and buttons become larger on touch screens. On a phone held sideways the title and main buttons still fit on screen.</p>
</section>''' % (wire_header(), keys([
    ('Home', 'The start page with the demo and your own question.'),
    ('Lunar habitat demo', 'Opens the research explorer with a ready-made lunar-habitat question and ranked results.'),
    ('Mission screening', 'Opens the guided mission workflow.'),
    ('NASA research', 'Opens the research explorer.'),
    ('Save in this browser', 'Stores your mission answers on this device, in this browser only.'),
    ('Load saved', 'Restores answers you saved earlier. Saved data that is damaged or invalid is refused and your current answers are left unchanged.'),
    ('Start over', 'Clears your mission and starts again at stage 1.')]))

body += '''<section class="page"><h1>3. The NASA research explorer</h1>
<p class="lede">Find which NASA experiments can inform your question, compare them, and read exactly what they measured.</p>
<figure>%s<figcaption>The explorer page, top to bottom. Numbers: 1 the question and scenario, 2 the two main buttons, 3 the four filters, 4 the ranked results, 5 the proposed follow-up.</figcaption></figure>
<h3>3.1 Your research question</h3>
<p>The page opens on a question. For the demo it is <i>"Which NASA experiments can inform a review of solid-material flammability in a ventilated lunar habitat?"</i> Open <b>Edit research question</b>, type your own, and press <b>Update ranked evidence</b>. The ranking is recalculated with the same fixed rules; nothing is sent to an AI.</p>
<h3>3.2 The filters</h3>
%s
<p>The filters are hard rules, not preferences. If a filter leaves no matching experiment, the page says so and shows <b>Reset experiment filters</b>. A short sentence under the filters explains what changed each time you change one. <b>Restore lunar preset</b> returns to the demo's original question and settings.</p>
<h3>3.3 The ranked results</h3>
<p>Each experiment appears as a result with a <b>Why this ranked first</b> (or second, third) line listing every point it earned, for example <i>solid materials +2; flame spread +2; ventilation +2; variable-flow coverage +1</i>. The score is <b>research relevance only, not fire risk</b>. Under each result:</p>
%s
</section>''' % (wire_research(),
                  table(['Filter', 'Choices'], [
                      ('Material / fuel', 'Any solid material; SIBAL / cotton-fiberglass; PMMA; Silicone; Gaseous fuel (coverage check)'),
                      ('Experiment gravity', 'Any gravity; Microgravity; Lunar surface; Earth gravity'),
                      ('Airflow evidence', 'Any airflow; Forced ventilation; Variable-flow investigation; Documented 20 cm/s; Concurrent-flow investigation; Opposed-flow investigation; Quiescent (coverage check)'),
                      ('Scenario gravity (for transfer limits)', 'Lunar surface; Microgravity; Earth gravity; Unspecified. This sets the gravity your scenario is about, so the page can warn when an experiment was done in a different gravity.')]),
                  keys([('Open NASA PSI record / Original PSI CSV', 'Opens NASA\'s own page, or downloads the exact original table.'),
                        ('Compare (tick box)', 'Selects the experiment for side-by-side comparison. Two can be selected at a time.'),
                        ('All documented conditions & measurement notes', 'Expands the detail: conditions, notes and the AstroFlare interpretation, clearly separated.'),
                        ('Evidence types, selected rows and limits', 'Shows which rows were selected and what the data cannot tell you.')]))

body += '''<section class="page"><h1>3. The NASA research explorer (continued)</h1>
<h3>3.4 What should we test next?</h3>
<p>This panel turns the top result into a proposed follow-up, in three parts: <b>What NASA measured</b>, <b>What's missing for this scenario</b> and <b>Next research step</b>. It is <b>AstroFlare's proposal, not a NASA recommendation</b>. Open <b>Variable and fixed conditions for the proposed study</b> to see what to change and what to hold fixed.</p>
<p><b>Copy research brief + citations</b> copies the whole panel with the original NASA citations to your clipboard. If your browser blocks clipboard access, a text box appears with the brief already selected, so you can copy it by hand.</p>
<h3>3.5 Compare investigations side by side</h3>
<p>Press <b>View comparison (2)</b> to jump here. The table has one column per experiment and these rows: <b>Study match / curated run match; Material / fuel; Gravity regime; Oxygen concentration; Airflow; Reported outcome (evidence type labelled); NASA source</b>. Reported measurements, published qualitative descriptions and AstroFlare's interpretation are kept in separate rows so you can tell which is which. Use <b>Remove BASS-II</b> or <b>Remove Saffire II</b> to take one out, then tick another result to replace it. A third selection is refused with a message.</p>
<h3>3.6 Ask about the evidence</h3>
<p>Type a question in <b>Your evidence question</b> and press <b>Find cited answer</b> (or press Enter). Three example questions are provided as buttons: <i>What was the flame spread rate in Saffire II? / What flame spread rate was measured in lunar gravity? / What was the flame spread rate in Saffire I?</i></p>
%s
<h3>3.7 Explain with AI (optional)</h3>
<p>Under an answer, <b>Explain with AI (optional)</b> asks for a short plain-language explanation based only on the curated NASA records. While it works, a line says <i>Writing an explanation from the curated NASA records</i>. The result is shown with the label <i>"Automatically generated explanation ... Not written or reviewed by a person; checked for consistency, not scientific correctness"</i> and the records it used. The answer above it never depends on this step.</p>
<ul><li><b>"An explanation was produced but withheld":</b> a safety check rejected it. Press <b>Explain again with AI</b>, or rely on the cited answer above.</li>
<li><b>"The explanation service did not return a usable result":</b> the free AI is busy or unavailable. Try again in a minute.</li></ul>
<h3>3.8 Measurements and methodology</h3>
<p><b>Explore actual measurements: BASS-II carbon monoxide readings</b> shows a bar chart of the final carbon monoxide readings for three runs, with initial readings and conditions. These are gas concentrations, not fire probabilities or safe exposure limits. <b>Methodology, sources and limitations</b> explains the ranking rule and links to the downloadable data set and the full documentation.</p>
</section>''' % table(['You ask about...', 'You get'], [
    ('A named measurement in a named experiment (for example Saffire II spread rate)', 'The value, its conditions, and the NASA table, file and row. Example: 2.1 mm/s for run 2-5, 20 cm/s concurrent flow.'),
    ('Something no experiment measured (for example lunar-gravity flame spread)', 'An honest gap: the curated studies were in microgravity and give no lunar measurement.'),
    ('A field the table does not report (for example Saffire I spread rate in its table)', 'A statement that it is not reported, plus NASA\'s companion report values where they exist, labelled as such.'),
    ('Safety limits, predictions, certification or a value at new conditions', 'A refusal to invent a number. Nothing is predicted or extrapolated.'),
    ('Two experiments at once', 'A request to ask about one experiment at a time.')])

body += '''<section class="page"><h1>4. Mission screening, step by step</h1>
<p class="lede">Describe a mission, answer guided questions, and get cited findings and a report.</p>
<h3>Stage 1: Mission</h3>
<p>Type a description in <b>What mission are you assessing?</b> (up to 2,000 characters). Three example descriptions are offered as links you can click to try the tool. Then choose:</p>
%s
<h4>Reading your description</h4>
<p>After <b>Read my description</b>, a list titled <b>What AstroFlare understood</b> appears. Each item has a tick box, the value it found, a tag, and <b>the exact words it came from</b>. The tag <b>Stated</b> means your words said it directly. <b>Inferred</b> means AstroFlare guessed from context (for example "transit" suggests microgravity); inferred items start <b>unticked</b>, and each says what to confirm. Tick only what is right. Nothing is used until you tick it. When ready, press <b>Use the ticked items and continue</b>.</p>
<p>If the optional AI is available, it may add proposals or up to three clarifying questions. Every AI proposal must quote your own words and passes the same checks as typed answers.</p>
<h3>Stage 2: Problem</h3>
<p>Choose one <b>hazard</b> and one <b>goal</b>, then <b>Continue</b>.</p>
%s
</section>''' % (
    keys([('Read my description', 'Reads your text with keyword rules (and the optional AI) and shows what it understood. It does not move on until you confirm.'),
          ('Skip: I\'ll answer the questions myself', 'Goes straight to the questions without reading any text.'),
          ('Use the ticked items and continue', 'Carries the ticked items forward as answers.')]),
    table(['Choice', 'Meaning'], [
        ('Electrical overheating or arc', 'Heating or arcing in wiring and electrical equipment. Gives a fault current integral (I squared t) when fault data are supplied.'),
        ('Battery thermal event', 'Records the reported stored-energy situation only; it does not model cell chemistry or thermal propagation.'),
        ('Cabin material ignition', 'Depends on how far flammability tests cover your atmosphere and gravity.'),
        ('Persistent smoke or combustion products', 'Detection, ventilation and clean-up provisions after a fire.'),
        ('Goal: Investigate a specific hazard', 'Full screening: asks about the environment, the equipment and the safeguards, then reports conditions that warrant review.'),
        ('Goal: Find out what information is missing', 'A short path: only the hazard and the cabin environment are asked. Everything else is reported as missing, with why it matters.'),
        ('Goal: See which answers matter most', 'Full screening, then a check of how each answer changes the findings and the heuristic index when varied.')]))

body += '''<section class="page"><h1>4. Mission screening (continued)</h1>
<h3>Stage 3: Information</h3>
<p>Questions come in small groups, one group per page, headed <b>Step n of N</b>. For the electrical hazard the groups are: <b>Cabin environment; Mission context; The circuit; Faults and protection; Airflow; Detection, suppression and response; Materials and other ignition sources</b>. Other hazards ask a shorter or different set, and some questions are skipped depending on earlier answers (the page tells you why).</p>
<p>Each question has:</p>
%s
<div class="note g"><b>Be honest about how you know.</b> Choosing a weak basis is fine and is useful: it is reported in the limitations rather than hidden. Choosing "Specification" for something you only assumed would make the result look stronger than it is. A provision marked "verified" with only an estimate behind it is flagged as unverified.</div>
<p>Press <b>Continue</b> after each group, or <b>Back</b> to revise the previous one. A blank answer is treated as unknown. Nothing is ever defaulted.</p>
<h3>Stage 4: Review</h3>
<p>A profile lists what you entered, which answers are <b>estimates</b> or <b>assumptions</b>, which are <b>unknown</b>, the values AstroFlare <b>derived</b> from your answers, and the assumptions it introduced. Any row can be edited without losing the others. Where estimates, assumptions or unknowns exist you must acknowledge them before continuing. Then press <b>Run the assessment</b>.</p>
<h3>Stage 5: Results</h3>
<p>Results are read top to bottom. At the top: <b>Edit answers</b>, <b>Pin as baseline</b> and <b>Prepare report</b>, with counts of calculations, cited statements and a note that independent validation and literature search were not performed.</p>
%s
</section>''' % (
    keys([('Why it matters', 'One line on why AstroFlare asks, so you can judge whether to answer.'),
          ('The question and its units', 'For example kPa or psia for pressure; units are shown and converted for you.'),
          ('I don\'t know', 'Records the answer as unknown instead of guessing. Unknowns are reported as gaps, with why they matter.'),
          ('How do you know this?', 'Basis: not stated; Specification or design document; Test or measurement; Analysis or simulation; My estimate; Working assumption.')]),
    table(['Section', 'What it shows'], [
        ('Assessment overview', 'Your screening question, the scenario in words, the result in one paragraph (for example: how many conditions warrant review and how many information gaps limit the assessment), and the evidence limits.'),
        ('Missing answers and evidence limits', 'Unanswered input fields, and the limits of the scientific evidence behind the findings.'),
        ('Key findings', 'Grouped as a hazard pathway, then conditions warranting review. Each finding has Why this matters, Reasoning, and Limitations and competing explanations, and can show its cited statements.'),
        ('Open source Sxx', 'Opens the source behind a statement: what it establishes, how deeply it was read, and a link to NASA\'s record.'),
        ('Show the reasoning and inputs', 'Expands exactly which of your answers led to the finding.'),
        ('Generate explanation for this mission', 'Optional AI paragraph summarising the results in plain language, labelled as unreviewed.')]))

body += '''<section class="page"><h1>4. Mission screening (continued)</h1>
<h3>Investigate further</h3>
<p>Below the findings, <b>Investigate further</b> runs real calculations on your assessment. Each result is added to a log underneath, so you can compare answers as you go. Six buttons:</p>
%s
<h4>Try a different answer</h4>
<p>Pick an input from the list <b>Input to change</b>, give a new value, and press <b>Compare</b>. AstroFlare re-runs the assessment with only that answer changed and shows what moved. The changed input carries no stated basis in this comparison.</p>
<h4>Pin as baseline</h4>
<p>Press <b>Pin as baseline</b> to remember the current assessment. After you edit answers and run again, the page can show what changed between the two. Use it to see how closing an information gap changes the findings.</p>
<h4>Ask a question about this assessment</h4>
<p>Type a question and press <b>Ask</b> (or Enter). Questions about influence, missing information, calculations, sources and verification are answered by the built-in logic. Other questions may go to the optional AI, which may only answer from this assessment, must cite real findings or sources, and may say it cannot answer.</p>
<h3>Stage 6: Report</h3>
<p>Press <b>Prepare report</b>. The report page offers:</p>
%s
<p>The report contains the mission and objective, every input with its basis, values AstroFlare derived, calculations with formulas, findings with reasoning, the evidence used, missing information, limitations, next steps, the date, and a disclosure of whether any text was automatically generated.</p>
</section>''' % (
    table(['Button', 'Answers'], [
        ('Which answer matters most?', 'Re-runs the assessment with each choice-type answer changed in turn; shows how far the heuristic index moves and which findings appear or disappear.'),
        ('What information is missing?', 'Lists every unanswered input and why it matters.'),
        ('What should I verify before relying on this?', 'Lists answers that rest on estimates, assumptions or no stated basis.'),
        ('Show all calculations', 'Every calculation with formula, inputs, assumptions and limits.'),
        ('What do the cited sources establish?', 'What each cited NASA statement does and does not support.'),
        ('How is the heuristic index built?', 'The exact points behind the single index, and why it is not a probability.')]),
    keys([('Download report (Markdown)', 'A readable report file you can open in any text editor.'),
          ('Download data (JSON)', 'The same assessment as structured data for other tools.'),
          ('Print', 'Prints the report, or saves it as a PDF from your browser\'s print dialog.'),
          ('Back to results', 'Returns to the results without losing anything.')]))

body += '''<section class="page"><h1>5. Reading results correctly</h1>
<p class="lede">The most important skill in using AstroFlare is knowing what a result does and does not mean.</p>
%s
<h3>What not to conclude</h3>
<ul><li><b>"Few findings" does not mean "safe".</b> It may only mean you supplied few answers. Check <b>Missing answers</b> first.</li>
<li><b>A higher index is not higher risk.</b> The index is a developer-chosen heuristic, uncalibrated, comparable only for the same hazard, and shown only when every needed input was supplied.</li>
<li><b>An experiment in microgravity is not a lunar test.</b> The research explorer flags this on every result.</li>
<li><b>"Not reported" is not zero.</b> It means the source table did not give a value.</li>
<li><b>Automatically generated text can be wrong.</b> It is checked for unsupported numbers and forbidden claims, not for subtle mistakes. Read the cited answer, not only the explanation.</li></ul>
<h3>Good habits</h3>
<ul><li>Describe the mission in your own words first; let AstroFlare show you what it understood, and correct it.</li>
<li>Prefer "I don't know" to a guess. A gap is information; a wrong number is not.</li>
<li>State the basis honestly for every number.</li>
<li>Open at least one cited source for each finding you intend to act on.</li>
<li>Pin a baseline before changing answers, so you can see what each change did.</li>
<li>Hand the report to a qualified fire-safety specialist; it is designed as their starting point.</li></ul>
</section>''' % table(['Finding kind', 'Meaning', 'What to do with it'], [
    ('Plausible pathway', 'A way a fire could start for the hazard you chose. Never a demonstrated failure.', 'Use it as an agenda item for review.'),
    ('Condition warranting review', 'Something in your answers a safety team should examine, for example oxygen above Earth air or ventilation that cannot be stopped.', 'Check the reasoning, the limits and the cited source, then decide who must look at it.'),
    ('Information gap', 'Something needed that you did not supply.', 'Gather it, then edit your answers and run again.'),
    ('Context', 'A relevant fact that is not a concern on its own, for example mission duration.', 'Read it; no action implied.')])

body += '''<section class="page"><h1>6. AI features</h1>
<p class="lede">AI is optional, labelled, and checked. Everything it appears beside works without it.</p>
%s
<h3>What you will see</h3>
<ul><li>Text from AI always carries a label such as <i>"Automatically generated ... not written or reviewed by a person"</i>.</li>
<li>If the AI is busy or off, a single plain sentence says so and nothing else changes.</li>
<li>If a reply fails the safety checks it is withheld and you are told so. You can try again or ignore it.</li>
<li>The site shares a limited free AI quota between all visitors, so heavy use in a short time may show "busy". Wait a minute and retry.</li></ul>
<h3>What is sent to the AI</h3>
<p>Only when you press an AI-backed control, and only the fields described: for evidence explanations, your question and the curated NASA records; for mission features, the structured results and the mission description you typed. Never your whole form, never anything from other visitors, and the site stores nothing about you.</p>
</section>''' % table(['Where', 'Control', 'What it does'], [
    ('Mission stage', 'Read my description', 'Also asks the AI for proposals; each must quote your words and still needs your tick.'),
    ('Results stage', 'Generate explanation for this mission', 'A short mission-specific explanation of the results.'),
    ('Investigate stage', 'Ask (for unusual questions)', 'An answer limited to this assessment, citing real findings or sources.'),
    ('Research explorer', 'Explain with AI (optional)', 'A short explanation limited to the curated NASA records, citing the records used.')])

body += '''<section class="page"><h1>7. Saving, sharing and privacy</h1>
%s
<h3>Sharing your results</h3>
<p>Use <b>Download report (Markdown)</b> or <b>Print</b> to share a report. To share explorer evidence, use <b>Copy research brief + citations</b>. The data set and the original NASA tables can be downloaded from the explorer's methodology section, and the entire project source from the site footer.</p>
<h1 style="margin-top:12mm">8. Troubleshooting</h1>
%s
</section>''' % (
    table(['Question', 'Answer'], [
        ('Where are my answers kept?', 'In the open page in your browser. If you press Save in this browser they are stored on this device only; they are never uploaded.'),
        ('Does AstroFlare store my mission?', 'No. The server is stateless and keeps no mission data; logs record only the type of request and its result.'),
        ('Can others see my work?', 'No. Nothing is shared unless you download or copy it yourself.'),
        ('Can I move my work to another device?', 'Download the data (JSON) report, or re-enter your answers; saved answers do not leave the browser they were saved in.'),
        ('What if I clear my browser data?', 'Saved answers are removed with it. Download a report first if you need a copy.')]),
    table(['Problem', 'Try this'], [
        ('The page is slow the first time', 'The free service wakes from sleep. Wait about a minute; later visits are quick.'),
        ('The page says explanations are unavailable', 'The optional AI is off or busy. Everything else works; try again later.'),
        ('"An explanation was produced but withheld"', 'The safety checks rejected the reply. Press the AI button again or use the cited answer.'),
        ('I cannot press Continue', 'A required answer is missing or invalid. The page names the field; fix it or choose I don\'t know.'),
        ('A value is rejected', 'It is outside the allowed range or the wrong unit. Check the unit shown beside the field.'),
        ('Results look empty', 'Few inputs were supplied. Open "Missing answers and evidence limits"; fewer answers means fewer findings, not a safer design.'),
        ('A filter shows no results', 'Press Reset experiment filters; some filters require explicitly documented values.'),
        ('Copy brief did not copy', 'Your browser blocked the clipboard. The brief appears in a text box; select and copy it manually.'),
        ('My saved answers will not load', 'The saved data was damaged or invalid. Current answers are left unchanged; re-enter them or start over.'),
        ('Tables are cut off on my phone', 'Swipe sideways inside the table; the page itself does not scroll sideways.')]))

body += '''<section class="page"><h1>9. Quick reference</h1>
<p class="lede">Every control in one place.</p>
%s
<h3>Glossary</h3>
%s
</section>''' % (
    table(['Where', 'Control', 'Result'], [
        ('Header', 'Home, Lunar habitat demo, Mission screening, NASA research', 'Move between the tools'),
        ('Header', 'Save in this browser, Load saved, Start over', 'Store, restore or clear mission answers'),
        ('Explorer', 'Edit research question, Update ranked evidence', 'Re-rank with your own question'),
        ('Explorer', 'Material, Experiment gravity, Airflow evidence, Scenario gravity', 'Filter and set the scenario'),
        ('Explorer', 'Reset experiment filters, Restore lunar preset', 'Return to the defaults'),
        ('Explorer', 'Compare tick, View comparison, Remove', 'Side-by-side comparison of two experiments'),
        ('Explorer', 'Copy research brief + citations', 'Copy the proposed follow-up with sources'),
        ('Explorer', 'Find cited answer, example questions', 'Exact NASA measurement with its table row'),
        ('Explorer', 'Explain with AI (optional)', 'Checked, labelled plain-language explanation'),
        ('Mission 1', 'Read my description, Skip, Use the ticked items', 'Turn a description into confirmed answers'),
        ('Mission 2', 'Hazard and goal choices, Continue', 'Choose what to screen and how deep'),
        ('Mission 3', 'I don\'t know, How do you know this?, Back, Continue', 'Answer honestly, with your basis'),
        ('Mission 4', 'Edit rows, acknowledge, Run the assessment', 'Check, confirm and run'),
        ('Mission 5', 'Edit answers, Pin as baseline, Prepare report, Generate explanation', 'Work with the results'),
        ('Mission 5', 'Six investigate buttons, Try a different answer, Ask', 'Dig into the results'),
        ('Mission 6', 'Download report, Download data, Print, Back to results', 'Take the report away')]),
    table(['Term', 'Meaning'], [
        ('Hazard', 'The kind of fire event being screened: electrical, battery, cabin material or smoke.'),
        ('Basis', 'How you know an answer: specification, test, analysis, estimate or assumption.'),
        ('Heuristic index', 'One developer-chosen number summarising applicable factors; not a probability or severity.'),
        ('PSI', 'NASA Physical Sciences Informatics, the repository the explorer\'s experiment tables come from.'),
        ('Microgravity', 'Very low effective gravity, as on the International Space Station.'),
        ('Concurrent / opposed flow', 'Air moving the same way the flame spreads, or against it.'),
        ('Let-through energy (I squared t)', 'Energy a faulted circuit passes before protection clears it.'),
        ('Withheld', 'An AI reply that failed the safety checks and was not shown.')]))

(ROOT / 'docs/AstroFlare-Users-Guide.html').write_text(page("AstroFlare: User's Guide", body, "AstroFlare · User's Guide"), encoding='utf-8')
print('guide written', len(body))
