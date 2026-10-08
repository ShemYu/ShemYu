---
id: cathay-gaia
type: focus
title: GAIA Enterprise Gen-AI Platform
kind: platform
role: cathay-mle-lead
start: 2024-11
end: 2025-06
problem: Internal Gen-AI platform providing model hub, guardrails, retrieval systems,
  evaluation tools, and multi-product orchestration.
ownership: led
release: production
stack:
- llm-ops
- databricks
- vector-search
- agents
- rag
- model-serving
claims:
- cathay-gaia-infra
- cathay-gaia-architecture
- cathay-gaia-vector
- cathay-gaia-governance
- cathay-gaia-multiproduct
- cathay-gaia-deploy
- cathay-gaia-guardrail-redesign
do_not_claim:
- end-to-end AI-service latency inferred from the recalled guardrail estimate
- Terraform authorship; the cloud team handled infrastructure provisioning
disclosure: public
---

Internal Gen-AI platform providing model hub, guardrails, retrieval systems, evaluation tools, and multi-product orchestration.

## Context and guardrail design

At the time, the company didn't yet have a GenAI service. We were building a platform so internal teams could launch GenAI applications with proper oversight, consistent internal standards, and reliable service.

We framed guardrail design around three questions: how to protect GenAI applications, how to provide one central guardrail service for all internal applications, and how to make sure teams used it correctly.

## Guardrail retrospective — 2026-10-08

I led GAIA from requirements and technology selection through service design and deployment, working with the cloud team on infrastructure provisioning and Terraform.

For guardrails, we moved from the initial Llama Guard check to the company's existing regex PII check plus parallel per-category smaller-model classifiers. From memory, guardrail latency fell from approximately **2 s to 0.8 s**, roughly **60%**. I no longer recall the exact timing convention. I remember the security-team evaluation and guardrail-service load test, including recording p95/p99, but not their numerical results.

The guardrail service started with a remembered 2-core / 4-GB configuration, two instances, and default concurrency/timeout settings. I no longer recall whether two was the autoscaling minimum or maximum. My interpretation at the time was that model calls remained the main latency constraint.

The detailed guardrail-retrospective note records the implementation, what I remember, details to revisit, and what I would improve today.

<!-- graph:start -->
## Graph

- role: [[cathay-mle-lead|Machine Learning Engineer, team lead]]
- claims: [[cathay-gaia-infra]], [[cathay-gaia-architecture|Designed the overall system architecture for the enterprise Gen-AI platform.]], [[cathay-gaia-vector|Integrated Databricks VectorSearch and scalable document pipelines.]], [[cathay-gaia-governance]], [[cathay-gaia-multiproduct]], [[cathay-gaia-deploy|Solutions deployed using Databricks workflows and AWS infrastructure.]], [[cathay-gaia-guardrail-redesign]]
- stack: [[llm-ops|LLM Ops]], [[databricks|Databricks]], [[vector-search|Vector Search]], [[agents|Agents]], [[rag|RAG]], [[model-serving|Model Serving]]
<!-- graph:end -->
