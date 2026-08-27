# Shem Yu
**Senior AI Engineer @ Cookpad | GenAI, AI Agents & MLOps | Tokyo**

[Email](mailto:shauns4y@gmail.com) | [Website](https://github.com/ShemYu) | [GitHub](https://github.com/ShemYu) | [LinkedIn](https://www.linkedin.com/in/shem-yu-a10494219/) | [Medium](https://medium.com/@shemyu)


## Summary
Applied AI engineer with 6 years building production agents, RAG platforms, and shared GenAI infrastructure. Now at Cookpad developing multimodal coaching agents, with a focus on agent evaluation, reasoning architecture, and reliability. Previously led an MLE team delivering production GenAI systems in financial services.



## Experience

### Senior AI Engineer at Cookpad
_2026-02 - Present_


Building AI that makes everyday life more joyful.




- Built and iterated the video-understanding system as a staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.

- Raised dish coverage from 50% to 95% (53/56) on a fixed 15-case, 56-item eval set; knowledge coverage remains the remaining optimization target.

- Capability-based evals and automated scoring for observation accuracy, issue coverage, factuality, coherence, and turn-level coaching quality.




### Machine Learning Engineer, team lead at Cathay Financial Holdings
_2022-09 - 2026-01_


Led 4 full-time reports (7 including contractors), overseeing AI project deployment and departmental internal agent development.




- Developed Departmental Internal AI Agents with Google ADK, automating deep research tasks, reducing analysis time from 2 hours to 15 minutes.

- Designed and built GenAI infrastructure (AI Gateway, Guardrails, MLflow), optimizing internal AI service latency by 60%.

- Implemented FinOps agent, achieving 30% GPU cost reduction.

- Reduced overall cloud spend by 40% through FinOps practices.

- With a data scientist, mapped the client's regulatory-comparison workflow in a workshop (legal and compliance participated) and selected it as the pilot; DS built the PoC, and I handled production readiness as a Databricks deployment workflow, storing related data on the Databricks data layer per internal access rules.

- Decoupled the DS-built PoC into external-regulation processing, internal-regulation processing, and comparison, all daily-triggered because regulation updates' finest grain is one day.

- Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.

- Regulatory pipeline: per-record processing status; max 3 retries with increasing wait; after 3 failures mark failed and retry the next day.

- Solutions deployed using Databricks workflows and AWS infrastructure, ensuring scalable and secure operations.

- CFH Cloud Creative Award 2024, 1st Place

- Departmental MVP, Q1 2025




### Senior AI Platform Engineer at Wisers Information Limited
_2020-11-01 - 2022-05-01_


Support cross-team AI solution integration, enabling seamless transition to unified platforms across new and legacy projects.




- Develop standardized ML project templates (AI Cloud Platform template; FastAPI, CI/CD, Kubernetes), reducing deployment time from 2 weeks to 3 days, adopted by 30+ projects.

- Implement NLP-focused Python library (UAP Common Library) with 70% internal adoption and 90%+ code coverage, improving productivity and reliability for AI developers.

- Lead automation of documentation pipelines via Sphinx and CI, enhancing onboarding efficiency and platform usability.




### Data Scientist at TripSaaS
_2019-12-01 - 2020-11-01_


Assist in maintaining ETL pipelines and data collection, ensuring stable analytics during dynamic business environments.




- Analyze customer order data using statistical modeling (FP-Growth, K-means, 4 clusters) to support marketing and segmentation strategies.

- Extract and optimize feature patterns from travel itineraries with CKIP NLP and frequent pattern mining, improving search relevance and user experience.




### Research assistant at Ming Chuan University
_2017-06-01 - 2019-06-01_


Assist teaching as a Teaching Assistant for Database Theory, supporting curriculum delivery and mentoring undergraduate students.




- Lead student research teams in multiple industry-university collaboration projects, coordinating with external partners and delivering actionable data science solutions.




### Intern at Institute for Information Industry, III
_2017-05-01 - 2017-11-01_


Facilitate communication and project delivery between university and III teams, ensuring alignment on deliverables and expectations.




- Develop full-stack web applications from end to end for social data analysis, supporting the transformation of raw posts into interactive word clouds and buzzword visualizations.

- Analyze and extract insights from social media data, applying NLP and visualization tools to generate actionable reports for industry partners.







## Education

### Master in Computer Science & Information Engineering at Ming Chuan University
_2017-06 - 2019-07_
Score: 3.82



- Graduate thesis: Yu, H. Y. and Lee, Y. S. 'The Portfolio Analysis of the Key Fans for FB fan pages,' 2019.

- Presented the research results twice on behalf of the laboratory and won the third prize once




### Bachelor in Computer Science & Information Engineering at Ming Chuan University
_2012-06 - 2016-06_








## Skills

- **Cloud & Infra**: AWS (EC2, Fargate, Lambda, Route53), Databricks, Distributed Systems, High-Availability Analytics, AI Gateway, Guardrails, MCP Protocol, A2A Protocol

- **Data Engineering**: AP Data Layer Design, SQL, NoSQL, Data Pipeline Design, ETL, Data Visualization

- **Generative AI & NLP**: Agent System Design, Retrieval-Augmented Generation (RAG), Large Language Models (LLM), Prompt Engineering, ASR/TTS, Embedding Databases, Search/Indexing Techniques

- **Language**: Chinese (Native), English (Limited Working)

- **Leadership & Communication**: Team Leadership, Project Management, Cross-Team Collaboration

- **MLOps & Deployment**: Databricks, MLflow, Docker, CI/CD (Azure DevOps), Kubernetes, AWS SageMaker, AWS Lambda

- **Programming & ML Frameworks**: Python, R (basic), C/C++ (familiar), Hugging Face, FastAPI, Google ADK, LangChain, LangGraph, PyTorch, TensorFlow, scikit-learn, pandas, NumPy, SciPy, Matplotlib




## Certificates

- AWS Certified Cloud Practitioner (Amazon Web Services)

- AWS Cloud Quest: Cloud Practitioner

- AWS Certified Machine Learning - Specialty (Amazon Web Services)




## Publications

- [AI Agent 專案架構最佳實踐](https://medium.com/@shemyu/ai-agent-%E5%B0%88%E6%A1%88%E6%9E%B6%E6%A7%8B%E6%9C%80%E4%BD%B3%E5%AF%A6%E8%B8%90-8d8613fde368) - Medium

- [容器化技術Podman的初體驗](https://medium.com/@shemyu/%E5%AE%B9%E5%99%A8%E5%8C%96%E6%8A%80%E8%A1%93-podman%E7%9A%84%E5%88%9D%E9%AB%94%E9%A9%97-f85cc07beff6) - Medium




## Projects

### Video-understanding coaching agent

_2026-02 - Present_



Infer where a learner is stuck from cooking video and voice, then coach the next step.




- Built and iterated the video-understanding system as a staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.

- Raised dish coverage from 50% to 95% (53/56) on a fixed 15-case, 56-item eval set; knowledge coverage remains the remaining optimization target.

- Capability-based evals and automated scoring for observation accuracy, issue coverage, factuality, coherence, and turn-level coaching quality.




**Keywords**: Multimodal AI, Agent Evaluation, video understanding



### DOGI Multi-Agent Productivity Suite

_2025-01 - 2025-12_



Internal productivity tools powered by multi-agent workflows, including meeting scheduling, summarization, and FinOps automation.




- Developed Departmental Internal AI Agents with Google ADK, automating deep research tasks, reducing analysis time from 2 hours to 15 minutes.

- Led development of a 5-agent productivity suite from 13 requirements to MVP; coordinated 10 contributors and launched to LINE users.

- Implemented multi-agent delegation patterns for enterprise workflows.

- Developed meeting scheduling agent integrating calendar and internal APIs.

- Designed session persistence and storage strategy using Redis/Postgres.




**Keywords**: Multi-Agent System, Workflow Orchestration, Redis, PostgreSQL, FinOps, LangGraph/ADK Pattern



### GAIA Enterprise Gen-AI Platform

_2024-11 - 2025-06_



Internal Gen-AI platform providing model hub, guardrails, retrieval systems, evaluation tools, and multi-product orchestration.




- Designed the overall system architecture for the enterprise Gen-AI platform.

- Integrated Databricks VectorSearch and scalable document pipelines.

- Delivered evaluation, guardrail, and governance modules for production workloads.

- Supported multi-product integration including meeting assistants and FinOps agents.




**Keywords**: LLM Ops, Databricks, Vector Search, Agents, RAG, Model Serving



### FinOps

_2025-01 - 2025-12_



GPU and cloud spend control for internal AI services.




- Implemented FinOps agent, achieving 30% GPU cost reduction.

- Reduced overall cloud spend by 40% through FinOps practices.




**Keywords**: FinOps, AWS



### Regulatory Knowledge Base (RKB)

_2024-10 - 2025-09_



Semantic search, retrieval, and comparison on regulatory and legal documents using enterprise RAG pipelines.




- Designed ingestion pipelines for PDFs and structured government rules.

- Implemented chunking, metadata tagging, and cleanup workflows.

- Improved retrieval recall and precision through iterative evaluation.

- Integrated with internal Gen-AI platform for unified access and governance.

- Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.




**Keywords**: RAG, Vector DB, Databricks, Data Pipeline, Embeddings



### AI Cloud Platform and UAP Common Library

_2020-11 - 2022-05_



Standardize ML project delivery and shared NLP libraries across new and legacy teams.




- Develop standardized ML project templates (AI Cloud Platform template; FastAPI, CI/CD, Kubernetes), reducing deployment time from 2 weeks to 3 days, adopted by 30+ projects.

- Implement NLP-focused Python library (UAP Common Library) with 70% internal adoption and 90%+ code coverage, improving productivity and reliability for AI developers.

- Lead automation of documentation pipelines via Sphinx and CI, enhancing onboarding efficiency and platform usability.




**Keywords**: FastAPI, CI/CD, Kubernetes, Sphinx



### Travel order analytics and itinerary features

_2019-12 - 2020-11_



Keep analytics stable and extract marketing and search features from order and itinerary data.




- Analyze customer order data using statistical modeling (FP-Growth, K-means, 4 clusters) to support marketing and segmentation strategies.

- Extract and optimize feature patterns from travel itineraries with CKIP NLP and frequent pattern mining, improving search relevance and user experience.




**Keywords**: FP-Growth, K-means, CKIP NLP, ETL



### Social data analysis applications

_2017-05 - 2017-11_



Turn raw social posts into interactive visualizations and partner reports.




- Develop full-stack web applications from end to end for social data analysis, supporting the transformation of raw posts into interactive word clouds and buzzword visualizations.

- Analyze and extract insights from social media data, applying NLP and visualization tools to generate actionable reports for industry partners.




**Keywords**: NLP, full-stack web


