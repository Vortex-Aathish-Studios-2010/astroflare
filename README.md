# AstroFlare · Flame in Freefall (2026 upgrade)

Live project: https://astroflare-research-2026.ajuponnu2009.chatgpt.site/

This is an in-place upgrade of the existing Sites project `appgprj_6af7a9a4f6748191bdc90847b966765a`, branch `main`. Its audience was explicitly changed from owner-private to **public** at the user's request. The separate original Render service at https://astroflare.onrender.com/ was not changed.

## The judging path

The primary homepage button **Run the lunar habitat demo** opens the question “Which NASA experiments can inform a review of solid-material flammability in a ventilated lunar habitat?” It immediately shows ranked NASA PSI evidence, with BASS-II and Saffire II selected for comparison. There is no AI call or account requirement for the research experience.

A 30-second recording:
1. 0–5 s: open the live URL and click **Run the lunar habitat demo**.
2. 5–10 s: show BASS-II's **Why it ranked here** and its lunar transfer warning.
3. 10–17 s: change **Airflow evidence → Documented 20 cm/s**. BASS-II leaves the results because the curated rows lack calibrated velocities; Saffire II becomes first.
4. 17–24 s: change **Airflow evidence → Any airflow**, select BASS-II if necessary, and click **View comparison**. Show conditions, measurements and the separate interpretation rows together.
5. 24–30 s: open **Open NASA PSI record** or **Original experimental table** from the comparison.

The recording needs no data entry. The source archive, curated dataset and pinned CSV downloads are available from the site. The older mission-screening workflow and cached electrical example remain secondary tools.

## Source audit: NASA PSI is the core dataset

Retrieved on **14 November 2026** using NASA's public repository metadata and original experimental-table downloads. Public source pages, metadata APIs and all three original CSV links returned HTTP 200; each downloaded CSV matched its pinned SHA-256 hash. Metadata snapshots and unmodified source CSV bytes are retained under `sources/`. `/dataset.json` contains the full curated records, versions, source links, file names, hashes, selected run IDs, outcomes and raw row values.

| Investigation | PSI ID / metadata version | Selected rows | Original NASA record |
|---|---|---|---|
| Burning and Suppression of Solids – II (BASS-II) | PSI-25 / v4 | T1, T2, T4, B1 | https://psi.nasa.gov/physci/repo/data/investigations/PSI-25 |
| Spacecraft Fire Experiment-II (Saffire II) | PSI-99 / v5 | 2-5, 2-1 | https://psi.nasa.gov/physci/repo/data/investigations/PSI-99 |
| Spacecraft Fire Safety Experiment-I (Saffire I) | PSI-98 / v4 | S1, S2 | https://psi.nasa.gov/physci/repo/data/investigations/PSI-98 |

The NASA PSI metadata API is `https://psi.nasa.gov/geode-py/ws/repo/investigations/{PSI-ID}`. The public original file endpoint is `https://psi.nasa.gov/geode-py/ws/studies/{PSI-ID}/download?file={URL-encoded-filename}&version=1`. It redirects to NASA's current storage download; expiring storage URLs are not embedded in the application.

Original source file names:
- `PSI-25_Experimental table_BASS-II.csv`
- `PSI-99_Experimental table_SAFFIRE-2.csv`
- `PSI-98_Experimental table_SAFFIRE-1.csv`

### Headline scientific claims and exact support

- **BASS-II used an ISS wind tunnel with variable forced flow and oxygen concentration.** PSI-25 `approach` states the facility could impose speeds up to 40 cm/s, and that flame appearance/growth/spread were determined in opposed and concurrent flow. This is investigation context, not a calibrated velocity for any selected CSV row.
- **BASS-II selected fabric rows have final CO readings 40, 78 and 72 ppm.** Rows T1, T2 and T4, column `Final CO (ppm)`. Initial CO was 0, 40 and 59 ppm. Initial calibrated O₂ was 18.5%, 18.5% and 18.7% by volume. The rows identify 2 cm SIBAL samples. These are concentration readings, not emission yields or safe-exposure limits. Uncertainty and calibrated airflow are **Not reported** in the selected table. No display-to-velocity conversion is made.
- **Saffire II sample 2-5 has a reported spread rate 2.1 mm/s and burn time 145 s.** PSI-99 original CSV row 2-5, columns `?-g Spread Length` (mislabelled, but the value explicitly has mm/s units) and `Burn Time (s)`. Row conditions are 20 cm/s concurrent flow, approximately 22.1% O₂, SIBAL cotton/fiberglass. Note 1 says oxygen is derived from CO₂ production referenced to the initial ISS reading. The spread rate is corroborated by NASA NTRS **20170008805**, slide 21: https://ntrs.nasa.gov/citations/20170008805 . Original report file: `20170008805.pdf`, https://ntrs.nasa.gov/api/citations/20170008805/downloads/20170008805.pdf . The original text export and metadata are preserved in `sources/`.
- **Saffire II silicone row 2-1 has burn time “Insignificant”.** This is a published qualitative table entry, not a numeric zero. Note 2 reports that the PMMA portion of sample 2-7 was consumed while Nomex did not ignite; it is specific to that configuration.
- **Saffire I selected burn times are 420 s and 70 s.** PSI-98 CSV rows S1 and S2. Both list 20 cm/s; directions are concurrent and opposed. Its PSI table does not supply a spread-rate outcome. Longer burn time is not interpreted as greater hazard.
- **These are microgravity investigations, not lunar surface validation.** PSI Approach/project context identifies ISS or uncrewed Cygnus experiments. Inferring transfer requires separate consideration of lunar buoyancy, atmosphere, material geometry and ignition conditions. AstroFlare's transfer warning is an engineering limitation, not a published result of a lunar experiment.

