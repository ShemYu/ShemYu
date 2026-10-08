---
id: cathay-gaia-guardrail-redesign
type: claim
title: |-
  Led GAIA from requirements and technology selection through service design and deployment, working with the cloud team on infrastructure provisioning. Redesigned guardrails using the company's existing regex PII check and parallel per-category smaller-model classifiers. Worked with the security team on guardrail evaluation and load tested the guardrail service, recording p95 and p99 latency. Numerical quality and load-test results are no longer recalled.
focus: cathay-gaia
status: confirmed
disclosure: internal
source: Shem recollection recorded 2026-10-08; GAIA guardrail redesign retrospective;
  benchmark references from an earlier ChatGPT summary of project documents
metric: cathay-gaia-infra-metric
text:
  en: |-
    Led GAIA from requirements and technology selection through service design and deployment, working with the cloud team on infrastructure provisioning. Redesigned guardrails using the company's existing regex PII check and parallel per-category smaller-model classifiers. Worked with the security team on guardrail evaluation and load tested the guardrail service, recording p95 and p99 latency. Numerical quality and load-test results are no longer recalled.
  ja: ''
do_not_claim:
- end-to-end AI-service latency inferred from the guardrail timing estimate
- exact before/after quality scores or p95/p99 values that are no longer recalled
- Terraform authorship; the cloud team handled provisioning and Terraform
- a confirmed model-endpoint bottleneck; this was my working interpretation
- autoscaling minimum/maximum or historical failure policy that I no longer recall
- gateway reference figures used as guardrail load-test results
---

## GAIA guardrail redesign — retrospective, 2026-10-08

I reconstructed this note from my recollection on 8 October 2026. Approximate figures and details I no longer remember are marked below. The final section describes improvements I would consider today.

### Context and design questions

At the time, the company didn't yet have a GenAI service. We were building a platform so internal teams could launch GenAI applications with proper oversight, consistent internal standards, and reliable service.

For guardrails, we framed the design around three questions:

1. How should we protect GenAI applications?
2. How could we provide one central guardrail service for all internal applications?
3. How could we make sure teams used it correctly?

### My role

I led GAIA from requirements through technology selection, service architecture, and deployment. My work covered the platform services, including the AI Gateway, guardrails, and MLflow. I agreed the infrastructure requirements with the cloud team; they handled provisioning and Terraform to their infrastructure standards.

I remember my role as application ownership. I no longer recall the exact division of paging and infrastructure operations responsibilities.

### Why I redesigned the guardrails

We initially selected Llama Guard after comparing guardrail options on our selection benchmark. I remember it producing the strongest overall result in that comparison.

In use, I became concerned about the amount of context in a single guardrail call and the time spent evaluating categories outside our intended use cases. I considered splitting the checks to reduce latency. These were my engineering concerns at the time; the numerical result I recall is the latency change below.

The redesign combined the company's existing regex PII check with smaller-model classifiers, one call per blocking category. The category calls ran in parallel. The regex check handled configured PII patterns, while the model calls handled semantic categories.

I no longer recall the replacement model/version, complete category list, decision aggregation, or exact scheduling of the regex check relative to the model calls.

### Latency and evaluation

| Item | What I remember | Details I no longer recall |
|---|---|---|
| Guardrail latency | Approximately 2 s before and 0.8 s after the redesign, roughly 60% lower, **from memory** | Exact timing boundary, one check versus input-plus-output, statistic, dates, and test configuration |
| Quality evaluation | Worked with the security team on labels by guard type and included normal inputs to examine over-blocking | Dataset size, real/synthetic split, tuning versus held-out set, and before/after recall and false-positive rates |
| Guardrail-service load test | Ran the test and recorded instance information, the two-instance setup, and p95/p99 latency | Numerical results, request rate, concurrency, payloads, duration, and error rates |
| Model endpoint | My interpretation at the time was that model calls were the remaining latency constraint | Per-call traces and measurements that would distinguish model execution from queueing and service overhead |

The approximately 60% figure describes the **guardrail step**. I do not remember the original measurement convention well enough to label the 2 s and 0.8 s as mean, median, p95, or p99. I remember recording p95/p99 in the load test separately, but not their values.

I remember carrying out the quality checks. Since I no longer recall the before/after scores, I have left numerical quality comparisons open.

### Deployment and sizing

| Setting | My recollection | Detail to revisit |
|---|---|---|
| Component | Guardrail service on Databricks | Exact deployment/service identifier |
| Per-instance size | 2 CPU cores and 4 GB RAM; the starting size I remember from the project's documented spec | Exact instance type and original specification |
| Reason for starting there | It matched that per-instance spec and kept the initial cost low | Measured capacity and any later resizing |
| Instances | Two instances were configured | Whether two was the autoscaling minimum, maximum, or another setting |
| Concurrency and timeout | Left at their defaults | The default values and the layer enforcing them |

