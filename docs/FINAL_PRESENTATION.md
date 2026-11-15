# AstroFlare: everything you need before presenting

Live site: https://astroflare.onrender.com
Challenge: NASA Space Apps 2026, *Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data*

---

## 1. What AstroFlare is, in one breath

> AstroFlare turns NASA's microgravity combustion data into a cited research brief. A researcher asks a question, AstroFlare finds and ranks the relevant NASA experiments, shows the measurements with their exact test conditions, and says what to test next. Every value links back to the original NASA table.

**The problem it answers (from the challenge):** NASA has decades of flame and fire data from the ISS and other platforms. It is public in the PSI database, but it is hard to find, hard to compare and hard to interpret. Fire is one of the most dangerous events on a spacecraft, and the Moon base and Mars missions will use higher-oxygen atmospheres where materials burn more readily.

**What you built, mapped to the challenge's three objectives**

| Challenge objective | Where AstroFlare delivers it |
|---|---|
| Identify investigations most relevant to crew habitats (stations, lunar bases, rovers) | Lunar habitat demo and NASA research: ranked experiments with "why it ranked here" |
| Extract data that supports predictive modelling | Original conditions and values per run (material, oxygen, airflow, gravity), source row IDs, downloadable dataset and original CSVs, JSON export |
| Highlight research that informs next-generation fire-safety controls | "What should we test next?" panel, research brief, comparison, saved projects |

**Who it is for (the challenge names these):** professors, graduate and undergraduate students, aerospace researchers and engineers. Your first target users are university combustion and materials-science labs.

---

## 2. The concepts you must be able to explain

Say these in plain words. Do not read them out; just know them.