### Source defects deliberately retained

- PSI-25 Approach describes oxygen below 21%, but selected run B1 lists calibrated initial O₂ 22.2%. Row-specific values are preserved and the difference is disclosed.
- PSI-99 Approach says flows of 20 or 30 cm/s, while the selected rows say 20 cm/s. Its row 2-6 lists 20 cm/s where NTRS 20170008805 reports 25 cm/s; this conflicting row is not used for a flow-effect claim. Strings such as `037 mm` are not silently corrected. The rate/length column label problem is disclosed.
- PSI-98 CSV lists thickness as 0.37 cm and length/width as 40.6/94 cm; PSI Approach describes approximately 0.94 × 0.4 m, and NTRS reports 0.37 mm thickness. Geometry is flagged as inconsistent. The comparison does not pretend these are interchangeable dimensions.
- Raw source content is never overwritten by a correction. Unreported fields display **Not reported**.

Saffire III (PSI-100) was checked, but not added: the three selected investigations already support the material/ventilation use case, while the retrieved Saffire III table did not add a measured outcome needed for this comparison. BASS-II/Saffire coverage is curated, not exhaustive.

The official challenge link https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/ returned HTTP 503 from this environment on repeated checks. The implementation follows the user's stated challenge and judging requirements; no unverified detail from that inaccessible brief is attributed to the organizers. No award or nomination is promised.

## Ranking and interaction methodology

`public/research.js` implements pure deterministic functions, tested independently:

1. Hard filters include/exclude investigations by material family, gravity and airflow evidence. A numeric 20 cm/s filter requires an explicitly documented value; a broad facility range is not enough. Direction filters operate at investigation coverage level, not at every curated run.
2. Each recognized question-topic match adds **2** points. Topics are solid materials, flame spread/flammability, ventilation/airflow, oxygen/atmosphere, microgravity and combustion gases. Repeated words count once.
3. A variable-flow investigation adds **1** point when the question asks about airflow. A specific material named in the question or selected material filter adds **2** points if supported. An exact scenario-gravity match adds **1** point; a mismatch is disclosed and earns no point.
4. Ties use fixed dataset order: BASS-II, Saffire II, Saffire I. Default lunar preset scores: **7, 6, 6**. None earns a lunar gravity-match point.
5. Every card lists its scoring components, experiment conditions and evidence limits. Filtering displays a result-change explanation. No-match cases are explicit, with a reset action. A missing lunar dataset does not imply safety.

The rank is research relevance, not fire risk, certainty, severity, experimental quality or probability. No score enters the mission-screening engine. Filtering changes the answer by changing the evidence set; it does not claim to simulate new measurements.

The comparison supports two investigations, with source links and separate rows for reported measurements, published qualitative descriptions and AstroFlare interpretation. A third selection is refused with a status message. Controls have labels, focus is restored after updates, and tables are keyboard-focusable scroll regions. Responsive layouts stack cards and filters on mobile; horizontal table scrolling preserves the side-by-side comparison.

## Evidence questions and AI behavior

**There is no generative research AI integration configured.** The existing remote `/api/ask` endpoint only accepts its own mission-assessment context; it cannot ingest the curated PSI evidence. Reusing it to explain these records would misrepresent its grounding.

