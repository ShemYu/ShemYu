# Interview log

These notes record my project clarifications and interview preparation. Dates identify when I added or clarified an account; missing details are listed where they would add useful context.

## Issue-recall metric clarification

The public result is issue recall 50% → 95%: domain experts annotated the issues in each video, and the metric is the share of all annotated issues the system recalls. The name "dish coverage" (taken from the `dish_covered` eval field and made the mandatory public name, with "never call it recall", in PR #29 on 2026-10-01) was a wording error; the owner clarified the definition on 2026-10-10. The 53/56 count is retained as internal context. The 15-case/103-unit
67.6 → 83.0 reading is retired from the story (`cookpad-vu-internal-coaching`,
status `do-not-claim`). Not on the Bible view.

## Synced from origin/main Cookpad evidence (PR #25)

Public one-pager bullets unchanged. Internal Cookpad claims now match
`data/work/cookpad.yaml` A–D plus `career_evidence/moment_coach_ai_git_history.md`:
Guideline Grounder 13/14 vs 2/14, ObservationAgent design/mentorship (PR #461),
video infra PRs, evaluation architecture, and the 33-PR ledger. PR #606 is not Shem.

## Confirmed 2026-08-27

- **FinOps is one workstream.** The DOGI-suite FinOps agent and the 30% GPU reduction are the same work. Public result stays [[cathay-finops-gpu]] / [[cathay-finops-cloud]]. [[cathay-dogi-finops-agent]] is assembly only (the cost result belongs to the same workstream).
- **Guideline grounder v2 did not ship.** This is historical internal design work. Its relationship to v5 is influence rather than production ownership.
- **Bachelor:** listed alongside the master’s degree, with degree details recorded in the education note.
- **Wisers** (`wisers-platform`) ownership is **led** (templates / UAP). TripSaaS, MCU, III stay `implemented`.

## Details to add when available

- Master thesis Japanese wording (`mcu-master-h1`, `mcu-master-h2`).
- `text.ja` for Cathay project-only claims (DOGI extras, GAIA extras, RKB ingest/chunking, etc.).
- Medium `released` dates; AWS Cloud Quest issuer/date.
- Skill titles that still embed proficiency (`python-expert`) — split to a field if you want.
