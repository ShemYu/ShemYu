---
id: cathay-gaia-infra-metric
type: metric
title: Guardrail latency ~2 s → ~0.8 s (from memory)
name: guardrail_latency
display: Approximately 2 s → 0.8 s (~60%; from memory)
from: approximately 2 seconds
to: approximately 0.8 seconds
window: Before/after dates no longer recalled; retrospective recorded on 2026-10-08
cohort: Guardrail step; exact timing boundary, statistic, and test configuration no
  longer recalled
n_cases: null
n_items: null
source: Shem recollection recorded 2026-10-08; GAIA guardrail redesign retrospective
disclosure: public
---

## Recalled timing

I remember guardrail latency being approximately **2 seconds before** and **0.8 seconds after** the redesign. This implies roughly **60%** lower latency: `(2 - 0.8) / 2 = 60%`. The values are estimates from memory recorded on 8 October 2026.

| Detail | Current record |
|---|---|
| Scope | Guardrail step |
| Timing convention | No longer recalled: a single check versus input-plus-output, and mean/median/percentile |
| Dates and test configuration | No longer recalled |
| Load-test percentiles | I remember recording p95 and p99 for the guardrail service; their values are no longer recalled |
| Quality scores | I remember evaluation with the security team; before/after recall and false-positive rates are no longer recalled |

I have kept the remembered timing pair separate from the load-test percentiles. If I recover the original results, I would add the timing boundaries, statistic, workload, configuration, and corresponding quality measurements here.

<!-- graph:start -->
## Graph

- claims: [[cathay-gaia-guardrail-redesign]], [[cathay-gaia-infra]]
<!-- graph:end -->
