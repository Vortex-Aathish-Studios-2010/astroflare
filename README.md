# Astroflare — copied interface with NASA combustion research

## What was recovered, and what was preserved

This project is a copy of the HTML interface served by https://astroflare.onrender.com/ on 14 November 2026, with focused improvements. Its original styling, guided input forms, review step, results, investigations, saved sessions and report interactions are retained. Original HTML is in `sources/original-interface.html`.

**This is not the original repository or a recovered assessment engine.** No original backend code, original test suite, Render blueprint, environment secrets, or configured deployment branch was available. No changes were made to the original Render service. Fresh assessment requests are relayed to that service's existing public API; the numerical engine is not reimplemented. NASA research relevance never enters those requests or modifies their scores.

The application discloses the remote-engine dependency in its footer. Normal assessments require the original service to remain available. It may cold-start, rate-limit or change its API. All entered assessment data sent through the copy is forwarded to that service; authentication cookies and authorization headers are not forwarded. Browser save/load remains local to the visitor's browser.

## Changes

- One click opens populated hypothetical results immediately, using an actual original-engine response bundled in `demo.json`. It is explicitly labelled hypothetical, captured on 14 November 2026, engine version 2026.10.21-2. All example inputs are marked working assumptions. These are not NASA observations or real mission data. Editing and rerunning invokes the original remote engine.
- A NASA combustion research explorer compares three curated, full-text-reviewed source records. Users enter a question, see explained keyword-topic matches, and compare up to two experiments. No-match questions are explicit. Ranking counts each matched topic once; ties keep catalogue order. It is neither a risk score nor a quality score.
- A useful chart shows three reported average SIBAL flame-spread measurements, with a downloadable CSV, units, conditions, source file and location. No measurements were invented or digitized from plots.
- The results overview omits the unsupported “Most consequential unresolved issue” paragraph. Presentation and prepared report text use “One condition to review (not ranked)” when that upstream wording appears. No numerical results are changed.
- Unanswered input fields have their own count and labels, separate from scientific evidence limits. The evidence note describes the scope of this library, rather than claiming that all science leaves these questions unanswered.
- Investigations/what-if controls are collapsed by default; primary actions and findings remain visible. Solar activity is outside the main workspace, in an optional footer appendix, fetched only when opened.
- Bootstrap schema and demo are bundled, so a remote cold start cannot block the demo or research explorer.

## NASA sources and data provenance

Verified against NASA NTRS metadata and original full text on 14 November 2026. The verification means the records and the cited statements were checked, not that NASA endorses this application. Original source metadata is retained under `sources/`.

1. **Results of Large-Scale Spacecraft Flammability Tests**, NTRS **20170008805**. https://ntrs.nasa.gov/citations/20170008805 . Source file **20170008805.pdf**: https://ntrs.nasa.gov/api/citations/20170008805/downloads/20170008805.pdf . Chart values are in slide 21 (“SIBAL Fabric Results (con't)”) and Table I. Slide 20 identifies the compared fabric and airflow. The original NASA text export is retained as `sources/20170008805.txt`.
2. **Effect Of Low External Flow On Flame Spreading Over ETFE Insulated Wire Under Microgravity**, NTRS **20040053553**, NASA/CP—2003-212376/REV1, pp. 177–181. https://ntrs.nasa.gov/citations/20040053553 . File **20040053553.pdf**: https://ntrs.nasa.gov/api/citations/20040053553/downloads/20040053553.pdf . Experimental section p. 178 supports facility, wire dimensions, diluents and flow range. This is NASA-hosted international partner research, not a NASA ISS experiment. No measurement series is extracted here.
3. **Preliminary Results from the Saffire VI Experiment**, **ICES-2024-365**, NTRS **20240002981**. https://ntrs.nasa.gov/citations/20240002981 . File **Saffire-ICES-2024-ICES-365-accepted final.pdf**: https://ntrs.nasa.gov/api/citations/20240002981/downloads/Saffire-ICES-2024-ICES-365-accepted%20final.pdf . Abstract, experimental section and Table 1 support the catalogue summary. Preliminary results cover selected tests, not the complete mission dataset.

