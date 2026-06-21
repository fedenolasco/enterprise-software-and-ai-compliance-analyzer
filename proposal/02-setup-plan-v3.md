# Enterprise Software & AI Compliance Analyzer Setup Roadmap

Here is your fully detailed, chronological setup plan for the **Enterprise Software & AI Compliance Analyzer**.  
This sequence ensures that data generation only happens *after* the schemas are strictly defined, and standardizes on JSON to perfectly map to the TypeScript environment. We use this task list to track main tasks progress step-by-step.

# 0 Pre-Requisite: Monorepo Initialization

## Task 0.1: Initialize the GitHub Monorepo

* Create a single GitHub repository to house your entire architecture\.  
* Set up the following core folder structure 1:  
* [`/database-layer`](../database-layer/) (For TypeScript/Prisma ORM setup)  
* [`/agent-brain`](../agent-brain/) (For Python orchestrators, Jupyter Notebooks, and LlamaIndex/LangGraph code)  
* [`/mock-pricing-api`](../mock-pricing-api/) (For lightweight FastAPI/Flask server)

# Phase 1: Local Data Foundations & Zero-ETL Architecture (May 31 \- June 2\)

***Goal**: Build a robust, type-safe data access layer that supports simultaneous agent reads/writes without database locking.*

## Task 1.1: Visual Database Design

* Open **Luna Modeler** or similar tool to visually map out your relational data layer\.  
* Design the Entity-Relationship (ER) diagrams for your subscriptions, vendors, and software tables, defining all primary and foreign keys\. This gives you the physical blueprint before writing ORM code\.

## Task 1.2: Docker Data Infrastructure

* Open your WSL2 Linux terminal and deploy a **PostgreSQL** Docker container\.  
* Enable the **pgvector** extension to achieve the "Zero-ETL Retrieval" architecture, which allows you to store both relational billing data and vectorized document chunks in the exact same database\.

## Task 1.3: Prisma ORM & TypeScript Setup

* Navigate to your [`/database-layer`](../database-layer/) folder and initialize a Node/TypeScript environment\.  
* Install **Prisma ORM**\.  
* Translate your Luna Modeler design into your Prisma schema in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma), ensuring you include a pgvector column for your SLA document embeddings\. This generates strict TypeScript types, acting as a guardrail against agent hallucinations\.

## Task 1.4: Synthetic Data Generation (JSON)

* *Now that the schema is locked in*, prompt a local LLM to generate a **JSON file** such as [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) containing mock AI corporate subscriptions (vendors, costs, seats)\. Instruct the LLM to ensure the JSON keys perfectly match your newly defined Prisma schema columns.  
* Simultaneously, generate 5-10 fake text files in [`database-layer/data/documents/`](../database-layer/data/documents/) representing vendor SLAs and GDPR policies\.

## Task 1.5: Data Ingestion

* Write a TypeScript script such as [`database-layer/scripts/ingest.ts`](../database-layer/scripts/ingest.ts) using Prisma Client to parse your structured JSON data into your Postgres tables\.  
* Embed your synthetic SLA documents and save those vectors to the pgvector column alongside the relational billing records\. Run a concurrent script such as [`database-layer/scripts/validate-concurrency.ts`](../database-layer/scripts/validate-concurrency.ts) to verify Postgres handles simultaneous read/writes flawlessly\.

# Phase 2: Local Hybrid Context Architecture (June 3 \- June 5\)

***Goal**: Connect structured billing data with unstructured compliance text to answer complex enterprise queries.*

## Task 2.1: Graph Database Deployment

* In your WSL2 terminal, deploy a local **Neo4j** Docker container\.

## Task 2.2: Knowledge Graph Mapping

* Define the nodes (Vendor, Software, Subscription, DocumentChunk) in Neo4j\.  
* Map the relationships linking your structured and unstructured data (e.g., \[Vendor\] \-SELLS-\> \[Software\], \[Vendor\] \-HAS\_POLICY-\> \[DocumentChunk\])\.

## Task 2.3: Hybrid Retrieval Pipeline

* Navigate to your [`/agent-brain`](../agent-brain/) folder and create a Jupyter Notebook such as [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb)\.  
* Use **LlamaIndex** and **LangChain** to write a Python pipeline\.  
* Code a hybrid retrieval function such as [`agent-brain/src/agent_brain/retrieval/hybrid.py`](../agent-brain/src/agent_brain/retrieval/hybrid.py) that traverses the Neo4j graph and simultaneously queries your Postgres pgvector embeddings to pull risk-flagged documents and their associated financial costs\.

# Phase 3: Agentic Coding, Orchestration & Mock Tool Use (June 6 \- June 8\)

***Goal**: Build the multi-agent reasoning engine that autonomously uses tools and pauses for human oversight.*

## Task 3.1: Visual API Design

* Use **Galaxy Modeler** or similar tool to visually map out a strongly typed GraphQL schema for the external mock pricing API\. This predictable structure will drastically reduce LLM hallucinations and improve tool-calling reliability\.  
* Export these API architecture diagrams as PDF or HTML reports for your project documentation in [`docs/`](../docs/)\.

## Task 3.2: The Mock API Setup

* Navigate to your [`/mock-pricing-api`](../mock-pricing-api/) folder\.  
* Build a lightweight Python web server such as [`mock-pricing-api/src/mock_pricing_api/app.py`](../mock-pricing-api/src/mock_pricing_api/app.py) using FastAPI or Flask, running on localhost:8000, that serves your synthetic software pricing JSON from [`mock-pricing-api/src/mock_pricing_api/data/pricing.json`](../mock-pricing-api/src/mock_pricing_api/data/pricing.json)\.

## Task 3.3: Agent SDK & Orchestration

* In your [`/agent-brain`](../agent-brain/) folder, implement the **OpenAI Agents SDK** for task decomposition\.  
* Wrap your workflow in **LangGraph** to manage hierarchical coordination and state memory in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py) (tracking the user\_query, compliance\_risks, live\_pricing, and human\_approval\_status)\.

## Task 3.4: Tool Use & Human Oversight

* Implement the **Model Context Protocol (MCP)** using Anthropic's specification\.  
* Write the Python logic in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) allowing your LangGraph agent to autonomously ping your mock GraphQL API to fetch pricing data\.  
* Program an explicit pause in the LangGraph execution flow for **Human Oversight Controls (HITL)** in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py), requiring manual approval before the agent can finalize any "cancellation recommendation"\.

# Phase 4: Microsoft Integration, Governance & FinOps (June 9 \- June 10\)

***Goal**: Prove your local prototype can scale into a governed, observable, and cost-effective enterprise pattern.*

## Task 4.1: Local Reasoning Engine Setup

* Download and install **Microsoft Foundry Local**\.  
* Run an open-source AI model directly on your Windows machine via this console application to act as the "brain" for your LangGraph agents, achieving zero cloud dependency\.

## Task 4.2: Agentic Observability

* Connect your LangGraph workflow to **Arize Phoenix** through [`agent-brain/src/agent_brain/governance/observability.py`](../agent-brain/src/agent_brain/governance/observability.py)\.  
* Configure it to log the trace\_id and a boolean safety\_flag (mirroring Azure AI Content Safety protocols), capturing step-by-step reasoning traces and evaluating the agent's logic for failure patterns\.

## Task 4.3: Token Economics Integration

* Integrate **Langfuse** into your workflow through [`agent-brain/src/agent_brain/governance/observability.py`](../agent-brain/src/agent_brain/governance/observability.py) to track simulated token consumption across your local Foundry model\.  
* Log the token\_usage and simulated cost to fulfill your FinOps requirements and prove the financial viability of your AI system\.
