import json, re
from common import *
import assessment as A
import guide

src = (ROOT / 'engine/assessment.py').read_text(encoding='utf-8')
finds = []
seen = set()
for m in re.finditer(r'finding\(\s*"(\w+)",\s*"(\w+)",\s*"([^"]+)"', src):
    k = (m.group(1), m.group(2))
    if k not in seen:
        seen.add(k)
        finds.append((m.group(1), m.group(2), m.group(3)))
kinds = {}
for _, k, _ in finds:
    kinds[k] = kinds.get(k, 0) + 1


def lines(p):
    try:
        return len((ROOT / p).read_text(encoding='utf-8').splitlines())
    except Exception:
        return 0


def arch():
    s = '<svg viewBox="0 0 720 360" width="100%">'
    def box(x, y, w, h, fill=None, dash=False):
        return '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#111" stroke-width="1"%s/>' % (x, y, w, h, fill or 'none', ' stroke-dasharray="4 3"' if dash else '')
    s += box(150, 62, 560, 232, '#f7f7f5')
    s += svg_text(162, 80, 'ONE RENDER FREE DOCKER CONTAINER', 8.5, 700, '#555')
    s += box(8, 96, 118, 52) + svg_text(18, 118, 'Visitor', 12, 700) + svg_text(18, 134, 'any device, browser', 9, 400, '#555')
    s += '<path d="M126 122 h40" stroke="#111"/><path d="M160 118 l6 4 -6 4" fill="none" stroke="#111"/>'
    s += box(166, 92, 150, 64, '#fff') + '<rect x="166" y="84" width="22" height="8" fill="#b9ddf3"/>' + svg_text(176, 114, 'Interface (Node)', 12, 700) + svg_text(176, 129, 'server.mjs + worker.js', 9, 400, '#555') + svg_text(176, 143, 'pages, CSP, relay', 9, 400, '#555')
    s += '<path d="M316 124 h36" stroke="#111"/><path d="M346 120 l6 4 -6 4" fill="none" stroke="#111"/>' + svg_text(318, 116, '127.0.0.1:8001', 8, 400, '#767676')
    s += box(352, 92, 160, 64, '#fff') + '<rect x="352" y="84" width="22" height="8" fill="#b9ddf3"/>' + svg_text(362, 114, 'Assessment engine', 12, 700) + svg_text(362, 129, 'Python, standard library', 9, 400, '#555') + svg_text(362, 143, 'rules, checks, limits', 9, 400, '#555')
    s += '<path d="M432 156 v40" stroke="#111"/><path d="M428 190 l4 6 4 -6" fill="none" stroke="#111"/>' + svg_text(438, 180, '127.0.0.1:3001', 8, 400, '#767676')
    s += box(352, 196, 160, 64, '#fff') + '<rect x="352" y="188" width="22" height="8" fill="#b9e6c5"/>' + svg_text(362, 218, 'FreeLLMAPI router', 12, 700) + svg_text(362, 233, 'Node, SQLite (empty at', 9, 400, '#555') + svg_text(362, 247, 'each start), key from env', 9, 400, '#555')
    s += box(530, 92, 172, 64, '#fff') + svg_text(540, 114, 'Data in the image', 12, 700) + svg_text(540, 129, 'dataset.json, sources.json', 9, 400, '#555') + svg_text(540, 143, 'pinned NASA CSV tables', 9, 400, '#555')
    s += '<path d="M512 124 h18" stroke="#111"/>'
    s += box(166, 196, 150, 64, '#fff') + svg_text(176, 218, 'render_start.py', 12, 700) + svg_text(176, 233, 'starts the three programs,', 9, 400, '#555') + svg_text(176, 247, 'hands the router key on', 9, 400, '#555')
    s += '<path d="M512 228 h40" stroke="#111"/><path d="M546 224 l6 4 -6 4" fill="none" stroke="#111"/>'
    s += box(552, 196, 150, 64, '#fff', True) + svg_text(562, 218, 'Google Gemini', 12, 700) + svg_text(562, 233, 'free tier, models tried', 9, 400, '#555') + svg_text(562, 247, 'in order', 9, 400, '#555')
    s += box(352, 310, 160, 40, '#fff', True) + svg_text(362, 328, 'NASA DONKI (flares)', 11, 700) + svg_text(362, 342, 'NTRS (record checks)', 9, 400, '#555')
    s += '<path d="M432 260 v0" stroke="#111"/><path d="M432 156 C 560 190 560 300 512 330" fill="none" stroke="#999" stroke-dasharray="3 3"/>'
    s += '</svg>'
    return s