The working alternative resolves a named investigation and requested measurement before relevance ranking. Saffire II / Saffire 2 / PSI-99 map only to PSI-99; Saffire I / Saffire 1 / PSI-98 map only to PSI-98. Named lookups use the curated catalogue independently of dashboard filters; general questions use filtered records. Flame-spread rate, burn time, airflow, oxygen and CO are separate quantities. The direct answer is the first line, followed by conditions, original table link, filename and row ID. Missing selected-table measurements and direct lunar-gravity measurements are explicit gaps. Three clickable examples demonstrate a successful Saffire II lookup, a lunar evidence gap and a Saffire I missing measurement. No model is active. Unsupported questions, safety certification, predictions, battery/health questions and unmeasured numeric/lunar rates return an evidence-gap message. It remains functional when the AI/status API fails. Ranking never depends on a model. The secondary mission workflow retains its original AI integration code but an explicit false activation gate prevents it from running during judging. Deterministic investigation tools remain usable.

## What changed for the judging criteria

- **Impact:** puts source-backed material/ventilation research and transfer limits into a short review workflow.
- **Creativity:** makes missing evidence and source inconsistencies visible, rather than turning them into unsupported risk numbers.
- **Validity:** original PSI tables, pinned raw bytes, checksums, reproducible scoring, explicit units and evidence types.
- **Relevance:** the primary path is the Flame in Freefall lunar-habitat research question; mission screening is secondary.
- **Presentation:** one-click public demo, ranked explanation, working filters, ready comparison, readable mobile layout and a short recording path.

## Run, tests and deployment

Node.js 22+ and Python 3; no runtime npm dependencies. `jsdom` is a development-only dependency for DOM interaction checks.

```sh
npm ci
npm run build
npm test
npm start
```

`PORT` is honored; default 3000. `GET /healthz` documents the original remote-engine dependency. Optional live screening regression: `NODE_USE_ENV_PROXY=1 node test/live-check.mjs` in the managed environment; omit that environment flag on hosts without a proxy. `/verification` records results and limitations.

Build embeds the interface, dataset, documentation, pinned CSVs and `/source.zip` in `dist/server/index.js`, a Cloudflare Worker. `server.mjs` adapts the same handler for Render. The source ZIP excludes site identity and credentials and rebuilds using `python3 build.py` after extraction.

### Exact Render steps for this copy, branch main

The existing Sites project is deployed in place. A Render deployment is optional and separate from it:
1. Download `/source.zip`, unzip it, create a repository you control on branch **main** (`git init -b main`, add/commit, add your remote, push main).
2. Render → New → Web Service → connect that repository. Set **branch main**, root directory to the repository root and runtime **Node**.
3. Build command **`python3 build.py`**; start command **`node server.mjs`**; `NODE_VERSION=22`; health-check path **`/healthz`**. Render supplies `PORT`. No NASA key, AI key or database is required. The checked-in `render.yaml` declares these settings for the copy.
4. Deploy. Verify homepage → lunar demo → 20 cm/s filter → comparison → NASA source in a signed-out window. For later revisions, push main and use **Manual Deploy → Deploy latest commit**, or enable auto-deploy on main. Rollback: Events → prior successful deployment → Rollback.

No changes were made to the separate original Render service. Its original repository/configured branch remain unavailable. Numerical screening still calls that original engine through a fixed-route relay. Cookies/authorization are not forwarded; requests have size/method/route checks and a timeout. Fresh screening data goes to the original service; browser saves remain local. Research does not send its question to that engine.

## Research-decision and instrument-layout upgrade

The lunar demo now ends in **What should we test next?**, beside the top result on desktop and directly after it in the single-column mobile layout. Default evidence is Saffire II row 2-5: 2.1 mm/s, SIBAL fabric, microgravity, concurrent 20 cm/s flow and approximately 22.1% O₂ (derived per source Note 1). The panel separates this observation from the missing lunar/habitat validation and an **AstroFlare proposed analysis**, not a NASA recommendation or a completed experiment. The proposed independent variable is gravity; material, airflow, atmosphere, geometry and ignition must be held fixed, and missing pressure/temperature plus the thickness ambiguity must be resolved before a credible protocol. The copy action includes these qualifications and the original NASA citations. If clipboard access is denied, a selected read-only brief appears for manual copying.

Material filtering now projects material-matched rows into cards and comparisons. Silicone uses PSI-99 row 2-1 (approximately 21.5% O₂, 20 cm/s concurrent flow), whose burn outcome is qualitatively “Insignificant”. There is no selected numeric silicone flame-spread rate, and no zero is invented. PMMA coverage without a matching selected run is labelled missing, rather than borrowing SIBAL measurements. An empty filter result produces an evidence-gap decision panel with no invented baseline.

