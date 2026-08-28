---
id: cathay-rkb
type: focus
title: Regulatory Knowledge Base (RKB)
kind: product
role: cathay-mle-lead
start: 2024-10
end: 2025-09
problem: Semantic search, retrieval, and comparison on regulatory and legal documents using
  enterprise RAG pipelines.
ownership: implemented
release: production
stack:
- rag
- vector-db
- databricks
- data-pipeline
- embeddings
claims:
- cathay-rkb-discovery
- cathay-rkb-decouple
- cathay-rkb-f1
- cathay-rkb-adoption
- cathay-rkb-retry
- cathay-rkb-ingest
- cathay-rkb-chunking
- cathay-rkb-retrieval
- cathay-rkb-integration
- cathay-rkb-autolabel
- cathay-rkb-quota
do_not_claim:
- F1 caused adoption / resulting in adoption / により採用
- Shem built the DS PoC
- Unity Catalog, Delta, or a forgotten table name
- Spark, TB-scale, QPS
- auto-labeling / 4-stage / retrieval miss-rate on public highlights
- stage-level diagnostics as a highlight (only per-record status is confirmed)
- failure-rate threshold, gate, or SLO (15% was an observed peak, not a configured stop)
disclosure: public
---

Semantic search, retrieval, and comparison on regulatory and legal documents using enterprise RAG pipelines.

<!-- graph:start -->
## Graph

- role: [[cathay-mle-lead|Machine Learning Engineer, team lead]]
- claims: [[cathay-rkb-discovery]], [[cathay-rkb-decouple]], [[cathay-rkb-f1|Improved regulatory Agent F1 from 0.67 to 0.89.]], [[cathay-rkb-adoption|Adopted by 2 of 5 subsidiaries.]], [[cathay-rkb-retry]], [[cathay-rkb-ingest|Designed ingestion pipelines for PDFs and structured government rules.]], [[cathay-rkb-chunking|Implemented chunking, metadata tagging, and cleanup workflows.]], [[cathay-rkb-retrieval|Improved retrieval recall and precision through iterative evaluation.]], [[cathay-rkb-integration|Integrated with internal Gen-AI platform for unified access and governance.]], [[cathay-rkb-autolabel]], [[cathay-rkb-quota]]
- stack: [[rag|RAG]], [[vector-db|Vector DB]], [[databricks|Databricks]], [[data-pipeline|Data Pipeline]], [[embeddings|Embeddings]]
<!-- graph:end -->
