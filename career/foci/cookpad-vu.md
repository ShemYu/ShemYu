---
id: cookpad-vu
type: focus
title: Video-understanding coaching agent
kind: product
role: cookpad-senior-ai
start: 2026-02
end: Present
problem: Infer where a learner is stuck from cooking video and voice, then coach the next
  step.
ownership: implemented
release: production
stack:
- multimodal-agents
- capability-based-evals
- video-understanding
claims:
- cookpad-vu-pipeline
- cookpad-vu-dish-coverage
- cookpad-vu-evals
- cookpad-vu-ruler-note
- cookpad-vu-internal-coaching
- cookpad-vu-architecture-bound
do_not_claim:
- 40% → 95% as the same ruler; 40.5% (30/74 on 2026-07-06) and 95% (53/56) used different
  denominators
- knowledge coverage numbers (31.9% → 79.2%, 14.9%, 56.3%, 27/48, 38/48)
- coaching eval 67.6% → 83.0% (+15.4 pp) or 15-case / 103-unit / 56-case / 9 min
- flaky-miss RCA (73 flaky misses; 64% incomplete candidate hypotheses)
- Shem or Sonan implemented, shipped, or owned v5 investigator
- production is Recall-first Candidate Generator + Debater Investigator
- Guideline grounder v2 is in production
- model names, fusion methods, Moment team name, 20 users
disclosure: public
---

Inputs: cooking video and learner voice. Infer where the learner is stuck; older wording was decide reteach, narrow, or advance so the next prompt targets that gap. Public architecture is the staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.

## Eval history (one measurement story)

An earlier public sentence said Coverage 40% → 95% on a versioned eval set. That was a shorthand, not two competing truths. Source: `daily/history.json` (23 reports, always 15 cases).

- 2026-07-06: dish 30/74 = 40.5%. This is the reading behind the earlier 40%.
- Same-rubric 56-item window 2026-07-08 → 2026-07-27: 28/56 → 53/56 (50% → 94.6%). Owner locked the public sentence to 50% → 95% (53/56) because this is the same denominator. 53/56 is 94.6%; owner accepted writing 95% (53/56). So 40% and 95% were both real readings, but not the same ruler.
- Same-rubric series 2026-07-08 to 2026-08-04: dish_total 56. Peak dish 53/56 on 2026-07-27 and 2026-08-02. Knowledge peaked 38/48 = 79.2% on 2026-08-02. Knowledge coverage remains remaining work; do not put a knowledge number on a public view.
- Later, different ruler: after 2026-08-11 the set is 61 dish items; 2026-08-12 onward `v3_canonical_claim` (stricter). Latest 2026-08-19 is 23/61 dish / 27/48 knowledge. That is a different ruler, not a product regression and not an arrow from 53/56. Parent DR units later decomposed into VU / DU / LVO children (109-contract family); 2026-08-18 dish 19/61 is that later metric.

## Architecture journey

Name lock: Guideline grounder (not Guideline grounding, not Galactic Rounder). Propose / influence only — not a clean Shem-owned shipped lineage.

1. **Video Description v1** — very detailed Video Description, then agents to verify. Needed near-100% precision on the transcript-like description; even a small hallucination damages the rest. Cost is wall-clock: typical source videos about 20–50 minutes; processing about 30–45 minutes. That path did not succeed and is not a public highlight. No SLA, dollar cost, or GPU type recorded.
2. **Proposed split** — Shem proposed (not implemented / not shipped as current production): Recall-first Candidate Generator, and Debater Investigator for video grounding. Diagnosis: mixing recall and precision in one agent hurt performance. Proposed split: Recall first → Ranker → Precision via Investigator. Speech typos: Recode = Recall, Debezter = Debater. Do not write that production is currently this stack.
3. **Guideline grounder v1** — Shem only. No Sonan. Staged ground-then-assess: Detect → Plan → Select → Observe → Correct. Source: `20260424_feat_guideline-grounding-action.md` (#299). ~2–4s latency is not a win to write.
4. **Guideline grounder v2** — Collaboration with Sonan (do not invent title or ownership beyond this). ObservationAgent loop, skill-routed observation. Owner ruling 2026-08-27: **did not ship / not online**. Do not claim v2 is in production. Source: `20260608_feat_guideline-grounding-v2-observation-agent.md`.
5. **Influence on v5** — Guideline grounder design later influenced the final v5 investigator. Influence only. Do not write that Shem or Sonan implemented, shipped, or owned v5 investigator.
6. **Iteration** — Company iterations often unplanned-refactored the whole architecture. Shem's pieces mostly remained as concepts that later rewrites absorbed. After a version was replaced it was no longer online. Culture commentary stays off public views.
7. **Other systems** — Video embeddings + semantic search + Visual Explorer (internal tool). Shem PRs #213/#217/#220/#222/#202/#239. Gemini Embedding 2 migration to 3072-d with model-scoped cache; no retrieval-accuracy lift sourced. Same-dish / multi-video selection (#606) is **not** Shem-authored (Git records Sonanchalant; no co-author trailer). Observed cooking audit: Shem 15b56449 (#666); contract incomplete, no metric.

Canonical hash-locked 15-case `make eval` pipeline + viewer; README example 77/103 (74.8%) is run-varying / unpublished. Assessment v5 + frozen-input LLM-as-judge suite + failure taxonomy stay unpublished unless a view explicitly selects an internal claim.

Tracked commit ledger: [`career_evidence/moment_coach_ai_git_history.md`](../../career_evidence/moment_coach_ai_git_history.md) (33 main-branch PRs, 2026-02-27 through 2026-08-19).

<!-- graph:start -->
## Graph

- role: [[cookpad-senior-ai|Senior AI Engineer]]
- claims: [[cookpad-vu-pipeline]], [[cookpad-vu-dish-coverage]], [[cookpad-vu-evals]], [[cookpad-vu-ruler-note]], [[cookpad-vu-internal-coaching]], [[cookpad-vu-architecture-bound|Guideline grounder (v1 Shem-only; v2 with Sonan did not ship)]]
- stack: [[multimodal-agents|multimodal agents]], [[capability-based-evals|capability-based evals]], [[video-understanding|video understanding]]
<!-- graph:end -->