body = cover('Technical reference  ·  architecture, engine, API, operations', 'AstroFlare', 'How the system is built, how it behaves, and how to run, change and verify it.',
             [('Audience', 'Developers, reviewers,<br>and whoever operates the site'), ('Version', 'Engine 2026.10.21-2<br>Document of %s' % DATE), ('Repository', 'Vortex-Aathish-Studios-2010/<br>astroflare')])

body += '''<section><h1>1. Architecture</h1>
<p class="lede">Three programs in one container; only the interface is public.</p>
<figure>%s<figcaption>Runtime layout on Render. Solid arrows are local connections inside the container; dashed boxes are external services.</figcaption></figure>
<h3>Design decisions</h3>
<ul><li><b>Engine in Python, standard library only.</b> No third-party packages: nothing to install, no supply chain to audit, and the whole engine runs from a single command.</li>
<li><b>Interface as a thin Node server.</b> It serves one self-contained page (one inline script, pinned by hash in the CSP) and relays a fixed list of API routes to the engine. The same handler also runs as a Cloudflare Worker, which is how the original public deployment works.</li>
<li><b>AI behind the engine.</b> The browser never talks to an AI service. The engine builds each prompt from validated data, calls the router and validates the reply, so keys and prompts never reach a client.</li>
<li><b>Everything stateless.</b> The server stores no mission data and writes nothing durable. FreeLLMAPI keeps a SQLite file, which is deliberately empty on each start because the free plan keeps no files; its keys are re-seeded from a secret each time.</li>
<li><b>One public port.</b> The router (3001) and the engine (8001) listen on 127.0.0.1 only. Render assigns the public port to the interface.</li></ul>
<h3>Request lifecycle: a mission assessment</h3>
<ol><li>The browser posts answers to <code>/api/assess</code> on the interface (size-capped at 262,144 bytes).</li>
<li>The relay checks route and method against an allow-list, forwards the body and the visitor address (<code>X-Forwarded-For</code>) to <code>http://127.0.0.1:8001</code>, and drops cookies and authorisation headers.</li>
<li>The engine checks host and origin, parses and validates every field against the schema (units, ranges, options), and runs the deterministic assessment.</li>
<li>The result returns through the relay with <code>no-store</code> caching. No AI is involved at this point.</li>
<li>Only if the user presses an AI-backed control does the engine build a prompt, apply the rate limits, call FreeLLMAPI, validate the reply, and return it labelled or withheld.</li></ol>
</section>''' % arch()

