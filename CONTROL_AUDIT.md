# AstroFlare control inventory and reliability audit

Scope: existing Sites project, branch main, current public URL. Inventoried before this release's changes by reviewing every event listener, generated control and navigation target in the source. Repeated controls are listed as families with their generating IDs. NASA IDs, run values and ranking formulas are outside the visual redesign.

## Intended behavior inventory

| Control or family | Intended behavior | Verification scope |
| --- | --- | --- |
| Skip to content, Home, NASA research, Mission screening, Lunar habitat demo | Navigate and focus the correct heading; browser Back/Forward remains usable | DOM routes/history; real browser blocked |
| Run the lunar habitat demo; Restore lunar preset | Restore lunar question, all filters, two default selections and cited takeaway | Local and published DOM |
| Explore my own question | Open research editor and focus its question | Regression added |
| SIBAL fabric / Silicone plate buttons | Switch specimen, run, observation and source together; selected state and focus retained | Local and published DOM |
| Edit research question disclosure; question textarea; Update ranked evidence | Preserve draft while editing; validate blank input; submit and update deterministic relevance | Regression added |
| Material / fuel, Experiment gravity, Airflow evidence | Include/exclude studies, explain all included/excluded studies; retain only visible comparison selections | All options and representative combinations |
| Scenario gravity | Change transfer interpretation separately from experiment-gravity filtering | All options |
| Reset experiment filters | Reset hard filters without silently resetting the user's research question | DOM |
| View comparison / Ask about the evidence shortcuts | Move focus to the relevant section without breaking route history | DOM |
| Compare checkbox for every ranked investigation | Select/remove a study; reject a third; announce current count | 0, 1, 2, attempted 3 and filtered-out selection |
| Remove study controls in comparison | Remove that study and update columns/count/checkboxes together | Regression added |
| Conditions; row notes; other investigations; comparison notes | Native keyboard-operable disclosures; maintain open state on updates | DOM semantics/state; native visual animation blocked |
| Measurement chart; methodology; fixed proposal conditions | Expand real measurements and their limitations, formulas, sources and proposed inputs | DOM; source audit |
| Evidence input; Find cited answer; Enter; three examples | One latest-submission workflow; clear stale answers; supported, unsupported, blank and missing evidence cases | Rapid submissions and cancellation |
| Copy research brief + citations | Copy current scenario/measurement or gap/proposal/citations; show real success or manual fallback | Clipboard adapter and denied fallback; native clipboard blocked |
| NASA PSI links; original CSV; pinned source CSV | Open the correct record/file without authentication; preserve row labels and units | Anonymous HTTP and hashes |
| NTRS presentation and record links | Open page 29/Table I and the corresponding NASA record | Anonymous HTTP and PDF hash |
| Dataset JSON, measurements CSV, source ZIP, documentation, verification | Deliver valid, current files; source archive rebuilds the release | Anonymous downloads and rebuild |
| Mission description; example descriptions; Read my description | Parse deterministically; show proposed extracted fields; no AI without activation | Fixtures plus available remote service |
| Skip description; hazard radios; objective radios; optional question; Continue / Back | Validate required hazard and move between mission/problem stages | DOM validation/navigation |
| Extracted candidate checkboxes, ambiguous-hazard radios, Use ticked items | Confirm only selected candidates; preserve their basis/source | Deterministic fixture response |
| Mission field inputs/selects c_*; pressure unit; unknown u_*; basis b_* | Edit values/units; unknown disables corresponding controls; numeric validation comes from original engine | Generated fields listed below; fixture/live boundary explicit |
| Info Back / Continue; profile review; context Edit; Answer it; stepper | Save current fields, show errors, preserve answers, navigate only when prerequisites exist | Regression and available service |
| Profile acknowledgement; Run the assessment | Require acknowledgement, show genuine pending state, preserve answers on failure | Success fixture and network/429 failure |
| Results Edit answers; Pin as baseline; next assessment comparison | Preserve baseline inputs; compare with fresh submitted inputs | Fixture contract and response rendering |
| Finding disclosures; Show reasoning; Show calculation; Open source | Invoke original deterministic investigation action with the correct ID | Action contracts and source rendering |
| Six investigation tools: influence, missing, verify, calc, evidence, index | Use original service; render returned data or real error | Fixture controls and live availability |
| What-if field/value selects; Compare | Send selected field/new value; display returned comparison | Fixture contract |
| Assessment Ask / Enter | Route recognized topics to deterministic tools; unsupported prompts explain inactive AI | No generated requests |
| Generate explanation (disabled) | Stay disabled while AI is inactive; integration code remains available for future authorized configuration | Adversarial available-status fixture |
| Verify source records | Show actual pending/result/error and re-enable control | Fixture success/failure |
| Prepare report; Retry report; Back to results; Open NASA lunar demo | Generate only actual service reports; preserve error/recovery; ignore obsolete completions | Fixture exports, live service status |
| Markdown / JSON report downloads; Print | Export actual displayed data with corrected I²t label; invoke print | Blob contents / print callback; native dialogs blocked |
| Save / Load / Start over | Save current draft inputs locally, validate loaded state, cancel obsolete tasks; confirm clearing current answers | Storage success/denial/corruption and reset |
| Solar appendix / Retry / record links | Load only when opened, report real availability, provide retry | Fixture success/failure; live availability |

## Initial observed defects and changes to verify