### Chart transcription

| Test | Average flame spread (mm/s) | Flow (cm/s) | Initial O₂ (%) | Width (cm) | Direction |
|---|---:|---:|---:|---:|---|
| Saffire I, 1-1 | 1.8 | 20 | 21.7 | 40.6 | Concurrent |
| Saffire I, 1-2 | 1.3 | 20 | 21.7 | 40.6 | Opposed |
| Saffire II, 2-5 | 2.1 | 20 | 22.1 | 5 | Concurrent |

SIBAL cotton/fiberglass fabric, orbital microgravity. Reported oxygen values are initial ISS readings, not an independently calibrated atmosphere reconstruction. Samples differ in geometry and oxygen fraction, so these bars cannot isolate a causal width effect. Total pressure and uncertainty for the spread-rate averages are not specified in the cited excerpt; neither was invented. See the CSV for specimen length/thickness. Chart bars begin at zero; rates are averages, not time-series measurements. No general ignition threshold or fire probability follows from this chart.

## Run and verify

Requirements: Node.js 22 or later and Python 3. No runtime npm packages are needed.

```sh
npm ci
npm run build
npm test
npm start
```

`PORT` is honored (default 3000). `GET /healthz` reports the remote-engine dependency. Optional live API regression check: `node test/live-check.mjs` (in proxy-managed environments, use `NODE_USE_ENV_PROXY=1 node test/live-check.mjs`). Build embeds the public files and documentation in `dist/server/index.js`, an ESM Cloudflare Worker; `server.mjs` adapts the same handler for Render.

The original repository's tests cannot be run because they were never provided. See `/verification` for exact checks and limitations. DOM checks are not browser visual checks. No claim of completed desktop/mobile visual QA is made without a browser runner.

## Exact Render steps for this copy

The **copy's branch is `main`**. This is not a claim about the existing service's unknown configured branch.

1. Download `/source.zip` from the published copy, unzip it, and create a GitHub/GitLab repository you control with branch `main` (for example, `git init -b main`, add/commit the files, add your remote, and push main). Do not overwrite the original service or its environment configuration without the original repository.
2. In Render, choose **New → Web Service**, connect that repository, choose branch **main**, and set the root directory to the repository root.
3. Select the **Node** runtime, set build command **`python3 build.py`** and start command **`node server.mjs`**. No npm installation is needed for production: there are no runtime dependencies. Render's build environment must provide Python 3 and Node 22+. The `engines` field declares Node >=22.
4. Set the health-check path to **`/healthz`**. Render supplies `PORT`; do not hardcode it. No NASA key, AI key or database is required for this copy. Optional upstream AI features depend on the original service's configuration.
5. Create the service and wait for the health check to pass. Use Render's assigned URL. Open the demo, enter a research question, compare two records, download the CSV, edit a demo answer and run a fresh assessment, then prepare a report.
6. For later revisions: push the tested source to **main**, then **Manual Deploy → Deploy latest commit** (or enable auto-deploy for main). Roll back using **Events → select a previous successful deployment → Rollback** if needed.

For the **existing** astroflare.onrender.com service, exact deployment instructions remain blocked until its repository and Settings → Build & Deploy → Branch are known. Its configuration was not inspected or changed. Integrating this frontend into that repository should use its existing same-origin API and deployment commands, rather than replacing its engine with this relay.

## Limitations

- New copy, not a backend clone. Original engine availability and contract changes are external dependencies.
- Three curated records, no exhaustive search, no semantic/AI research ranking, no assurance of complete literature coverage.
- Public NASA data was accessible. Only reported summary averages were extracted; no raw instrument time-series dataset is claimed.
- No independent fire-risk validation, no severity/probability estimates, no NASA endorsement.
- The original service still owns its raw backend wording; replacement here is presentation-only, including locally prepared report exports.
- Sources are pinned for reproducibility and require periodic human review.