- **Microgravity.** Free fall. With no buoyancy, hot gas does not rise, so a candle flame becomes a small, round, blue, dim sphere that gets its oxygen by diffusion instead of a rising teardrop. That is the photo on the homepage (NASA Glenn).
- **Why it matters for fire safety.** Flammability depends on oxygen concentration and airflow, and spacecraft fire-safety work rests on prevention (material selection, ignition control), detection and suppression. Designs were largely based on normal-gravity understanding.
- **Flame spread rate (mm/s).** How fast a flame travels across a solid sample. It is a *measurement for specific conditions*, never a universal number.
- **Concurrent vs opposed flow.** Air flowing in the same direction the flame spreads (concurrent) or against it (opposed). It changes the spread rate.
- **SIBAL.** A cotton-fiberglass fabric used as a standard test material (Solid Inflammability Boundary at Low-speed).
- **PSI.** NASA's Physical Sciences Informatics repository, the source of the data.
- **The three investigations in AstroFlare**
  - **BASS-II (PSI-25):** Burning and Suppression of Solids, run in the Microgravity Science Glovebox on the ISS. AstroFlare shows its CO (carbon monoxide) readings for 2 cm SIBAL fabric runs: final CO 40, 78 and 72 ppm for runs T1, T2 and T4.
  - **Saffire I (PSI-98):** a large-scale spacecraft fire experiment. Spread rates come from NASA's NTRS report (1.8 mm/s concurrent, 1.3 mm/s opposed), which AstroFlare cites.
  - **Saffire II (PSI-99):** run on a Cygnus cargo vehicle after it left the ISS. Run 2-5, SIBAL fabric, 20 cm/s concurrent flow, about 22.1% oxygen: **2.1 mm/s**, burn time 145 s. Run 2-1, silicone: burn time described as **"Insignificant"** (NASA's qualitative description), at about 21.5% oxygen.
- **Dataset facts:** 3 investigations, 8 curated test rows, dataset version 2026-11-14.2, with source file hashes so a judge can check nothing was altered.
- **Research relevance.** The ranking says how well an experiment matches *your question*. It is not a measure of how safe or effective anything is. (Scoring: 2 points per recognised topic match, +1 for variable-flow coverage when airflow is asked about, +2 for a named material, +1 for an exact gravity match. Every card shows the points behind its rank.)
- **Lunar gravity.** PSI does not yet contain partial-gravity combustion data. NASA expects the LUCI and FM2 experiments to add it. That is exactly why AstroFlare labels microgravity results as the starting evidence and lists the next conditions to test.
- **Moon base atmosphere (from the challenge brief).** Expected to be 30% oxygen or more at 10.2 psi or less, compared with about 21% on Earth. Materials become more flammable, so tests at those levels matter.
- **The AI.** Optional. A cited answer always appears first. "Explain with AI" adds an AI-generated interpretation built only from the curated records, checked before display (numbers must come from the records, it must cite real record IDs, no unsupported claims), and it is labelled as AI-generated and kept separate from NASA's results. The API key lives on the server only.

---

## 3. The two tools (be able to say this in 15 seconds)

1. **Research explorer** (menu: *Lunar habitat demo*, *NASA research*). Runs in the browser on the NASA records bundled with the page. This is the main product and the one to demo.
2. **Mission screening** (menu). A questionnaire about your own mission or habitat. It lists conditions worth a closer look and what information to add, using the engine from the original AstroFlare project. Choose **Quick** (3 questions) or **Full** (20 to 29 questions in 5 to 7 groups). Its heuristic index is separate from research relevance.

---

## 4. Navigation map

Top menu: **Home** · **Lunar habitat demo** · **Mission screening** · **NASA research** · **For research labs** (plus Save / Load / Start over for mission screening). A one-line note under the menu explains the two tools. Browser Back and Forward work; direct links work (`/#lunar-demo`, `/#research`, `/#labs`, `/#mission`).

**Home**
- Navy hero with the NASA candle-flame photo (credited), "Recommended first step", the button **Run the lunar habitat demo**, and the quiet link "Explore my own question".
- Below: a preview card (a ranked experiment, a cited measurement, a transfer note), "Two tools, one site", "How it works" in 3 steps, the demo question, and a collapsed "Also available" section for mission screening.

**Lunar habitat demo** (the guided route, 3 steps)
1. **Choose a material:** SIBAL or Silicone.
2. **See NASA's observation:** the value, the test conditions (material, gravity, airflow, oxygen), and the source row with links to the NASA record and original CSV.
3. **See where it applies and what comes next:** microgravity, lunar gravity and Moon-atmosphere as the next tests.
Then buttons: *Ask a question about this evidence*, *Compare two experiments*, *Advanced filters and tables*.
Further down: filters (collapsed), ranked evidence (BASS-II first, then Saffire II and Saffire I), **What should we test next?** (What NASA measured / Next conditions to test / Next research step / **Copy research brief + citations**), comparison table, **Ask about the evidence**, **Research projects**, an optional CO-readings chart, and "Methodology, sources and scope".

**NASA research:** same tools without the walkthrough, for a free-form question (type your own question, narrow with filters, open sources, compare, ask).

**For research labs:** the business page (section 7).

---

## 5. The 5-minute demo script (exact clicks and words)

Open the site at least 5 minutes before you start (see section 8). Zoom 100%, full screen.

**0:00 Hook (30 s). Stay on Home.**
> "Fire is one of the biggest dangers for a crew, and flames behave very differently in microgravity. On the left you see a candle flame on Earth, on the right the same candle in microgravity. NASA has decades of experiments on this, but the data is hard to find, compare and interpret. AstroFlare turns it into a research brief with sources you can trace."

**0:30 Start the demo (20 s).** Click **Run the lunar habitat demo**.
> "Our recommended first step is a lunar habitat question: which NASA experiments can inform a fire review for a lunar habitat?"

**0:50 Step 1 and 2 (60 s).** SIBAL is selected.
> "SIBAL is a standard fabric. In Saffire II, run 2-5, NASA measured a flame spread rate of **2.1 millimetres per second**. Here are the exact conditions: microgravity, 20 centimetres per second of concurrent airflow, about 22 percent oxygen. And here is the source row with a link to the NASA table."
Click **Silicone**.
> "Now silicone, same experiment. NASA describes the burn as *Insignificant*. The page switches the value, the conditions and the source together, so you never see one material's number next to another's."
Click **Open NASA record** (or just point to the link) to show it is real.

**1:50 Step 3 (20 s).**
> "Both ran in microgravity. Lunar gravity is the natural next test, and the Moon's expected 30 percent oxygen atmosphere is another one. So the demo ends with what to test next, not just numbers."

**2:10 Ranking and takeaway (60 s).** Click **Advanced filters and tables** (or scroll).
> "Behind this is a ranking. BASS-II ranks first for this question, then Saffire II and Saffire I. Each card shows exactly which criteria earned its points."
Point to **What should we test next?**
> "This panel gives what NASA measured, the next conditions to test, and a next research step. One click copies it as a research brief with citations."
Click **Copy research brief + citations**.

**3:10 Ask and AI (45 s).** Scroll to **Ask about the evidence**. Click the example *What was the flame spread rate in Saffire II?*
> "Answers come from the records and always show their source. If I want an interpretation, I can ask the AI. It only uses these records, it is checked before it appears, and it is labelled as AI-generated."
Click **Explain with AI (optional)**. If it is slow, keep talking and come back to it.

**3:55 Return value (35 s).** Scroll to **Research projects**. Type "Lunar fabric review", click **Save project**, then **Markdown**.
> "Researchers can save, reopen and export a project, so they return to it. The export separates what NASA measured, the next conditions to test, and the proposed research. This is stored in the browser for now."

**4:30 Business (25 s).** Click **For research labs**.
> "Our first users are university combustion and materials labs. Exploration stays free. We plan a team workspace, shared projects, comments and version history, and we will pilot it with three labs."

**4:55 Close (5 s).**
> "AstroFlare turns decades of NASA fire data into traceable research for the Moon and Mars. Thank you."

**If you only get 2 minutes:** Hook, Run demo, SIBAL then Silicone, Copy brief, close.
**30-second elevator version:** "AstroFlare finds, ranks and explains NASA's microgravity fire experiments for a research question, with every number tied to its source and the conditions it was measured under, and it ends with what to test next for the Moon."

---

## 6. Prepared questions for the AI box

Use these in the **Ask about the evidence** panel.

| Ask | What you should see |
|---|---|
| What was the flame spread rate in Saffire II? | 2.1 mm/s for run 2-5 with its conditions and NASA source links |
| What was the flame spread rate in Saffire I? | The values from the cited NASA report (1.8 mm/s concurrent, 1.3 mm/s opposed) with links |
| What flame spread rate was measured in lunar gravity? | A statement that PSI does not yet include a lunar-gravity measurement and that LUCI and FM2 are expected to add one |
| Is silicone safe on the Moon? | A calm pointer: the records report measured behaviour under stated conditions; start from the original NASA sources |
| Who won the football match? | A pointer to the topics the records cover (material, airflow, oxygen, microgravity, combustion gases) |

Then click **Explain with AI** under the first answer; it can take up to a minute on the free plan.

---

## 7. Business story (the For research labs page)

Say it as a plan, not as results. Do not invent customers, revenue, partnerships or endorsements.

| Criterion | What to say |
|---|---|
| Customer | University combustion and materials-science researchers |
| Buyer | A lab director, principal investigator or university department |
| Problem | They must match published experiments to their conditions and document why the evidence supports their investigation |
| Value | A research question connected to relevant experiments, source conditions, next-step opportunities and a reusable research brief |
| Revenue | Public exploration free; paid collaboration, project history and maintained evidence collections |
| Validation | Pilot with three labs and ten observed review tasks; measure return use, brief accuracy and willingness to pay |

- **Offerings:** *Public Explorer*: free, available now. *Research Lab Workspace*: **Planned** (shared projects, reviewer comments, version history, reviewed additions to the evidence collection).
- **Pilot price on the page:** *Proposed pilot pricing: US$49 per lab/month. We will test this price with research teams before launching subscriptions.* Present it as a proposal.
- **Five things the pilot tests:** can researchers find the right evidence; can they separate measurements from next-step opportunities; how long a comparable review takes with and without AstroFlare; do they return to saved projects; would the lab's budget holder pay.
- **Do not say:** any revenue, user, savings, profit or market-size figure; any NASA endorsement.

---

## 8. Before you go on stage (setup checklist)

1. **Wake the site 5 to 10 minutes early.** The free hosting sleeps after inactivity, and the first load can take up to a minute. Open https://astroflare.onrender.com and click through the demo once. Reload it again just before you start.
2. **Use the device and browser you will present on.** Chrome or Edge, 100% zoom, full screen, notifications off, bookmarks bar hidden.
3. **Have the URL on a slide** so judges can open it.
4. **Test the internet at the venue.** If it is weak, use the backup plan below.
5. **Clear stale saved data** if you want a clean demo: browser settings, clear site data for astroflare.onrender.com.
6. **Pre-type the question** in your notes so you can paste it quickly.
7. **Keep this page open** on a second device or printed.

**Backup plan**
- **Screenshots or a screen recording:** record one run-through of the script before the event (Windows: Win+G or Win+Alt+R). Keep it on the desktop. Backup screenshots are not yet saved in the project; record your own recording or ask me to capture them once the final deploy is confirmed.
- **Run it locally** if the internet fails: open a terminal in the project folder and run `npm start`, then open http://localhost:3000. The research explorer, labs page and project save all work offline because the NASA data is bundled. (Mission screening and the AI need the engine and internet.)
- **If the AI is slow or unavailable:** say "The cited answer is the core; the AI interpretation is optional," and continue. The cited answer always works.
- **If a page loads slowly:** talk through the hook while it loads, then continue.

---

## 9. Likely judge questions and answers

State facts plainly. Do not over-claim and do not apologise.

1. **Is this validated with real users?** "We are at the pilot stage. Our targets are three labs and ten observed review tasks, measuring return use, brief accuracy and willingness to pay."
2. **Why only three investigations?** "We started with a curated, fully traceable set: every row has a source file hash and links to the original NASA table. The structure adds more PSI investigations the same way."
3. **Does it predict fire behaviour on the Moon?** "No. It organises and ranks what NASA measured, shows the conditions, and lists what to test next for lunar gravity and the Moon's atmosphere. PSI does not have partial-gravity data yet."
4. **What does the AI do, and can it make things up?** "It writes an interpretation only from the curated records. Before it is shown, numbers must come from the records, it must cite real record IDs, and unsupported claims are rejected. It is labelled AI-generated, kept separate from NASA's results, and the answer above it works without it."
5. **Is the ranking a safety score?** "No. It is research relevance to your question, with every point traceable. It does not say anything is safe."
6. **Where does the data come from?** "NASA's PSI repository and NASA's technical reports server. Each value links to its original table and record."
7. **How is 2.1 mm/s traceable?** "Saffire II, PSI-99, run 2-5. The page shows the row, the conditions and the NASA link, and an NTRS report corroborates the value."
8. **Why does silicone have no number?** "NASA's table describes the burn as Insignificant, a qualitative result. We show it exactly as NASA described it."
9. **What is the business model?** "Free public exploration. A paid lab workspace is planned, with shared projects, comments, version history and maintained evidence collections. The US$49 per lab per month price is a proposal we will test."
10. **Who are your users?** "University combustion and materials-science labs first, then aerospace engineers and students."
11. **What is the mission screening?** "A separate questionnaire tool for your own mission or habitat. Choose a quick path of 3 questions or a full path of 20 to 29. It lists conditions worth reviewing and what information to add."
12. **How do you handle API keys?** "They stay on the server. The browser never sees them."
13. **What is next?** "Add more PSI investigations, add partial-gravity data when LUCI and FM2 publish, and build the shared lab workspace."
14. **Do you work with NASA?** "AstroFlare is an independent project built on public NASA data." (Do not imply endorsement.)

---

## 10. Facts at a glance (memorise these)

- 3 NASA investigations, 8 curated test rows, dataset version 2026-11-14.2
- **2.1 mm/s**: Saffire II, run 2-5, SIBAL fabric, microgravity, 20 cm/s concurrent flow, about 22.1% oxygen, burn time 145 s
- Silicone run 2-1: burn time "Insignificant", about 21.5% oxygen
- Saffire I (from NASA's report): 1.8 mm/s concurrent, 1.3 mm/s opposed
- BASS-II final CO: 40, 78 and 72 ppm (T1, T2, T4)
- Ranking for the lunar question: BASS-II 7 points, Saffire II 6, Saffire I 6
- Quick screening: 3 questions. Full: 20 to 29 questions in 5 to 7 groups
- Pilot targets: 3 labs, 10 observed review tasks. Proposed price: US$49 per lab per month
- Photo: NASA Glenn Research Center, image GRC-1998-C-00485

---

## 11. Verification status (honest)

**Confirmed on the live site (build 7967508):** all pages and downloads load (home, documentation, verification, control audit, dataset, source zip, health check, measurements and the three source CSVs, photo, fonts); the live home page is byte-identical to the committed build; unknown pages return a clean 404; the quick mission path ran end to end on the live engine (review then results with 9 findings); quick is 3 questions and full is 29 in 7 groups; reloading on `#research` restores the right page; the AI explanation returned a checked answer citing run 2-5 (on an earlier build); no console errors seen.

**Confirmed in automated tests (not yet re-run on the live site):** 54 interface tests and 499 engine tests pass, covering navigation and back/forward, material switches, filters, empty results, comparison, evidence questions including irrelevant and unsupported ones, project save, reopen and export, the labs page, the quick/full choice, in-page link integrity, and the server's compression and caching. All 27 external NASA links return 200.

**In progress when this was written:** a performance fix (compressed, cached pages) was being deployed because the free hosting made the home page take anywhere from 2 to 25 seconds. After it is live, load time still depends on the free plan, which is why you should wake the site early.

**Not yet done:** the remaining live checks (filters, comparison and projects on the live site; layout at 390 and 768 px; text contrast), and backup screenshots saved into the project.