fr = [(f['id'], f['label'], f['group'], f['kind'], (f.get('unit') or '').replace('�', '').replace('m³', 'm3')) for f in A.FIELDS]
body += '''<section class="page"><h1>2. Repository layout</h1>
<p class="lede">One repository holds the interface, the engine, the data and the deployment files.</p>
%s
<h3>Build</h3>
<p><code>python build.py</code> composes the page from the original guided interface plus the research explorer scripts and stylesheets, writes <code>public/index.html</code>, computes the SHA-256 of the single inline script for the CSP, embeds every asset and the worker into <code>dist/server/index.js</code>, and rebuilds the downloadable <code>public/source.zip</code>. The Docker image runs this build again so it can never ship a stale bundle.</p>
</section>''' % table(['Path', 'Lines', 'Purpose'], [
    ('engine/server.py', lines('engine/server.py'), 'HTTP routes, settings, rate limits, host checks, NASA data, AI service calls and fallback'),
    ('engine/assessment.py', lines('engine/assessment.py'), 'Deterministic engine: 33 inputs, validation, calculations, rules, index, basis, next steps'),
    ('engine/guide.py', lines('engine/guide.py'), 'Question flow and branching, review profile, keyword mission reading, checks on suggested values'),
    ('engine/report.py', lines('engine/report.py'), 'Explanation prompt and validator, shared text checks, public messages, Markdown report'),
    ('engine/investigate.py', lines('engine/investigate.py'), 'Sensitivity, what-if, explanations, question routing, answer validator'),
    ('engine/evidence.py + evidence/sources.json', lines('engine/evidence.py'), 'Library of 14 NASA documents (37 statements), citation lookup, live record checks'),
    ('engine/research.py', lines('engine/research.py'), 'Optional AI answers about the curated PSI records and their validator'),
    ('engine/render_start.py', lines('engine/render_start.py'), 'Starts router, engine and interface; passes the router key to the engine only'),
    ('engine/check_keys.py', lines('engine/check_keys.py'), 'Live setup check that never prints a key'),
    ('worker.js / server.mjs', lines('worker.js') + lines('server.mjs'), 'Relay, asset serving, CSP and security headers; Node adapter'),
    ('build.py', lines('build.py'), 'Builds the page, the CSP hash, the bundle and the source archive'),
    ('public/*.js, *.css, index.html', lines('public/index.html'), 'Interface scripts and styles (explorer, motion, theme), built page'),
    ('public/dataset.json, sources/', '-', 'Curated PSI records; pinned original CSV tables, hashes, metadata snapshots'),
    ('engine/test_*.py, test/*.mjs', '-', 'Python tests (491) and Node tests (relay, explorer, reliability)'),
    ('Dockerfile, render.yaml, .dockerignore', '-', 'Container build and Render service definition (no secrets)')], num=(1,))

body += '''<section class="page"><h1>3. The assessment engine</h1>
<p class="lede">Deterministic code: the same answers always give the same result.</p>
<h3>Inputs (%d fields, six groups)</h3>
<p>Selects are checked against fixed options; numbers against units and ranges. A blank answer becomes <i>unknown</i>; each answer can carry a basis (specification, test, analysis, estimate, assumption).</p>
%s
</section>''' % (len(fr), table(['Id', 'Label', 'Group', 'Kind', 'Unit'], fr))

bys = {}
for fid, k, t in finds:
    bys.setdefault(k, []).append((fid, t))
frows = [(fid, k, t) for fid, k, t in finds]
ns = [(i, v[0], v[1][:104] + ('…' if len(v[1]) > 104 else '')) for i, v in A.NEXT_STEPS.items()]
body += '''<section class="page"><h1>3. The assessment engine (continued)</h1>
<h3>Hazards and layers</h3>
%s
<h3>Calculations</h3>
<p>Each is dimension-checked, reported to the significant figures of its inputs, and shown with formula, assumptions and limits.</p>
%s
<div class="note"><b>No ignition-limit comparison.</b> Let-through energy is shown but never compared with an ignition threshold, because the project holds none. This is stated wherever the value appears.</div>
<h3>The heuristic index</h3>
<p>A sum of developer-chosen points over the factors that apply to the hazard (gravity, mission phase, ventilation and, for battery and isolation hazards, extra terms). It is computed only when every needed input was supplied, labelled uncalibrated and unvalidated, comparable only within the same hazard, and has no tiers and no 0-100 scale. An earlier score with silent defaults was removed.</p>
<h3>Basis rules</h3>
<p>A weak basis (estimate, assumption) is listed in the limitations. A provision claimed at its strongest level ("verified", "tested") with only an estimate behind it is flagged as unverified; one with no stated basis is flagged as unchecked. The basis never changes a calculation or a rule.</p>
<h3>Sensitivity</h3>
<p>"Which answer matters most" re-runs the assessment with each select-type answer changed in turn (about 150 runs) and reports how far the index moves and which findings appear or disappear. Numeric answers are not varied because no defensible range exists. Limited to 12 runs per visitor per minute in production.</p>
</section>''' % (
    table(['Hazard', 'Label'], [(k, v) for k, v in A.HAZARD_LABELS.items()]) + table(['Layer', 'Inputs it covers'], [(n, ', '.join(ids)) for n, ids in A.LAYERS]),
    table(['Calculation', 'Notes'], [('Nominal circuit power', 'voltage times operating current'), ('Let-through energy (I squared t)', 'from fault current and clearing time; shown, never compared with a limit'), ('Oxygen partial pressure', 'and its ratio to sea-level air'), ('Air turnover time', 'compartment volume divided by ventilation flow'), ('Minimum round-trip delay', 'from one-way communication delay'), ('Pressure conversion', 'between psia and kPa')]))