- Custom-question action opened a closed editor containing the preset, without focusing it.
- Blank research-question submissions replaced the current question instead of explaining the missing input.
- Save missed current textarea/field drafts until a navigation/submit action collected them.
- Back from an information group had an uncaught network-rejection path.
- Mission interpretation/flow/assessment/report callbacks could update a departed page or navigate after a newer action.
- Some disclosures had no stable identity and collapsed during comparison/filter updates.
- Comparison removal required returning to a study card; add explicit removal controls beside the visible comparison.
- Detached report preparation did not consistently register its navigation state.
- Browser downloads immediately revoked their object URL; retain it briefly for browser handoff.

## Environment and external boundaries

The site is public. Production runtime contains no credentials. AI stays inactive. The managed environment advertises an on-demand desktop but exposes no browser/desktop JavaScript tool. The Sites skill forbids installing a browser or using a substitute control path in that state. Real-browser desktop/tablet/mobile visual and native keyboard/clipboard/print checks remain blocked; DOM checks are not described as rendered-browser tests.

The original assessment engine is a separate Render service. Do not substitute invented or cached answers for a failed fresh request. Local tests use explicitly named fixtures to verify UI behavior, never to serve users a fake successful assessment.

## Generated mission input controls
- `question`: Research question (optional) — text; preserve the schema’s units, options and validation.
- `hazard`: Hazard under investigation — select; preserve the schema’s units, options and validation.
- `habitat`: Habitat or vehicle — select; preserve the schema’s units, options and validation.
- `phase`: Mission phase — select; preserve the schema’s units, options and validation.
- `gravity`: Gravity — select; preserve the schema’s units, options and validation.
- `o2_percent`: Oxygen fraction — number; preserve the schema’s units, options and validation.
- `pressure`: Total cabin pressure — number; preserve the schema’s units, options and validation.
- `pressure_unit`: Pressure unit — select; preserve the schema’s units, options and validation.
- `volume_m3`: Volume of the affected compartment — number; preserve the schema’s units, options and validation.
- `vent_flow_m3_min`: Ventilation flow through the compartment — number; preserve the schema’s units, options and validation.
- `vent_control`: Ability to stop ventilation to the affected compartment — select; preserve the schema’s units, options and validation.
- `duration_days`: Mission duration — number; preserve the schema’s units, options and validation.
- `crew`: Crew size — number; preserve the schema’s units, options and validation.
- `abort`: Return or safe-haven options — select; preserve the schema’s units, options and validation.
- `comm_delay_min`: One-way communication delay to ground — number; preserve the schema’s units, options and validation.
- `equip_type`: Equipment type — select; preserve the schema’s units, options and validation.
- `voltage_v`: Operating voltage — number; preserve the schema’s units, options and validation.
- `op_current_a`: Operating current — number; preserve the schema’s units, options and validation.
- `fault_current_a`: Prospective fault current — number; preserve the schema’s units, options and validation.
- `clearing_ms`: Fault clearing time of the protective device — number; preserve the schema’s units, options and validation.
- `fault_protection`: Fault protection — select; preserve the schema’s units, options and validation.
- `power_isolation`: Procedure to remove power from the affected equipment — select; preserve the schema’s units, options and validation.
- `redundancy`: Redundancy and emergency power — select; preserve the schema’s units, options and validation.
- `inspection`: Inspection and maintenance history — select; preserve the schema’s units, options and validation.
- `detection_coverage`: Fire detection coverage — select; preserve the schema’s units, options and validation.
- `detection_signals`: Fire signatures detected — select; preserve the schema’s units, options and validation.
- `suppression`: Fire suppression provisions — select; preserve the schema’s units, options and validation.
- `ppe`: Crew breathing protection — select; preserve the schema’s units, options and validation.
- `drills`: Crew fire-response practice — select; preserve the schema’s units, options and validation.
- `postfire`: Post-fire monitoring and clean-up — select; preserve the schema’s units, options and validation.
- `materials`: Material flammability evidence — select; preserve the schema’s units, options and validation.
- `ignition_other`: Other ignition sources considered — select; preserve the schema’s units, options and validation.
- `battery`: Stored energy (batteries) — select; preserve the schema’s units, options and validation.

## Current implementation and local verification

The inventory's intended actions now have handlers and targeted regression coverage. Added explicit comparison removal, custom-question focus/validation, unsent question persistence across filters, saved mission draft collection, malformed-storage rejection, and task cancellation across navigation. An additional audit found the Report step could display an endless preparation message without starting a request; it now invokes report generation. Back from a question group commits its destination only after the flow request succeeds, so a failed request preserves the visible fields and a retry remains usable. Profile failures re-enable Continue. Restored unknown pressure correctly disables the unit control.

Local regressions exercise all investigation action bindings, finding/calculation/source IDs, what-if values, source-check failure/retry, baseline comparison and report-step preparation using explicit UI fixtures. The mathematical engine is unchanged; these tests verify client behavior, not fresh service availability. Declared theme contrast pairs pass at a minimum of 6.49:1. Motion fail-open and reduced-motion behavior pass programmatically. No newer logo asset was found.

The owner has created https://github.com/Vortex-Aathish-Studios-2010/astroflare as a public repository. Its initial commit is preserved and the project includes a CI workflow; the earlier automatic repository-creation permission blocker no longer prevents source upload.

Published acceptance passed on the midnight application: anonymous research/science DOM checks at 1280/390 and reliability checks at 1280/768/390. Source links and downloads passed. Fresh mission flow returned HTTP 429 from the original remote service; no fresh report success is claimed. All 34 local tests passed; raw results and exact conditions are in `/release-checks.json`. Browser visual/native checks remain blocked as described above.