We had no earlier GenAI project to learn from, so I started with a minimum design and load tested the guardrail service. I no longer recall the complete sizing decision path or later operational outcomes.

### Gateway benchmark reference notes

The figures below came from an earlier ChatGPT summary of project documents. I have not rechecked the original workbook or its test setup, so I retain them as reference notes, separate from my recalled guardrail timing.

| Metric in the earlier summary | LiteLLM | Databricks gateway |
|---|---|---|
| Test latency | 30 ms | 280 ms |
| Test throughput | 125 requests/s | About 100 requests/s |
| Separately documented latency | Below 40 ms | 50 ms |
| Separately documented throughput | 425 requests/s | Not specified |

The summary did not preserve payloads, concurrency, versions, hardware, or whether the latency figures were averages or percentiles. The test and documented figures therefore need their original context before I use them as a comparison. They describe gateway selection, rather than the guardrail load test. I also no longer recall whether GAIA ultimately used LiteLLM.

The earlier summary mentioned guardrail comparisons across injection, privacy, and custom categories. My recollection is that we selected Llama Guard from the overall comparison; I have left individual category percentages out until I can revisit the original benchmark.

### How I would explain the work

“At the time, the company didn't yet have a GenAI service. We were building a platform so internal teams could launch GenAI applications with proper oversight, consistent internal standards, and reliable service.

For guardrails, we framed the design around three questions: How should we protect GenAI applications? How could we provide one central guardrail service for all internal applications? And how could we make sure teams used it correctly?

I led GAIA from requirements and technology selection through service design and deployment, with the cloud team handling infrastructure provisioning and Terraform.

We initially selected Llama Guard based on our benchmark. In use, I became concerned about its context size and the time spent checking categories outside our intended scope. I redesigned the guardrail using our existing regex PII check and parallel smaller-model calls, one per category.

From memory, guardrail latency went from about two seconds to about 0.8 seconds, roughly a 60% reduction. I no longer recall the exact timing convention. We evaluated with security-team labels and normal inputs, and load tested the guardrail service while recording p95 and p99. I remember those checks, though not the numerical quality or load-test results.

We started with a 2-core, 4-GB configuration, two instances, and default concurrency and timeout settings. My interpretation at the time was that model calls remained the main latency constraint. If I revisited this today, I would recover the measurements and compare alternatives using both quality and loaded tail latency.”

### What I would improve today

- Compare faster candidate classifiers on a held-out security-labeled set, measuring per-category recall, false positives, and p95/p99 under representative load.
- Revisit category coverage and the behavior when a classifier fails or times out, including retries, fallback, and fail-open/fail-closed choices.
- Set concurrency, timeout, and autoscaling policies from measured traffic, throughput, queueing, resource use, and the overall request latency budget.
- Check data-handling requirements, per-category call cost, provider limits, and model-version regressions before switching providers.

With N categories checked once on the same endpoint, a guardrail operation makes approximately N model calls before retries. Input/output checks or skipping rules may change the relationship to user-request rate. For simultaneous calls that all must finish, stage completion follows the slowest call plus service overhead; early-blocking and timeout policies can change that behavior. The combined stage's p95/p99 should be measured under fan-out.

For a stable workload, average in-flight work is approximately `average arrival rate × mean time at that component`. I would use this alongside load measurements when sizing, rather than deriving a concurrency cap or timeout from p99 alone.

These are ideas for revisiting the design today. My original concurrency and timeout settings remained at their defaults.

### Details to revisit

- [ ] Original timing convention and matched configuration for the approximate 2 s → 0.8 s comparison.
- [ ] Before/after quality scores, dataset composition, and the distinction between tuning and evaluation data.
- [ ] Blocking categories, whether any were excluded, and who agreed the coverage scope.
- [ ] Decision aggregation and failure/timeout behavior.
- [ ] p95/p99 values, test traffic, error rates, cost, and per-call timing.
- [ ] Exact Databricks deployment type, default settings, and the meaning of the two-instance configuration.
- [ ] Gateway choice and replacement model/version.
- [ ] Whether the wrong-block/missed-risk feedback loop was implemented or remained planned.
- [ ] Operational responsibilities and the teams/products using GAIA when I left.

<!-- claim-text:start -->
Led GAIA from requirements and technology selection through service design and deployment, working with the cloud team on infrastructure provisioning. Redesigned guardrails using the company's existing regex PII check and parallel per-category smaller-model classifiers. Worked with the security team on guardrail evaluation and load tested the guardrail service, recording p95 and p99 latency. Numerical quality and load-test results are no longer recalled.
<!-- claim-text:end -->

<!-- graph:start -->
## Graph

- focus: [[cathay-gaia|GAIA Enterprise Gen-AI Platform]]
- metric: [[cathay-gaia-infra-metric|Guardrail latency ~2 s → ~0.8 s (from memory)]]
<!-- graph:end -->
