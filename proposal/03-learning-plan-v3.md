# The Enterprise AI Compliance Analyzer Implementation Roadmap

Here is the finalized, comprehensive Learning Plan for the **Enterprise Software & AI Compliance Analyzer**, which reflects our decision to stick with the type-safe, Prisma-native approach (Setup Plan V3). This sequence guarantees that your synthetic data generation perfectly maps to your TypeScript environment after the schemas are defined.

# 0 Pre-Requisite: Monorepo Initialization

## Task 0.1: Initialize the GitHub Monorepo

* Create a single GitHub repository to house your entire architecture\.  
* Set up three core folders: [`/database-layer`](../database-layer/) (for your TypeScript/Prisma ORM setup), [`/agent-brain`](../agent-brain/) (for your Python orchestrators, Jupyter Notebooks, and LlamaIndex/LangGraph code), and [`/mock-pricing-api`](../mock-pricing-api/) (for your lightweight FastAPI/Flask server)\. Also set up [`/plans`](../plans/) to track planned changes in date-time versioned md files. Finally add [`/docs`](../docs/) for user documentation\.

# Phase 1: Local Data Foundations & Zero-ETL Architecture (May 31 \- June 2\)

**Goal**: Build a robust, type-safe data access layer that supports simultaneous agent reads/writes without database locking.

## Task 1.1: Visual Database Design

* Open **Luna Modeler** or similar tool to visually map out your relational data layer and Entity-Relationship (ER) diagrams for your subscriptions, vendors, and software tables\.

## Task 2.2: Docker Data Infrastructure

* Open your WSL2 Linux terminal and deploy a **PostgreSQL** Docker container with the **pgvector** extension enabled through [`docker-compose.yml`](../docker-compose.yml) to achieve a "Zero-ETL Retrieval" architecture\.

## Task 1.3: Prisma ORM & TypeScript Setup

* Navigate to your [`/database-layer`](../database-layer/) folder to initialize a Node/TypeScript environment and install **Prisma ORM**\. Translate your Luna Modeler design into your Prisma schema in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma) (including a pgvector column for SLA document embeddings), which will generate strict TypeScript types to act as a guardrail against agent hallucinations\.

## Task 1.4: Synthetic Data Generation (JSON)

* Now that the schema is locked in, use a local LLM to generate a **JSON file** such as [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) containing mock AI corporate subscriptions where the keys perfectly match your Prisma schema columns\. Simultaneously, generate 5-10 fake text files in [`database-layer/data/documents/`](../database-layer/data/documents/) representing vendor SLAs and GDPR policies\.

## Task 1.5: Data Ingestion

* Write a TypeScript script such as [`database-layer/scripts/ingest.ts`](../database-layer/scripts/ingest.ts) using Prisma Client to parse your JSON data into Postgres, embed your synthetic SLA documents, and save those vectors to the pgvector column\. Run a concurrent script such as [`database-layer/scripts/validate-concurrency.ts`](../database-layer/scripts/validate-concurrency.ts) to verify Postgres handles simultaneous read/writes flawlessly\.

# Phase 2: Local Hybrid Context Architecture (June 3 \- June 5\)

***Goal**: Connect structured billing data with unstructured compliance text to answer complex enterprise queries.*

## Task 2.1: Graph Database Deployment 

* In your WSL2 terminal, deploy a local **Neo4j** Docker container through [`docker-compose.yml`](../docker-compose.yml)\.

## Task 2.2: Knowledge Graph Mapping

* Define the nodes (Vendor, Software, Subscription, DocumentChunk) and map their relationships (e.g., \[Vendor\] \-SELLS-\> \[Software\]) in Neo4j\.

## Task 2.3: Hybrid Retrieval Pipeline

* Navigate to your [`/agent-brain`](../agent-brain/) folder and create a Jupyter Notebook such as [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb)\. Write a Python pipeline using **LlamaIndex** and **LangChain** to code a hybrid retrieval function such as [`agent-brain/src/agent_brain/retrieval/hybrid.py`](../agent-brain/src/agent_brain/retrieval/hybrid.py) that simultaneously traverses the Neo4j graph and queries your Postgres pgvector embeddings\.

# Phase 3: Agentic Coding, Orchestration & Mock Tool Use (June 6 \- June 8\)

***Goal**: Build the multi-agent reasoning engine that autonomously uses tools and pauses for human oversight.*

## Task 3.1: Visual API Design

* Use **Galaxy Modeler** or similar tool to map out a strongly typed GraphQL schema for the external mock pricing API, which reduces LLM hallucinations and improves tool-calling reliability\.

## Task 3.2: The Mock API Setup

* In your [`/mock-pricing-api`](../mock-pricing-api/) folder, build a Python web server such as [`mock-pricing-api/src/mock_pricing_api/app.py`](../mock-pricing-api/src/mock_pricing_api/app.py) using FastAPI or Flask, running on localhost:8000, that serves your synthetic software pricing JSON from [`mock-pricing-api/src/mock_pricing_api/data/pricing.json`](../mock-pricing-api/src/mock_pricing_api/data/pricing.json)\.

## Task 3.3: Agent SDK & Orchestration

* In your [`/agent-brain`](../agent-brain/) folder, implement the **OpenAI Agents SDK** for task decomposition and wrap your workflow in **LangGraph** to manage hierarchical coordination and state memory in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py)\.

## Task 3.4: Tool Use & Human Oversight

* Implement the **Model Context Protocol (MCP)** using Anthropic's specification\. Write the Python logic in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) allowing your LangGraph agent to autonomously ping your mock GraphQL API, and program an explicit pause for **Human Oversight Controls (HITL)** in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) requiring manual approval before the agent finalizes any "cancellation recommendation"\.

# Phase 4: Microsoft Integration, Governance & FinOps (June 9 \- June 10\)

***Goal**: Prove your local prototype can scale into a governed, observable, and cost-effective enterprise pattern.*

## Task 4.1: Local Reasoning Engine Setup

* Download and install **Microsoft Foundry Local** to run an open-source AI model directly on your Windows machine, acting as the "brain" for your LangGraph agents with zero cloud dependency\.

## Task 4.2: Agentic Observability

* Connect your LangGraph workflow to **Arize Phoenix** through [`agent-brain/src/agent_brain/governance/observability.py`](../agent-brain/src/agent_brain/governance/observability.py)\. Configure it to log the trace\_id and a boolean safety\_flag (mirroring Azure AI Content Safety protocols) to capture step-by-step reasoning traces\.

## Task 4.3: Token Economics Integration

* Integrate **Langfuse** into your workflow through [`agent-brain/src/agent_brain/governance/observability.py`](../agent-brain/src/agent_brain/governance/observability.py) to track simulated token consumption across your local Foundry model to fulfill your FinOps requirements\.
