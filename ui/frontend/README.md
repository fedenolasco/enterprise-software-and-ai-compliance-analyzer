# Compliance Analyzer UI Frontend

Next.js frontend for the Enterprise Software & AI Compliance Analyzer.

## Overview

This frontend provides a polished, user-friendly interface for the compliance analyzer, with:

- Dashboard with service health monitoring
- Configuration display with provider status
- Data browsing (vendors, subscriptions, pricing)
- Hybrid retrieval query interface
- LangGraph workflow execution with HITL approval
- Observability dashboard with provider comparison
- CLI command launcher
- 6-layer educational guidance system with user preferences

## Setup

```bash
cd ui/frontend
npm install
```

## Run

```bash
npm run dev
```

The UI will be available at `http://localhost:3000`.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:3001` | URL of the UI API backend |

## Build

```bash
npm run build
npm start
```

## Architecture

- **Framework:** Next.js 15 with App Router
- **Styling:** Tailwind CSS with shadcn/ui-inspired components
- **Icons:** lucide-react
- **Data tables:** @tanstack/react-table
- **Workflow visualization:** @xyflow/react (react-flow)
- **Guidance system:** Centralized content in `src/lib/guidance.ts` with localStorage-based preferences
