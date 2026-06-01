

# High-Level Plan: Enterprise Software & AI Compliance Analyzer

# High-Level Goal

To architect and deploy a 100% local, concurrency-safe, and highly observable multi-agent reasoning system capable of analyzing enterprise software subscriptions and their associated AI compliance risks 1\. The architecture will securely bridge structured relational data with unstructured text using a "Zero-ETL" approach, all orchestrated without any cloud dependencies 2\.

# Strategic Intent

The intent of this project is to prove the viability of a governed, enterprise-grade AI architecture that perfectly aligns with strict compliance frameworks (such as the EU AI Act) and FinOps principles 1\. By utilizing synthetic data and local tools, the system will demonstrate robust operational realism, ensuring zero-cost local prototyping, strict type-safety to prevent LLM hallucinations, and mandatory human-in-the-loop (HITL) oversight before the AI takes action 2-4.

# Project Implementation Roadmap
Please use the following roadmap for a high-level view and use the detailed project implementation setup from "/proposal/setup-plan-v3.md". 

## Pre-Requisite: Architecture Initialization

* **Action:** Establish a centralized GitHub monorepo to house the entire infrastructure, partitioned into three core workstreams: /database-layer (TypeScript/Prisma ORM), /agent-brain (Python/LangGraph), and /mock-pricing-api (Python/FastAPI) 5, 6\.

## Phase 1: Local Data Foundations & Zero-ETL Architecture

* **Objective:** Build a type-safe data access layer that prevents concurrent locking issues and unified storage 2\.  
* **Key Components:** Use **Luna Modeler** for visual relational design 2\. Deploy **PostgreSQL** locally via Docker, leveraging the **pgvector** extension to store structured subscription records and vectorized compliance SLAs in the exact same database 2, 7\. Secure the application layer with **Prisma ORM** in a TypeScript environment to guarantee strict type safety, followed by targeted synthetic data ingestion 2, 7\.

## Phase 2: Local Hybrid Context Architecture

* **Objective:** Enable the system to answer complex, interconnected enterprise queries by blending Baseline RAG with GraphRAG 8, 9\.  
* **Key Components:** Deploy a local **Neo4j** Docker container to establish a Knowledge Graph 9\. Use **LlamaIndex** and **LangChain** to build a hybrid retrieval pipeline that queries the Neo4j graph and PostgreSQL vectors simultaneously, linking specific compliance risks to precise financial costs 8, 9\.

## Phase 3: Agentic Coding, Orchestration & Mock Tool Use

* **Objective:** Construct the multi-agent reasoning engine that autonomously uses tools and strictly enforces compliance protocols 3\.  
* **Key Components:** Visually design a strictly typed GraphQL interface using **Galaxy Modeler** and deploy a local mock pricing API 3, 10\. Utilize the **OpenAI Agents SDK** and **LangGraph** for hierarchical coordination 3\. Implement the **Model Context Protocol (MCP)** to allow agents to fetch live pricing data, while hard-coding an explicit pause for **Human Oversight Controls (HITL)** before finalizing vendor cancellation recommendations 3, 10\.

## Phase 4: Microsoft Integration, Governance & FinOps

* **Objective:** Scale the prototype into a fully observable, cost-effective pattern that ensures high-risk AI governance 4, 11\.  
* **Key Components:** Transition the agent's core reasoning engine to **Microsoft Foundry Local** to execute open-source AI models directly on a Windows machine 4, 11\. Connect the workflow to **Arize Phoenix** to monitor step-by-step reasoning traces and safety flags, and integrate **Langfuse** to perform token economics and FinOps cost tracking 4, 11\.

