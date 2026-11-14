import json, unittest, importlib, sys, pathlib
from common import *

live = json.load(open('C:/Users/bassi/AppData/Local/Temp/live_results.json'))
loader = unittest.TestLoader()
mods = {}
for f in sorted((ROOT / 'engine').glob('test_*.py')):
    m = importlib.import_module(f.stem)
    n = loader.loadTestsFromModule(m).countTestCases()
    mods[f.stem] = n
total_py = sum(mods.values())

passed = sum(1 for r in live if r['pass'])
retests = [
    ('Report with AI explanation', 'Re-run alone after spacing calls', 'included on both of 2 tries', 'pass'),
    ('Security headers on the home page', 'After the fix and redeploy', 'CSP, X-Frame-Options, Permissions-Policy, COOP, HSTS, nosniff, referrer policy all present', 'pass'),
    ('Non-page assets carry no page policy', 'GET /dataset.json', 'no Content-Security-Policy header', 'pass'),
    ('Page works under the CSP', 'Live page, demo opened, violation listener', '0 policy violations, 3 experiments ranked', 'pass'),
    ('Evidence AI acceptance', '10 spaced requests, 5 questions', '10 of 10 accepted', 'pass')]


def res(ok):
    return '<span style="font-weight:700;color:%s">%s</span>' % ('#2f7a47' if ok else '#a33', 'PASS' if ok else 'FAIL')


body = cover('Test and verification report  ·  %s' % DATE, 'AstroFlare', 'What was tested, how, what was found, and what has not been tested.',
             [('Scope', 'Code, live API, live interface,<br>AI behaviour, security headers'), ('Result', '%d of %d live checks passed first time;<br>both failures were investigated' % (passed, len(live))), ('Under test', 'astroflare.onrender.com<br>commit a04c3dc and earlier')])

body += '''<section><h1>1. Summary</h1>
<p class="lede">Everything tested works. One real defect was found and fixed (missing browser security headers); several smaller findings are recorded below, and the limits of this testing are stated plainly.</p>
<div class="cols3">%s%s%s</div><div class="cols3">%s%s%s</div>
<h3>Verdict</h3>
<p>The site is functionally sound and ready for review. The deterministic engine, the NASA evidence explorer and both AI features behave as designed on the live site. Testing uncovered a regression from the interface migration, a missing Content-Security-Policy and related headers, which is now fixed and verified live. The remaining caveats are about what could not be run on the development laptop (34 browser-simulation tests and a local container build), not about failures.</p>
%s
</section>''' % (stat(str(total_py), 'Python engine tests (all passing; see flake note)'), stat('8', 'Node relay and header tests passing', True), stat('4 / 4', 'NASA source-audit checks'),
                 stat('%d' % len(live), 'live API checks run', True), stat('10 / 10', 'evidence-AI answers accepted (spaced)'), stat('1', 'real defect found and fixed', True),
                 note('<b>Honest scope.</b> Tests were run by the person who built the system, on one Windows laptop, against the live free-tier service, in one browser engine (Chromium). That makes them useful but not independent. The unfinished list in section 8 matters as much as the passes.'))

pyrows = [(k.replace('test_', ''), v) for k, v in mods.items()]
body += '''<section class="page"><h1>2. Automated tests</h1>
<h3>Python engine suite: %d tests</h3>
<p>The suite uses a fake network and needs no keys. It covers validation, every rule and calculation, the shared AI text checks, key handling, security headers, host and origin checks, the new evidence-AI route and checker, the startup script's environments, and the deployment files.</p>
%s
<h4>Repeated runs</h4>
<p>The suite was run five times. Three runs passed completely (491 of 491). Two runs each had exactly one error, in a different test each time. Isolating the cause on repeated runs showed <code>ConnectionAbortedError: [WinError 10053]</code>, where Windows aborts a local test socket. The same intermittent error occurred on the original code before any changes. It is a property of running local socket tests on this machine, not of the application.</p>
<h3>Node tests</h3>
%s
<h3>Source audit</h3>
<p><code>test/source-audit.py</code> re-checks every curated NASA value against the pinned original CSV bytes. All four checks passed: PSI-25 (4 rows), PSI-99 (2 rows), PSI-98 (2 rows), and the NTRS cross-check of Saffire I samples 1-1 and 1-2.</p>
</section>''' % (total_py, table(['Test module', 'Tests'], pyrows, num=(1,)), table(['Check', 'Result', 'Detail'], [
    ('engine-relay.test.mjs', '8 / 8 pass', 'local-engine relay, public fallback, visitor-address forwarding, evidence-AI route, default-export environment, page flags, CSP hash matches the inline script, HSTS follows the connection'),
    ('Syntax checks', 'pass', 'dist/server/index.js, server.mjs, worker.js and the built page script all parse on Node 22'),
    ('Browser-simulation suite (34 tests)', 'not run here', 'Needs jsdom from npm, unavailable on the development laptop. Runs in CI once the Vortex owner approves workflows on the pull request')]))

