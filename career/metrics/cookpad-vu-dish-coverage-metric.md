---
id: cookpad-vu-dish-coverage-metric
type: metric
title: 50% → 95%
name: issue_recall
display: 50% → 95%
from: 50%
to: 95%
window: 2026-07-08 to 2026-07-27
cohort: same-rubric 56-item window
n_cases: 15
n_items: 56
source: daily/history.json
disclosure: internal
---

Public metric is issue-level recall: domain experts annotated the issues in each video (ground truth), and the metric is the share of all annotated issues the system recalls (owner clarification 2026-10-10; earlier internal notes called this dish coverage). Internal counts only: the same-rubric window 2026-07-08 to 2026-07-27 moved 28/56 to 53/56 (94.6%, published as 95%; source fields `dish_covered`/`dish_total` in `daily/history.json`). Do not publish 53/56.

<!-- graph:start -->
## Graph

- claims: [[cookpad-vu-dish-coverage]], [[cookpad-vu-ruler-note]]
<!-- graph:end -->
