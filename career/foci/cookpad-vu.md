---
id: cookpad-vu
type: focus
title: Video-understanding coaching agent
kind: product
role: cookpad-senior-ai
start: 2026-02
end: Present
problem: Infer where a learner is stuck from cooking video and voice, then coach the next step.
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
- cookpad-vu-grounder-v1
- cookpad-vu-observation-agent
- cookpad-vu-video-infra
- cookpad-vu-eval-architecture
- cookpad-vu-git-history
do_not_claim:
- 40% → 95% as the same ruler
- combining 56-item dish metric with later 61-item or 109-contract rubrics
- 93% grounding accuracy / 93% coverage
- 67.6 → 83.0 / +15.4 pp as recall or a second coverage arrow
- Guideline grounder v2 or ObservationAgent as production
- Shem owned or shipped v5 investigator
- attributing PR #606 to Shem
- commit count or PR count as impact
- Moment team name, 20 users, model names, fusion methods
disclosure: public
---

Video-understanding and cooking-coaching agent. Inputs: cooking video and learner voice. Infer where the learner is stuck. Public architecture: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.

## B. Eval

Public highlight is 50% → 95% (53/56) on a fixed 15-case, 56-item set (same-rubric window 2026-07-08 → 2026-07-27; 28/56 → 53/56 = 94.6%, published as 95%). Source: `daily/history.json`.

- 2026-07-06 30/74 = 40.5% is a **different ruler**, not an arrow into 53/56.
- After 2026-08-11 the set is 61 dish items; 2026-08-12 onward `v3_canonical_claim`. Later 23/61 is not a product regression from 53/56.
- Knowledge coverage remained remaining work; do not publish knowledge percentages.
- Do not use 67.6% → 83.0% as recall; that number is retired from the story.

## C. Architecture

1. **Video Description path** — 20–50 minute videos, ~30–45 minutes processing; near-100% precision constraint. Did not succeed as production. Then proposed Recall-first Candidate Generator → Ranker → Investigator. Informed later designs; **not** verified as the shipped stack.
2. **Guideline Grounder v1** (Shem; PR #299) — Detect → Plan → Select → Observe → Correct. Legacy 14-case review: dish-specific signals in 13, correct diagnoses in 2. Isolates Assessment causal selection; **not** 93% accuracy.
3. **ObservationAgent v2** — Shem designed and mentored Sonan (PR #461 / `741fa4a3`). **Did not ship.** Unrelated to PR #606.
4. **Video infrastructure** — Video Explorer, embeddings, similarity search, semantic retrieval, Visual Explorer (internal). Gemini Embedding 2 → 3072-d with model-scoped cache. No retrieval-accuracy lift. PRs #202/#213/#217/#220/#222/#239.
5. **Evaluation architecture** — frozen-state suites, LLM-as-judge, failure taxonomy, canonical GT, review UI, observed-cooking audit (#666; contract incomplete). Human-equivalence is conformance, not production accuracy.

Company iterations often replaced architectures; do not claim every merged component remained online.

## D. Git history

Tracked ledger: [`career_evidence/moment_coach_ai_git_history.md`](../../career_evidence/moment_coach_ai_git_history.md) — 33 main-branch PRs, 2026-02-27 through 2026-08-19. A commit is contribution, not ownership, deployment, or impact.

<!-- graph:start -->
## Graph

- role: [[cookpad-senior-ai|Senior AI Engineer]]
- claims: [[cookpad-vu-pipeline]], [[cookpad-vu-dish-coverage]], [[cookpad-vu-evals]], [[cookpad-vu-ruler-note]], [[cookpad-vu-internal-coaching|67.6-83.0 is not the recall story; public recall is 50-95 (53/56)]], [[cookpad-vu-architecture-bound]], [[cookpad-vu-grounder-v1]], [[cookpad-vu-observation-agent]], [[cookpad-vu-video-infra]], [[cookpad-vu-eval-architecture]], [[cookpad-vu-git-history]]
- stack: [[multimodal-agents|multimodal agents]], [[capability-based-evals|capability-based evals]], [[video-understanding|video understanding]]
<!-- graph:end -->
