# Moment Coach AI — Git-History Technical Fact Inventory

This is the tracked, repo-derived inventory behind future Cookpad resume work. It records what the Moment Coach AI `main` history can prove without turning commit volume into impact or treating local experiments as shipped work.

## Scope and attribution rules

- Source repository: `cookpad-research/moment-coach-ai`, updated from `origin/main` on 2026-08-27.
- History window: 2026-02-27 through 2026-08-19.
- Included author identities: `shem-yu <shem-yu@cookpad.com>` and `余顯漁Shem <shauns4y@gmail.com>`.
- Included evidence: the 33 non-merge commits on `main` authored by those identities. All 33 are PR-tagged in their subject.
- A commit proves a code or documentation contribution. It does not by itself prove sole ownership, production deployment, adoption, or business impact.
- Branch-only, untracked, proposal-only, and notebook-only work is not promoted to a shipped claim here.
- PR #606 (`25012512`, same-dish video selection and multi-video artifact path) is not attributed to Shem: Git records Sonanchalant as author and contains no co-author trailer. Do not transfer the separate Guideline Grounding ObservationAgent design attribution to this PR.

## Verified contribution ledger

| Date | PR / commit | Repo-verifiable technical fact | Resume use boundary |
|---|---|---|---|
| 2026-02-27 | #147 / `4f354ae0` | Expanded AG5 delivery translation to carry `wrong_actions` and `coaching_breakdown_dict` through processing and prompt output. | Supporting delivery-schema work; no outcome metric found. |
| 2026-03-11 | #202 / `fb473178` | Built the Video Explorer surface across UI, video API, `VideoService`, and S3-backed video storage, with endpoint and infrastructure tests. | Strong multimodal tooling fact; adoption and user count are unknown. |
| 2026-03-11 | #208 / `7d4e6404` | Fixed video download behavior in the Explorer UI/client flow. | Maintenance evidence, not a standalone achievement. |
| 2026-03-13 | #213 / `e71428f8` | Added video embedding generation to the video-processing action, including chunk construction, embedding, persistence, and tests. | Strong multimodal infrastructure fact; no retrieval-quality uplift is sourced. |
| 2026-03-17 | #217 / `604d0216` | Refactored embedding logic into reusable infrastructure abstractions for models, similarity search, toolkit access, and Vertex AI, with broad unit coverage. | Supports platform/reusability wording; do not claim team-wide adoption without evidence. |
| 2026-03-18 | #219 / `cc6e6810` | Persisted workflow name and workflow version in Burr state. | Traceability/versioning support; small change. |
| 2026-03-19 | #220 / `78a196aa` | Migrated video processing from the temporary shared embedding module to the infrastructure embedder. | Completes the #217 migration; combine with #213/#217 in resume wording. |
| 2026-03-20 | #222 / `469be7dd` | Added a semantic-search video toolkit and demo path over stored video embeddings, with search/toolkit tests. | Strong retrieval/tooling fact; no accuracy metric found. |
| 2026-03-30 | #240 / `002402f5` | Updated O1 assessment cases to retain prior-session feedback and application IDs, plus seed tooling and evaluator changes. | Supports cross-session evaluation continuity; not a product-quality result. |
| 2026-04-03 | #249 / `f9118232` | Updated the Explorer agent model configuration. | Configuration maintenance; model choice is not an achievement by itself. |
| 2026-04-04 | #239 / `d3699633` | Implemented a stateful Visual Explorer agent for locating frames that answer a question, including API/service wiring, Burr app/persistence, UI integration, and integration tests. | Strong agentic video-understanding fact; call it an internal tool unless release evidence is added. |
| 2026-04-07 | #254 / `081bf4bb` | Fixed Visual Explorer re-processing and propagated semantic-search results through the workflow/API. | Reliability follow-up to #239. |
| 2026-04-16 | #264 / `d8763af4` | Refreshed O1 assessment cases and added a pool index for the evaluation set. | Dataset maintenance; no quality uplift should be inferred. |
| 2026-05-01 | #299 / `8b9fc681` | Added the Guideline Grounder action and workflow: temporal detection, observation planning, frame selection, crop observation, and description correction, integrated into the v4 graph with unit tests and a specification. | Strong multimodal-agent architecture fact; later replacement means it should not be described as the current production stack. |
| 2026-05-12 | #326 / `f63b3440` | Reworked Guideline Grounder frame handling to use the shared `VideoService`, removing its direct OpenCV dependency. | Infrastructure consolidation; no latency or cost result found. |
| 2026-05-15 | #331 / `56915538` | Routed temporal-detector video access through the Vertex path. | Operational/configuration fix; not a standalone resume bullet. |
| 2026-06-08 | #405 / `000719e8` | Built the assessment-evaluation core suite: frozen versioned states, runner, evaluator, state sync, and a backtrace dashboard. | Strong evaluation-platform fact; pair with verified run-time evidence only when denominator and date are retained. |
| 2026-06-08 | #427 / `831535dc` | Updated the assessment runner for the newer action-context interface. | Compatibility maintenance. |
| 2026-06-15 | #465 / `0b1bbc06` | Migrated video/text retrieval to Gemini Embedding 2 with 3,072-dimensional outputs, model-scoped S3 artifacts, metadata compatibility checks, and rejection of incompatible legacy vectors. | Strong embedding-platform migration fact; no retrieval-accuracy improvement is sourced. |
| 2026-06-15 | #481 / `ac0b07ac` | Implemented recall-focused Assessment v5 with structured assessor stages for candidate generation, right-action finding, follow-up synthesis, frozen-state evaluation, and tests. | Strong evaluation/agent design fact; do not publish internal experimental scores without their frozen cohort and evaluator version. |
| 2026-06-18 | #533 / `21252ce8` | Fixed end-of-file tail windows in video embedding generation and added edge-case tests. | Reliability/correctness evidence; no measured incident reduction found. |
| 2026-06-23 | #553 / `ad4e3ff0` | Increased learner-profile updater tool iterations and covered the behavior with tests. | Small agent-loop maintenance item; no quality result found. |
| 2026-07-03 | #578 / `dde9f49e` | Removed the hard requirement for key concepts when determining end-to-end dish support. | Contract correction; impact is not isolated. |
| 2026-07-06 | #586 / `35eb0224` | Established the Generation v3 O1 candidate-coverage evaluation lane with static chef ground truth, extraction models/specs, runner, comparison/report tooling, and tests. | Strong evaluation-system fact; historical scores require their exact extraction/judge contract. |
| 2026-07-08 | #592 / `fc8d9ddb` | Added deterministic generation of O1 ground truth from static test-set HTML and updated coverage reports and failure-analysis documents. | Supports reproducible GT lineage; do not equate static-source conversion with human validation. |
| 2026-07-14 | #603 / `3e0d2440` | Authored the recall-oriented Generation v3 candidate-generation specification covering internalized-knowledge baseline and warmup-axis design. | Design evidence; the spec alone is not shipped behavior. |
| 2026-07-15 | #611 / `b1b4321f` | Implemented warmup internalization and focus axes in the Generation v3 candidate pool, including prompt, ranking, state, and turn-test changes. | Merged implementation; any quality delta must use a compatible evaluation. |
| 2026-07-16 | #616 / `8f3a3cef` | Tightened O1 coverage state helpers, delivery-state construction, and test typing. | Evaluation reliability/maintainability support. |
| 2026-07-16 | #612 / `bc15f3a6` | Added recall-focused O1 Coverage Eval v5 for the candidate warmup round, including delivery-state tooling, focused reports, and test coverage. | Strong evaluation iteration fact; keep it distinct from production generation behavior. |
| 2026-08-04 | #633 / `4b80a81e` | Shipped warmup candidate generation as four concurrent draws unioned after per-draw synthesis, and rebuilt large-pool ranking as chunked criterion scoring plus holistic ordering while preserving downstream contracts. | Strong production-path/reliability fact. The verified internal benchmark and 4x generation-token caveat are preserved in `data/work/cookpad.yaml`. |
| 2026-08-04 | #636 / `f71efdec` | Built chunked O1 extraction, Delivery v2 construction, and validation with per-draw pools plus a shared-sources call. | Strong evaluation-provenance fact; research/eval path, not product behavior. |
| 2026-08-14 | #661 / `9e49f646` | Added one-shot Dish Result understanding decomposition, Ground Truth v3 assets, review UI, batch/validation tooling, coverage console, and artifact tests. | Strong human-review/evaluation-contract fact; decomposition counts are a later rubric and must not be merged with the earlier 56-item metric. |
| 2026-08-19 | #666 / `15b56449` | Added observed-cooking/current-cook audit tasks and a canonical, human-equivalence evaluation pipeline with deterministic contracts, fixtures, projection, scoring, delivery viewer, and extensive tests. | Strong canonical-evaluation and video-fact-audit fact; observed-cooking contract was still incomplete, so no quality uplift is claimed. |

