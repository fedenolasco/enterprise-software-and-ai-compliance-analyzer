

# High-Level Plan: Enterprise Software & AI Compliance Analyzer

# High-Level Goal

To architect and deploy a 100% local, concurrency-safe, and highly observable multi-agent reasoning system capable of analyzing enterprise software subscriptions and their associated AI compliance risks\. The architecture will securely bridge structured relational data with unstructured text using a "Zero-ETL" approach, all orchestrated without any cloud dependencies\.

# Strategic Intent

The intent of this project is to prove the viability of a governed, enterprise-grade AI architecture that perfectly aligns with strict compliance frameworks (such as the EU AI Act) and FinOps principles\. By utilizing synthetic data and local tools, the system will demonstrate robust operational realism, ensuring zero-cost local prototyping, strict type-safety to prevent LLM hallucinations, and mandatory human-in-the-loop (HITL) oversight before the AI takes action.

# Project Implementation Roadmap
Please use the following roadmap for a high-level view and use the detailed project implementation setup from [`proposal/02-setup-plan-v3.md`](02-setup-plan-v3.md). 

## Pre-Requisite: Architecture Initialization

* **Action:** Establish a centralized GitHub monorepo to house the entire infrastructure, partitioned into three core workstreams: [`database-layer/`](../database-layer/) (TypeScript/Prisma ORM), [`agent-brain/`](../agent-brain/) (Python/LangGraph), and [`mock-pricing-api/`](../mock-pricing-api/) (Python/FastAPI)\.
* **Runnable capability:** Not runnable as an application phase yet; this phase makes the repository navigable and prepares the local execution boundaries.
* **Expected outcome:** The user can inspect the repository layout, understand which folder owns each workstream, and confirm that later runnable phases have a stable place to live.

## Phase 1: Local Data Foundations & Zero-ETL Architecture

* **Objective:** Build a type-safe data access layer that prevents concurrent locking issues and unified storage\.  
* **Key Components:** Use **Luna Modeler** or similar for visual relational design\. Deploy **PostgreSQL** locally via Docker, leveraging the **pgvector** extension to store structured subscription records and vectorized compliance SLAs in the exact same database\. Secure the application layer with **Prisma ORM** in a TypeScript environment to guarantee strict type safety, followed by targeted synthetic data ingestion\.
* **Runnable capability:** Runnable locally as the data foundation. The user can start the Docker database services, validate Prisma schema generation, ingest synthetic subscription and policy data, and run concurrency checks from [`database-layer/`](../database-layer/).
* **Expected outcome:** PostgreSQL contains structured software subscription records, compliance documents, vector-ready document chunks, risk records, and audit events. The user can demonstrate that the local database accepts repeatable ingestion and concurrent reads/writes without relying on cloud services.

## Phase 2: Local Hybrid Context Architecture

* **Objective:** Enable the system to answer complex, interconnected enterprise queries by blending Baseline RAG with GraphRAG\.  
* **Key Components:** Deploy a local **Neo4j** Docker container to establish a Knowledge Graph\. Use **LlamaIndex** and **LangChain** to build a hybrid retrieval pipeline that queries the Neo4j graph and PostgreSQL vectors simultaneously, linking specific compliance risks to precise financial costs\.
* **Runnable capability:** Runnable locally as a retrieval demo from [`agent-brain/`](../agent-brain/). The user can execute curated hybrid retrieval queries that combine PostgreSQL vector context with Neo4j graph relationships.
* **Expected outcome:** The user can demonstrate risk-to-cost retrieval: vendors, subscriptions, renewal exposure, compliance evidence, and risk categories appear together in deterministic query results aligned to the curated query scope.

## Phase 3: Agentic Coding, Orchestration & Mock Tool Use

* **Objective:** Construct the multi-agent reasoning engine that autonomously uses tools and strictly enforces compliance protocols\.  
* **Key Components:** Visually design a strictly typed GraphQL interface using **Galaxy Modeler** or similar design tool and deploy a local mock pricing API\. Utilize the **OpenAI Agents SDK** and **LangGraph** for hierarchical coordination\. Implement the **Model Context Protocol (MCP)** to allow agents to fetch live pricing data, while hard-coding an explicit pause for **Human Oversight Controls (HITL)** before finalizing vendor cancellation recommendations\.
* **Runnable capability:** Runnable locally as an agent workflow demonstration. The user can start [`mock-pricing-api/`](../mock-pricing-api/), run the orchestration flow in [`agent-brain/`](../agent-brain/), fetch mock pricing data, draft a recommendation, and observe the mandatory HITL pause before finalization.
* **Expected outcome:** The user can demonstrate that the system can retrieve evidence, call a local pricing tool, produce a recommendation draft, and block final cancellation or renewal decisions until human approval is supplied.

## Phase 4: Microsoft Integration, Governance & FinOps

* **Objective:** Scale the prototype into a fully observable, cost-effective pattern that ensures high-risk AI governance\.  
* **Key Components:** Transition the agent's core reasoning engine to **Microsoft Foundry Local** to execute open-source AI models directly on a Windows machine\. Connect the workflow to **Arize Phoenix** to monitor step-by-step reasoning traces and safety flags, and integrate **Langfuse** to perform token economics and FinOps cost tracking\.
* **Runnable capability:** Runnable locally as a governance and observability demonstration, with optional local observability services. The user can run workflows with local model-adapter boundaries, audit persistence, safety flag logging, Phoenix-compatible trace hooks, and Langfuse-compatible token/cost telemetry.
* **Expected outcome:** The user can demonstrate a governed local AI workflow that records trace identifiers, safety decisions, simulated token usage, simulated cost, and audit events, proving that compliance and FinOps evidence is available without mandatory cloud dependencies.