lrows = [(r['group'], r['name'], r['request'].split(' ', 1)[1] if ' ' in r['request'] else r['request'], str(r['expected']), str(r['status']), '%.1f s' % r['seconds'], res(r['pass'])) for r in live if r['seconds'] or r['group'] != 'AI' or True]
body += '''<section class="page"><h1>3. Live API tests</h1>
<p class="lede">%d checks against https://astroflare.onrender.com covering every public route, bad input, limits, lockdowns, headers and the AI routes.</p>
%s
<div class="note"><b>The two first-run failures.</b> (1) "Report with AI explanation" returned 200 but not the expected status. It was caused by sending several AI calls in a row and meeting the per-visitor rate limit, which is by design. It passed on both of two retries once calls were spaced. (2) "Security headers" was a real defect, covered next.</div>
<h3>Re-tests after investigation and fixes</h3>
%s
</section>''' % (len(live), table(['Group', 'Check', 'Route', 'Expect', 'Got', 'Time', 'Result'], lrows), table(['Check', 'How', 'Result', 'Status'], [(a, b, c, res(d == 'pass')) for a, b, c, d in retests]))

body += '''<section class="page"><h1>4. Live interface tests</h1>
<p class="lede">A scripted walkthrough of the real pages in a browser, against the live engine and AI.</p>
%s
<h3>Responsive and device-shape tests</h3>
<p>The interface was loaded at the sizes below. Each was checked for sideways overflow and legibility, and the layout rules for aspect ratio, orientation, short height and touch were exercised.</p>
%s
</section>''' % (
    table(['Area', 'What was done', 'Result'], [
        ('Home', 'Loaded; title, navigation, both buttons', res(True)),
        ('Lunar demo', 'Opened; experiments ranked PSI-25, PSI-99, PSI-98 (scores 7, 6, 6)', res(True)),
        ('Filters', 'Airflow "documented 20 cm/s" removes BASS-II; reset restores all three', res(True)),
        ('Evidence answers', 'Saffire II spread rate (2.1 mm/s, run 2-5); lunar-gravity gap stated; Saffire I companion rates and the missing table value', res(True)),
        ('Explain with AI (explorer)', 'Button, loading state, result panel; one live result was withheld by the checks, others accepted', res(True)),
        ('Mission screening', 'Typed a mission; reading found 7 items with quotes; ticked all', res(True)),
        ('Guided flow', 'Problem, seven Information groups, Review, Results, run against the live engine', res(True)),
        ('Results page', 'Overview, 9 findings, missing-answer limits, evidence counts, no sideways overflow', res(True)),
        ('AI explanation (mission)', 'Generate button enabled; explanation produced and labelled as unreviewed', res(True)),
        ('Report', 'Report stage reached; Markdown, JSON and Print offered; about 50,000 characters', res(True)),
        ('Security policy in the browser', 'Page and demo ran on the live site with zero policy violations', res(True))]),
    table(['Shape', 'Size', 'Observed', 'Result'], [
        ('Phone, portrait', '375 x 812 and 390 x 844', 'Title wraps, navigation in two lines, buttons fit, no overflow', res(True)),
        ('Phone, landscape', '844 x 390', 'Title, intro and both buttons visible in 390 px of height', res(True)),
        ('Tablet, portrait', '820 x 1180', 'Decision panel and comparison table fit; no overflow', res(True)),
        ('Laptop', '1440 x 900', 'Two-column decision layout; header aligned to content', res(True)),
        ('Ultra-wide', '2560 x 1080', 'Centred, readable column; no stretched lines', res(True))]))

body += '''<section class="page"><h1>5. AI behaviour</h1>
%s
<h3>Observations</h3>
<ul><li><b>Model fallback in action.</b> Render's logs showed <code>google/gemini-3.6-flash: 1 key(s) - cooldown</code> before every request: the first model was in a free-tier cooldown after heavy testing, and the router fell through to <code>gemini-3.5-flash-lite</code> immediately. This is the designed behaviour and explains the roughly two-second answers. It also shows free-tier capacity is shared and can be exhausted.</li>
<li><b>Citation formats.</b> Early on, one of three evidence explanations was withheld because the model wrote citations such as "PSI-99 row 2-5". The checker now accepts format variants that still name a real record or run. Afterward 13 of 13 API requests were accepted (3 plus 10), and one live interface request was withheld, so the checks remain cautious.</li>
<li><b>Safety wording.</b> A question asking whether Saffire II proves a lunar habitat is safe produced no safety claim; the checker rejects unnegated safety words and the system prompt forbids them.</li>
<li><b>Reasons are visible.</b> A withheld explanation now logs its reason code (never text or keys) in Render's logs.</li></ul>
</section>''' % table(['Feature', 'Test', 'Outcome'], [
    ('Mission reading', 'Keyword plus AI reading of a Mars transit description', 'Returned a structured interpretation (about 32 s on the first call)'),
    ('Report explanation', 'Full report with AI narrative', 'Accepted ("included") on retries'),
    ('Typed question, rules', '"What information is missing?"', 'Answered by the built-in rules, no AI'),
    ('Typed question, AI', 'A question outside the rules', 'Answered or withheld by the checks'),
    ('Evidence AI', '3 calls then 10 spaced calls, five different questions', '13 of 13 accepted'),
    ('Evidence AI, interface', 'Button in the explorer, live', 'Loading state shown; result panel shown; one withheld'),
    ('Safety claim request', 'Asked if the experiments prove a habitat is safe', 'No safety claim in the answer')])