## User-confirmed collaboration outside authored commits

| Work | Confirmed contribution | Boundary |
|---|---|---|
| Guideline Grounding v2 ObservationAgent / PR #461 / `741fa4a3` | Shem designed the iteration and mentored Sonan through its implementation. | Attribute design and mentorship to Shem, implementation to Sonan; unrelated to PR #606. |

## Resume-relevant workstream facts

These are safe technical summaries of the ledger, not ready-made impact bullets:

1. Built multimodal video infrastructure spanning upload/storage, video services, embedding generation, semantic retrieval, and a stateful frame-finding agent.
2. Defined the upstream observation problem and designed and implemented staged video grounding so downstream diagnosis could be evaluated independently. A legacy 14-case manual review found dish-specific signals in 13 cases but correct diagnoses in only 2, isolating unresolved causal selection in Assessment rather than establishing visual accuracy or uplift.
3. Built versioned, replayable evaluation systems over frozen agent states, with static/canonical ground-truth lineage, automated extraction and judging, review surfaces, and case-level backtraces.
4. Improved candidate-generation reliability through recall-focused warmup axes, multi-draw union, chunked scoring, holistic ranking, and explicit downstream contract validation.
5. Developed evaluation-integrity tooling that distinguishes source evidence, candidate claims, extraction, judge decisions, delivery views, and human-equivalence constraints.
6. Hardened operational correctness through workflow-version metadata, interface migrations, model-scoped embedding caches, incompatible-vector rejection, EOF-window handling, and deterministic artifact validation.