body += '''<section class="page"><h1>3. The assessment engine (findings)</h1>
<p class="lede">%d rules produce findings of four kinds. Each carries reasoning, relevance, limits, cited statements, and whether it is sourced, an inference or a calculation.</p>
%s
<h3>Next steps (%d fixed)</h3>
%s
</section>''' % (len(finds), table(['Rule id', 'Kind', 'Title'], frows), len(ns), table(['Id', 'Kind', 'Action'], ns))

body += '''<section class="page"><h1>4. Evidence data and the explorer</h1>
<h3>Literature library</h3>
<p><code>engine/evidence/sources.json</code> (library version 2026-10-21): 14 sources, 37 statements, plus "tensions" notes where cited statements concern different conditions and cannot be combined. Each statement has an id such as <code>S04.c2</code>; findings cite those ids. Verification checks each record live at NTRS for existence and matching title (rate-limited to one real check per 30 seconds); it does not re-read content.</p>
<h3>PSI data set</h3>
<p><code>public/dataset.json</code> holds three investigations and eight curated runs, each with the original raw row, units, conditions, outcome fields and a source link. Every original CSV under <code>sources/</code> is pinned by SHA-256, and <code>test/source-audit.py</code> re-checks curated values against the pinned bytes. Unreported fields are shown as "Not reported" and a number is never inferred.</p>
<h3>Ranking algorithm (<code>public/research.js</code>)</h3>
%s
<h3>Evidence answers</h3>
<ul><li>A named investigation and a requested measurement are resolved before ranking: "Saffire II", "Saffire 2" and "PSI-99" all map to PSI-99 only.</li>
<li>Flame-spread rate, burn time, airflow, oxygen and carbon monoxide are separate quantities; a question naming more than one is asked to be narrowed.</li>
<li>Requests for safe limits, predictions, certification or numeric extrapolation return a gap message. Lunar-gravity flame spread returns the explicit statement that no lunar measurement exists.</li>
<li>Each answer ends with the NASA table link, file name and row id. A latest-request-wins coordinator discards late responses when the user changes the question or filters.</li></ul>
</section>''' % table(['Rule', 'Points'], [('Each recognised question topic (solid materials, flame spread, ventilation, oxygen, microgravity, combustion gases); repeats count once', '+2'), ('Variable-flow investigation when airflow is asked about', '+1'), ('Specific material named in the question or filter and supported', '+2'), ('Exact scenario-gravity match (a mismatch is disclosed, no point)', '+1'), ('Ties', 'fixed order: BASS-II, Saffire II, Saffire I')])