body += '''<section class="page"><h1>6. Defects and findings</h1>
%s
<h3>Detail: the missing security headers</h3>
<p><b>Found by:</b> the "security headers" live check. <b>Cause:</b> the earlier Python site served the page itself and sent a strict Content-Security-Policy (script allowed only by hash), HSTS and framing protection. When the Vortex interface (a Node server) took over serving the page, it sent only <code>X-Content-Type-Options</code> and <code>Referrer-Policy</code>. <b>Risk:</b> an injected script would not have been blocked by the browser, and the page could be framed by another site. <b>Fix:</b> <code>build.py</code> now hashes the page's single inline script; the server sends a policy allowing exactly that script, plus X-Frame-Options, Permissions-Policy, Cross-Origin-Opener-Policy and HSTS over HTTPS. <b>Verified:</b> unit tests assert the hash equals the script's SHA-256; the live page runs with zero violations; plain assets such as the data set do not carry the page policy.</p>
</section>''' % table(['#', 'Finding', 'Severity', 'Status'], [
    ('1', 'Content-Security-Policy, frame, permissions and HSTS headers missing on the interface page', 'Medium', 'Fixed, tested, verified live'),
    ('2', 'Leftover chips, grey boxes and tags from the original interface contradicted the plain redesign', 'Low', 'Fixed and verified'),
    ('3', 'Evidence-AI citations in alternative formats were rejected', 'Low', 'Fixed; logging added'),
    ('4', 'First AI model in cooldown on the free tier; fallback hides it', 'Info', 'Observed; consider reordering models'),
    ('5', 'A wording replacement can turn a mid-sentence phrase into "The One condition to review"', 'Cosmetic', 'Open: found in an AI explanation; needs a case-aware replacement'),
    ('6', 'Occasional WinError 10053 in local socket tests on Windows', 'Info', 'Environment; present before any change; one test each time'),
    ('7', 'First deploy of the colour pass used large pastel fills against the request', 'Process', 'Cancelled before it went live; replaced with small accents')])

body += '''<section class="page"><h1>7. What this testing does not show</h1>
<p class="lede">The most important section for anyone relying on these results.</p>
%s
<h1 style="margin-top:10mm">8. Reproducing the tests</h1>
%s
</section>''' % (
    table(['Gap', 'Why it matters', 'How to close it'], [
        ('34 browser-simulation Node tests not run locally', 'They cover many interface behaviours (focus, filters, drafts, storage, reduced motion)', 'Run npm ci and npm test, or approve CI on the pull request'),
        ('Container not built locally', 'No Docker on the laptop; first real build was on Render', 'Covered by CI Docker build and by the live deploys, which succeeded'),
        ('Mission hazards', 'The interface flow ran with one hazard path; the API assessed the three bundled examples; "smoke" was not run live', 'Run each hazard through the interface and API'),
        ('Accessibility', 'No screen-reader, keyboard-only or automated audit was run', 'Run an accessibility audit; test with a screen reader'),
        ('Other browsers', 'Only Chromium-based engines were used', 'Test Firefox and Safari, including iPhone'),
        ('Load and abuse', 'Latency was measured single-user; rate limits were exercised lightly', 'Run a load test and a deliberate abuse test'),
        ('Independence', 'The builder tested their own work', 'A reviewer who did not build it, especially a fire-safety specialist for the content'),
        ('Content validity', 'Tests show the software behaves as specified, not that the safety rules are right', 'Expert review of rules, wording and evidence'),
        ('Visual check of the PDFs', 'The reports were checked structurally and as HTML at page width; the desktop window was not visible for page images', 'Open the PDFs and review the pages')]),
    table(['What', 'Command'], [
        ('Python engine tests', 'cd engine ; python -m unittest discover -p "test_*.py"'),
        ('Node tests', 'npm ci ; npm run build ; npm test'),
        ('NASA data audit', 'python test/source-audit.py'),
        ('Live setup check (keys, AI, NASA)', 'cd engine ; python check_keys.py'),
        ('Live API checks', 'The 44 checks in section 3 are plain HTTPS requests to the routes listed in the technical reference'),
        ('Rebuild the bundle', 'python build.py  (the CSP hash is regenerated)')]))

(ROOT / 'docs/AstroFlare-Test-Report.html').write_text(page('AstroFlare: Test and Verification Report', body, 'AstroFlare · Test Report'), encoding='utf-8')
print('test report written', len(body), total_py, passed, len(live))