All evidence submission paths—mouse, Enter and three example buttons—call the same latest-request-wins coordinator. Submitting immediately clears the previous answer, shows status and the latest submitted question, and snapshots the current retrieved records. Late responses from older/cancelled requests are ignored. Filter/scenario changes invalidate pending answers. Input drafts are separate from submitted questions, and answer updates replace only the answer panel while preserving focus, selection and scroll position.

The current visual system is a combustion research journal: flat warm ivory, near-black ink, muted brick-red primary actions and restrained blue source links. Instrument Serif supplies the headline and Instrument Sans the interface; locally hosted files and SIL Open Font Licenses are bundled. An original schematic plate replaces the former orb and gradients. Ranked evidence and the research decision lead the workspace; comparison follows immediately. Detailed run notes and interpretation/limitations expand separately. Brief entrance, ranked-order movement and answer-arrival animations never hide results; reduced-motion settings suppress both CSS and JavaScript motion. Responsive rules stack the hero and decision panel and retain focusable horizontal comparison scrolling. Real-browser visual verification remains an explicit environment limitation.

### AI status — deferred for judging

**AI remains inactive pending the API key.** Research lookup runs entirely as deterministic cited retrieval; no provider is activated, no key is added and no model answer is simulated. Existing optional mission-screening AI integration code is retained. Research AI activation is out of scope for this release and would require a future supported server-side integration, not just a UI label change.

### Updated 30-second judging recording

1. 0–5 s: open the public URL and click **Run the lunar habitat demo**.
2. 5–12 s: show **What NASA measured**, the lunar/habitat evidence gap and **Next research step** alongside the top-ranked evidence.
3. 12–19 s: choose **Material / fuel → Silicone**. Show the row 2-1 qualitative result and the changed research takeaway, rather than 2.1 mm/s.
4. 19–25 s: click **Copy research brief + citations**, then **View comparison** to show the material-matched outcome and NASA source together.
5. 25–30 s: open **Original NASA table · PSI-99 · row 2-1** from the decision panel (or its original table link in the comparison).

## Judging reliability release — 14 November 2026

The pre-release public deployment reproduced two defects: after Airflow → 20 cm/s → Material → Silicone, the status said “1 of 3” but named only Saffire I as removed, omitting the already-excluded BASS-II. Also, submitting a blank question retained the previous answer. Rapid valid submissions already used the latest-only coordinator; this release extends regression coverage and makes blank submissions cancel pending work and remove the previous answer immediately.

Filter feedback is now derived from the complete current result set, with included/excluded counts and names, top result and current comparison selection count. Every filter option and representative combinations are exercised. Reset experiment filters clears only filters; Restore lunar preset also restores the question, lunar scenario and default comparison pair. Scenario gravity remains separate from the hard experiment-gravity filter. Named material questions cannot retrieve another material's spread rate.

Research state is saved in same-origin browser history so Back/Forward and refresh remain usable. Research inputs are not sent to the screening engine; mission inputs are not put in URLs. Clipboard rejection exposes a selected read-only brief with an explicit failure message. Remote report failure keeps a retry, results and lunar-demo recovery path. Dark-theme overrides fix inherited light panels and low-contrast chips; narrow layouts contain tables and long text. No visual redesign or ranking-rule change was introduced.

The audit also found that the published relay returned HTTP 502 while direct Render requests succeeded. The relay now uses a portable AbortController timer and manual redirect rejection instead of runtime-dependent AbortSignal.timeout/redirect:error behavior. Route, method, body-size, credential stripping and unchanged assessment payloads are preserved. A safe route/error diagnostic records failures without inputs or credentials.

Validation commands (Node 22+, Python 3):

```sh
python3 build.py
npm test
python3 test/source-audit.py
NODE_USE_ENV_PROXY=1 node test/live-check.mjs
NODE_USE_ENV_PROXY=1 node test/judge-live.mjs
NODE_USE_ENV_PROXY=1 node test/mission-live.mjs
```

The proxy environment flag is needed only in this managed environment. `judge-live.mjs` fetches the exact public homepage anonymously, executes the full judge matrix in fresh JSDOM sessions configured at 1280 and 390 px, verifies links/downloads and original CSV hashes, and reports cold delivery and click-to-takeaway times. These are programmatic timing measurements, not a human or rendered-browser stopwatch. `mission-live.mjs` uses visible form controls and the real published relay, explicitly suppresses AI status, and inspects real report download payloads. `/verification` records boundaries and acceptance steps.

No callable browser-control tool is available in this managed environment. The Sites skill explicitly prohibits a substitute browser-control path. Real signed-out desktop/mobile visual inspection, page overflow, native clipboard/print dialogs, touch behavior and OS reduced-motion appearance therefore remain blocked. Programmatic DOM/keyboard/history checks and a declared-color contrast audit do not replace that final manual review.