body += '''<section class="page"><h1>5. The AI subsystem</h1>
<h3>Providers</h3>
%s
<h3>Calls and fallback</h3>
<p>The engine sends an OpenAI-style chat request to the router. For each model in the configured list (up to five), a model that fails for a provider-side reason (retired, rate-limited or cooling down, slow, bad response, truncated) is skipped and the next is tried, inside a 70-second total budget; a model that stays silent is abandoned after 30 seconds while others remain. Failures that no other model can fix (such as an invalid key) stop immediately. Errors are reduced to generic public messages; provider names, models, keys and stack traces appear only in developer mode, which production ignores.</p>
<h3>The shared text checks</h3>
%s
<h3>Limits</h3>
%s
<h3>Router start-up on Render</h3>
<ol><li><code>render_start.py</code> starts FreeLLMAPI on 127.0.0.1:3001 with an encryption key (random if unset) and a database path in the container.</li>
<li>FreeLLMAPI applies <code>FREEAPI_CONFIG_JSON</code> on boot, loading the provider keys.</li>
<li>When the router answers, the script reads the router's freshly generated access key from its settings table (read-only) and starts the engine with it. The key is never printed and never given to the interface.</li>
<li>The engine starts on 127.0.0.1:8001; when its health check passes the interface starts on the public port.</li>
<li>If the router fails to start, the site still runs without AI. Router and engine are restarted up to five times if they crash.</li></ol>
</section>''' % (
    table(['Setting', 'Value / behaviour'], [('AI_PROVIDER', 'freellmapi (live), anthropic (supported, not exercised live) or invalid'), ('FREELLMAPI_MODEL', 'live: gemini-3.6-flash, gemini-3.5-flash-lite, gemini-3.5-flash (comma list, up to 5)'), ('Router base URL', 'http://127.0.0.1:3001/v1 inside the container; plain http is accepted only for localhost'), ('Response caps', 'explanations 1,500 tokens (4,000 for structured notes); mission reading and answers bounded and validated')]),
    table(['Check', 'Rejects'], [('Links and citations', 'URLs, DOIs, bracketed numbers, "et al"'), ('Disclosure', 'Mentions of models, providers, routers or "as an AI"'), ('Filler', 'Marketing and filler phrases'), ('Numbers', 'Any digit or spelled-out number not present in the results or question'), ('Claims', 'Unnegated safety, validation, certification, probability, likelihood, confidence or margin words'), ('Sources', 'Unknown source ids; answers must cite at least one real id'), ('Shape', 'Anything but the fixed JSON structure; answers over the length cap')]),
    table(['Limit', 'Value'], [('AI calls, whole site', '12 per minute in production (6 locally)'), ('Per visitor', 'at most half of the site budget'), ('Sensitivity runs', '12 per visitor per minute in production'), ('Body size', 'relay 262,144 bytes; engine 20,000 bytes'), ('Mission text / question', '2,000 / 400 characters')]))

routes = [('GET', '/healthz', 'Interface liveness; reports whether the relay uses the local engine'), ('GET', '/api/status', 'Public status: engine version, AI availability, evidence counts (no provider or key detail)'), ('GET', '/api/schema', 'Guided schema, examples and methodology'), ('GET', '/api/evidence', 'Evidence library and verification summary'), ('GET', '/api/nasa/flares', 'Last 30 days of NASA DONKI flares, cached 15 minutes'), ('POST', '/api/evidence/verify', 'Live re-check of the 14 source records'), ('POST', '/api/guide/flow', 'Next question group from answers and goal'), ('POST', '/api/guide/profile', 'Review profile: entered, estimates, assumptions, unknowns'), ('POST', '/api/guide/interpret', 'Mission text to proposed values; optional AI reading'), ('POST', '/api/assess', 'Run the assessment'), ('POST', '/api/compare', 'Compare a baseline and a current assessment'), ('POST', '/api/investigate', 'Sensitivity, calculation, evidence, missing, verify, what-if'), ('POST', '/api/report', 'Assessment plus optional AI explanation and report data'), ('POST', '/api/ask', 'Typed follow-up: rules first, then checked AI answer'), ('POST', '/api/research/ask', 'Optional AI explanation of the curated PSI records')]
body += '''<section class="page"><h1>6. API reference</h1>
<p class="lede">Fifteen routes reach the engine through a fixed allow-list. Anything else returns 404; wrong methods return 405.</p>
%s
<h3>Static assets</h3>
%s
<h3>Error behaviour</h3>
<p>400 invalid input (the message names the field); 404 unknown route; 405 wrong method; 413 oversized body; 415 non-JSON content type; 429 per-visitor limit; 502 engine unavailable (relay). AI failures are not HTTP errors: they return 200 with a mode of <code>unavailable</code> or <code>withheld</code> and a plain message.</p>
</section>''' % (table(['Method', 'Route', 'Purpose'], routes),
                  table(['Path', 'Content'], [('/', 'The interface (single page)'), ('/documentation', 'Project README as text'), ('/dataset.json', 'Curated PSI records'), ('/sources/PSI-nn-table.csv', 'Pinned original NASA tables'), ('/source.zip', 'Source archive of the whole project'), ('/*.ttf', 'Instrument Serif and Instrument Sans'), ('/verification, /control-audit, /release-checks.json', 'Earlier verification records')]))