## Public resume disclosure decision

**[User approved 2026-08-27]** The six sanitized workstream summaries above may be used in the detailed public resume, together with compatible metrics and their full evaluation boundaries. This approval does not extend to internal model names, team names, user counts, unpublished benchmark scores, branch-only work, or claims of sole ownership, adoption, or business impact that the Git history cannot prove. The 50% to 95% dish-coverage result remains tied to its fixed 15-case, 56-item rubric; the legacy 13-of-14 grounding signal and 2-of-14 correct-diagnosis result remain a failure-localization audit, not an accuracy or uplift claim.

### User-confirmed final public resume wording

**[User confirmed 2026-08-27]** Use the following five bullets as the final Cookpad resume version:

- Built a multi-agent video-understanding system to identify cooking issues from video, improving recall from 50% to 95% through iterative grounding, retrieval, and reasoning improvements.
- Designed evaluation-focused video grounding around ingredients, actions, timing, and state changes, reducing video context from 40 to 7 minutes while maintaining comparable precision.
- Built an end-to-end agent evaluation framework spanning ground-truth design, automated judging, human review, and reproducible test runs.
- Refactored a single-agent video-understanding workflow into a multi-agent, RAG-style architecture to separate evidence retrieval from downstream reasoning and address observed failure modes.
- Designed an evaluation-to-production architecture for AI agents, covering capability-based testing, human review, controlled rollout, and production monitoring.

Owner-grounded context that must survive future rewrites:

- The 50% to 95% recall result was the final outcome of more than one month of iteration across the overall video-understanding system, not the isolated effect of one graph or refactor.
- The 40-to-7-minute result measures the amount of video context retained for downstream assessment. The work replaced general descriptions with cooking-evaluation evidence centered on ingredients, actions, timing, and state changes while maintaining comparable precision; it is not a latency claim.
- The single-agent to multi-agent RAG-style refactor was driven by observed failure patterns and separated evidence retrieval from downstream reasoning.
- The evaluation-to-production lifecycle was an architecture design covering evaluation, human review, controlled rollout, monitoring, and feedback. It was not fully implemented, so the resume must use `Designed`, not `Built` or `Implemented`.
- Candidate-generation mechanics and runtime-integrity safeguards remain valid supporting/interview material but are intentionally excluded from the five final resume bullets.