## Combustion research journal and scientific audit — 14 November 2026

The homepage is an editorial split layout, with headline and lunar demo action before the experiment plate in document order. At widths up to 740 px it stacks; at 390 px the headline and button precede the plate. The plate is original SVG geometry, not NASA experimental imagery. It includes only a specimen, airflow and (for the SIBAL result) concurrent spread direction. It is labelled **Test schematic · not to scale**. There are no inferred apparatus dimensions, flames, ignition hardware, halos or gradients. SIBAL fabric / Silicone controls atomically switch the material, run, observation and citation; there is no looping animation. A brief switch transition respects reduced motion. All primary colors are flat, and checked text pairs exceed 4.5:1 (lowest tested 6.03:1); this is not a full rendered-page accessibility audit.

### Scientific corrections

1. **Fault current integral (I²t).** A frontend response adapter corrects the inaccurate energy label in the bootstrap schema, hypothetical demo, dynamic assessment text, report preview, Markdown download and JSON report download. I²t has units A²·s and is not energy in joules. The example remains exactly 112.5 A²·s. Numbers, units, formulas, engine IDs and calculations are unchanged. **Boundary:** the separate original Render engine, the unchanged same-origin API relay payload, and raw archived source/fixture responses retain their original wording. We do not control that service's repository; no upstream fix is claimed. Site-rendered results and report downloads apply the correction.
2. **Study versus run match.** Silicone + Opposed-flow investigation was reproduced on the prior public deployment: PSI-99 matched but the displayed row 2-1 was concurrent. Cards and comparison now label study-level coverage separately from curated run matches. No curated row matches silicone plus opposed flow. The copied brief preserves that gap, the displayed concurrent conditions, and a proposed evidence-retrieval step before selecting a baseline. This is a gap in the eight curated rows, not a claim that NASA never tested opposed-flow silicone (the full original table includes additional uncurated rows).
3. **Why this supporting study?** The default decision explicitly explains that BASS-II ranks first for the broad question while Saffire II supplies the measured spread rate for the proposed follow-up. This sentence updates with the top study and supporting evidence; empty results have no baseline.
4. **Saffire I companion results.** The selected PSI-98 CSV still has no spread-rate column. A separate NASA source is now cited: *Results of Large-Scale Spacecraft Flammability Tests*, NTRS 20170008805, Table I on **PDF page 29** and the average-rate discussion on slide 21. Sample **1-1: 1.8 mm/s, concurrent, 20 cm/s, O₂ 21.7 to 21.5%**; sample **1-2: 1.3 mm/s, opposed, 20 cm/s, O₂ approximately 21.5%**. Both are cotton/fiberglass (SIBAL), microgravity. The presentation's sample identifiers remain separate from PSI's S1/S2 labels. The missing PSI fields are not overwritten. `dataset.json` includes a separately named companion source, conditions, row identifiers and PDF hash. The legacy `measurements.csv` now corrects sample 1-2's initial oxygen to approximately 21.5%, per Table I; the original PDF/text is unchanged.

Original companion source: https://ntrs.nasa.gov/citations/20170008805
Direct table: https://ntrs.nasa.gov/api/citations/20170008805/downloads/20170008805.pdf#page=29

The plate cites **PSI-99**, not the NTRS companion, for its two rows. PSI row 2-1 gives O₂ approximately 21.5%; NTRS Table I gives approximately 22.1% for the same sample. These sources disagree. The plate retains the explicitly cited PSI value; neither source is silently reconciled. The existing thickness, geometry and spread-column-label discrepancies also remain documented.

**AI remains inactive pending the API key.** `AI_ENABLED=false` prevents automatic mission interpretation refinement and generated explanations, even when the separate service advertises availability. Free-text mission questions route only to supported deterministic investigation actions or an explicit inactive-mode message. Existing integration functions remain in source for a future separately authorized activation. No API key was added and no AI request was made in verification.

### Journal-release verification

27 Node regression tests cover the existing workflows plus both plate states at DOM widths 1280/390, focus retention/reduced motion, study/run gaps and copied briefs, dynamic supporting-study explanations, separate Saffire I citations, exact numeric preservation in terminology correction, and the inactive AI gate. `test/source-audit.py` checks all eight raw PSI rows and Table I's sample IDs, directions and rates. `test/judge-live.mjs` repeats the journal and core workflows anonymously on deployed bytes and checks local font delivery. `test/mission-live.mjs` asserts corrected terminology and unchanged 112.5 A²·s in real Markdown/JSON exports. Browser-control tooling remains unavailable; DOM widths are not rendered desktop/mobile viewports.
