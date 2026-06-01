# Database Layer

TypeScript and Prisma workstream for relational subscription data, compliance document chunks, pgvector storage, ingestion, and concurrency validation.

## Scripts

- `npm run db:generate` — generate the Prisma client.
- `npm run db:push` — push the Prisma schema to PostgreSQL.
- `npm run db:enable-vector` — enable the PostgreSQL `vector` extension.
- `npm run ingest` — load synthetic subscription and document data.
- `npm run validate:concurrency` — run simultaneous reads and optimistic writes.

## Data fixtures

- `data/subscriptions.json`
- `data/documents/*.txt`

## Suggested bootstrap sequence

1. Copy [`database-layer/.env.example`](./.env.example) to `.env`.
2. Start PostgreSQL with [`docker-compose.yml`](../docker-compose.yml).
3. Run `npm install`.
4. Run `npm run db:generate`.
5. Run `npm run db:push`.
6. Run `npm run db:enable-vector`.
7. Run `npm run ingest`.
8. Run `npm run validate:concurrency`.
