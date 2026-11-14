# Verification

Original repository and original tests: unavailable. Original deployment branch: unknown. Existing Render service: unchanged.

Recorded results: 7 automated tests passed; live original-engine equality passed for electrical_transit, electrical_transit_complete, lunar_battery and mars_material. Live guide flow and profile calls passed.

Automated checks for this copy:
- JavaScript syntax checks for the generated Worker and inline interface.
- Worker tests for immutable upstream forwarding, methods, route allowlist, body-size limit and failure handling.
- DOM interaction tests for one-click immediate demo results without an assessment request, explorer ranking, comparison selection, assessment/research isolation, save/load and original guided interactions.
- Data checks for NASA source IDs, transcribed rates, and separate research ranking.
- Live original-API integration checks for guide/profile/assessment and remote response equality.

Browser QA limitation: the selected managed environment exposes no callable desktop/browser JavaScript tool (`cua_repl.js`). Per the Sites managed-preview instructions, a preview server or substitute browser-control path was not started. Desktop/mobile layout and touch interaction have not been visually verified. Existing responsive CSS is preserved and new controls use wrapping layouts, small-screen breakpoints and scrollable comparison tables; this is not a substitute for browser testing.

Manual acceptance checklist for a browser:
1. Desktop 1440 × 900 and mobile 390 × 844: demo opens results in one click with an obvious hypothetical banner.
2. Edit a demo answer, complete review and rerun; result reflects the new input and no longer shows a cached-demo banner.
3. Ask a wire/ventilation question: ETFE ranks first with explicit matched topics. Ask an unrelated question: no-match status appears.
4. Select any two experiments; a third is refused with a readable status. Uncheck one and replace it. Compare metadata and original-source links.
5. Inspect chart, units, source filename, conditions, zero baseline and CSV download.
6. Verify missing input fields and evidence limits are separately labelled; investigations are collapsed; solar activity is footer-only and fetches only after expansion.
7. Save/load a scenario, prepare/download a report, and confirm hypothesis labelling and wording.