body += '''<section class="page"><h1>7. Security</h1>
%s
<div class="note"><b>Found and fixed during testing.</b> The Node interface initially sent only two security headers. The content-security policy, frame, permissions and HSTS headers that the earlier Python site sent were missing. The build now hashes the page's single inline script and the server sends a strict policy that allows only that script; tests assert the hash matches. See the test report.</div>
<h3>Secrets</h3>
<ul><li>Provider keys live only in the Render secret <code>FREEAPI_CONFIG_JSON</code>. They are never in the repository, the image (<code>.dockerignore</code> excludes <code>.env</code>) or logs.</li>
<li>The router's access key is generated at each start and handed only to the engine. Error text from services is stripped of key-like strings before use.</li>
<li>Developer-only routes and diagnostics are disabled in production regardless of settings.</li></ul>
</section>''' % table(['Layer', 'Protection'], [
    ('Content-Security-Policy', "default-src 'self'; script-src 'self' plus the page script hash; connect-src 'self'; frame-ancestors, base-uri, form-action, object-src none; no unsafe-eval"),
    ('Other headers', 'X-Frame-Options DENY, Permissions-Policy (camera, microphone, geolocation, payment off), Cross-Origin-Opener-Policy same-origin, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin, HSTS over HTTPS'),
    ('Page behaviour', 'Everything renders as text: no innerHTML for user text, no eval, no inline handlers'),
    ('Relay', 'Fixed routes and methods, size cap, 90-second timeout, redirects rejected, cookies and authorisation never forwarded'),
    ('Engine', 'Host and origin checks (against DNS rebinding and cross-site calls), no CORS, JSON-only bodies, per-visitor limits'),
    ('Network', 'Router and engine on loopback only; only the interface is reachable'),
    ('Data', 'Stateless server; no mission data stored; logs record method, path and status only')])

env = [('ASTROFLARE_ENV', 'production', 'Binds the engine for hosting, disables developer mode, adds per-visitor limits'), ('AI_PROVIDER', 'freellmapi', 'Selects the AI service'), ('FREELLMAPI_MODEL', 'gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.5-flash', 'Models tried in order'), ('FREEAPI_CONFIG_JSON', 'secret', 'FreeLLMAPI provider keys, e.g. {"keys":[{"platform":"google","key":"..."}]}'), ('ASTROFLARE_UPSTREAM', 'set by render_start.py', 'Interface relay target: http://127.0.0.1:8001'), ('FREELLMAPI_API_KEY / BASE_URL', 'set by render_start.py', 'Router access key (generated) and local address, given to the engine only'), ('ENCRYPTION_KEY', 'optional', 'Router database key; random per start if unset'), ('PORT', 'Render', 'Public port for the interface'), ('ASTROFLARE_AI_RATE_PER_MIN', 'optional', 'Site-wide AI calls per minute (default 12)'), ('ASTROFLARE_ALLOWED_HOSTS', 'optional', 'Extra host names; Render\'s own is added automatically')]
body += '''<section class="page"><h1>8. Deployment</h1>
<h3>Render service</h3>
%s
<h3>Configuration</h3>
%s
<h3>Free-plan behaviour</h3>
<ul><li>The service sleeps after about 15 minutes without traffic; the next visit takes about a minute while all three programs start, and the router re-loads its keys.</li>
<li>Memory is 512 MB for everything: the router's Node heap is capped at 256 MB and the interface's at 96 MB.</li>
<li>Auto-deploy is off. A change goes live after <b>Manual Deploy, Deploy latest commit</b>; a failed build leaves the previous version serving.</li>
<li>FreeLLMAPI's usage statistics and any dashboard changes reset on every start; its keys and the generated access key are re-created automatically.</li></ul>
<h3>Repositories and branches</h3>
%s
</section>''' % (
    table(['Item', 'Value'], [('Service', 'astroflare, Docker, free plan, health check /healthz'), ('Source now', 'bassim-ms/astroflare-vortex, branch feat/render-engine-and-ai (fork)'), ('Target source', 'Vortex-Aathish-Studios-2010/astroflare, branch main, after pull request #1 is merged'), ('Image', 'python:3.13-slim-bookworm with Node and the router copied from ghcr.io/tashfeenahmed/freellmapi:latest'), ('Blueprint', 'Disconnected; the service is managed directly. render.yaml documents the intended settings')]),
    table(['Variable', 'Value', 'Purpose'], env),
    table(['Repository / branch', 'Role'], [('Vortex-Aathish-Studios-2010/astroflare, main', 'Intended single original repository'), ('bassim-ms/astroflare-vortex, feat/render-engine-and-ai', 'Fork carrying PR #1; what Render builds today'), ('bassim-ms/astroflare (private), main', 'Backup of the Python-only version with the earlier Render and FreeLLMAPI setup'), ('bassim-ms/astroflare (private), feat/gemini-provider', 'Unmerged alternative: direct Google Gemini provider')]))