## Legacy Guideline Grounder metric audit

The pre-Obsidian archive `cooking_experiment_analysis` contains a useful but easy-to-overstate Guideline Grounder result:

| Field | Verified value | Boundary |
|---|---|---|
| Source run | `evaluation-V1_20260428_185044.yaml`, 2026-04-28, `vertex_ai/gemini-2.5-pro` | Legacy V1 pipeline/model; later architectures and eval contracts are different. |
| Cohort | 16 test cases; 14 usable assessments; 2 pipeline failures | Carbonara and dashimaki tamago were excluded from Grounding-effectiveness classification. |
| Grounding signal | 13/14 evaluable cases (92.9%) manually classified as showing some dish-specific grounding signal | Broad analyst taxonomy: includes useful facts even when the diagnostic axis, timestamp, visual reading, update, or downstream causal selection was wrong. Not accuracy. |
| Successful correction | 2/14 evaluable cases (14.3%): chicken saute and pan-fried fish | Both were manually classified as Grounding effective and successfully converted to the intended diagnosis. |
| End-to-end result | Run metadata reports average score `-2.0` | The final score did not establish an end-to-end improvement; additional facts often fed an incorrect downstream diagnosis. |

**[User confirmed 2026-08-27]** Shem deliberately defined and cleaned the upstream observation problem before optimizing downstream diagnosis. The generic Video Description path was not reliably surfacing the target-dish facts needed by Assessment, so he designed and implemented Guideline Grounder to make those inputs sufficiently focused and inspectable. This was a system-decomposition strategy: once upstream observation was cleaner, the team could evaluate whether the downstream Assessment understood why the cooking problem occurred rather than conflating missing evidence with faulty causal reasoning. The legacy review confirmed the upstream intervention by surfacing dish-specific signals in 13/14 evaluable cases, while also showing that individual observations could still be wrong, non-decisive, or conflicting. Only 2/14 converted into successful diagnoses, isolating primary-cause selection as the remaining downstream failure. That downstream Assessment had not yet been fixed or revalidated in this legacy iteration. Do not recast the 13/14 observation signal as diagnostic correctness or imply that the identified causal-selection problem was resolved.

Source lineage:

- `cooking_experiment_analysis/report/20250423/evaluation-V1_20260428_185044.yaml`: run metadata and raw per-case outputs.
- `cooking_experiment_analysis/report/20250423/6wg/boss_note_20260430.md`: the 13/14 versus 2/14 manual classification and case list.
- `cooking_experiment_analysis/report/20250423/analysis_20260427.md`: narrower conclusion that Grounding increased target-dish process detail but did not ensure correct coaching diagnosis.
- `cooking_experiment_analysis/report/20250423/6wg/cases/*/evidence.md`: seven standalone case deep-dives; the remaining cases are referenced directly from the raw evaluation YAML rather than having equivalent standalone evidence packets.

Safe future wording:

> Defined and cleaned the upstream observation layer with a staged video-grounding pipeline so downstream diagnosis could be evaluated independently; a legacy 14-case manual review surfaced dish-specific grounding signals in 13 cases but correct diagnoses in only 2, isolating unresolved causal selection in Assessment as the next bottleneck.

Do not shorten this to “93% grounding accuracy,” “93% coverage,” or “improved accuracy to 93%.” No compatible baseline was scored with the same manual taxonomy, and the 13/14 category includes partially useful but incorrect or non-decisive evidence.

## Do not promote without more evidence

- Do not use commit count, lines changed, or PR count as an impact metric.
- Do not claim the legacy downstream Assessment causal-selection problem was fixed; this evidence only diagnoses the unresolved bottleneck.
- Do not claim sole ownership of team systems from Git authorship alone.
- Do not claim that every merged component remained online; Guideline Grounder and other architectures were later replaced or absorbed.
- Do not attribute PR #606 to Shem without separate evidence or confirmation; the user-confirmed design ownership concerns the earlier Guideline Grounding v2 ObservationAgent, not #606.
- Do not combine the earlier 15-case/56-item dish metric with the later 61-item or 109-contract rubrics.
- Do not describe branch-only Investigator hypothesis work as implemented, merged, evaluated, or shipped until it reaches those states.