body += '''<section class="page"><h1>9. Operations runbook</h1>
%s
<h3>Troubleshooting</h3>
%s
</section>''' % (
    table(['Task', 'How'], [
        ('Deploy a change', 'Push to the branch Render builds, then Render: astroflare, Manual Deploy, Deploy latest commit. Watch the build log; the old version serves until the new one passes /healthz.'),
        ('Roll back', 'Render: astroflare, Events, choose an earlier successful deploy, Rollback. Or redeploy an earlier commit.'),
        ('Change or add AI keys', 'Render: astroflare, Environment, edit FREEAPI_CONFIG_JSON, then Save, rebuild and deploy. Never paste keys into chat or the repository.'),
        ('Change models', 'Edit FREELLMAPI_MODEL (comma list). Use models the key can actually use; python engine/check_keys.py tests them locally.'),
        ('Read logs', 'Render: astroflare, Logs. The engine logs method, path and status, and a reason code when an AI explanation is withheld.'),
        ('Run locally', 'cd engine and python server.py for the engine alone; node server.mjs for the interface (set ASTROFLARE_UPSTREAM to a local engine).'),
        ('Run the tests', 'cd engine and python -m unittest discover -p "test_*.py"; node --test test/*.test.mjs (needs npm ci for jsdom); python test/source-audit.py.')]),
    table(['Symptom', 'Likely cause', 'What to do'], [
        ('Site slow on first visit', 'Free plan woke from sleep', 'Wait about a minute; nothing to fix'),
        ('"Automated explanations" unavailable', 'FREEAPI_CONFIG_JSON missing or invalid', 'Check the secret exists and is valid JSON; redeploy'),
        ('AI answers slower or from a later model', 'First model in cooldown (free-tier limit)', 'Normal; fallback uses the next. Consider reordering FREELLMAPI_MODEL'),
        ('Explanation "withheld"', 'The consistency checks rejected the reply', 'Retry; read the reason code in the logs if it repeats'),
        ('Deploy fails at build', 'Dockerfile or build.py error', 'Read the build log; build.py asserts the page has exactly one inline script'),
        ('Page blank, console shows CSP error', 'Script changed without rebuilding the hash', 'Run python build.py; the CSP hash is generated, never hand-edited'),
        ('502 from /api routes', 'Engine not running', 'Check the logs for engine restarts; redeploy')]))

(ROOT / 'docs/AstroFlare-Technical-Reference.html').write_text(page('AstroFlare: Technical Reference', body, 'AstroFlare · Technical Reference'), encoding='utf-8')
print('tech written', len(body), 'rules', len(finds), kinds)
