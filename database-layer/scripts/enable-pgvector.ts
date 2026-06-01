import "dotenv/config";
import { Client } from "pg";

async function main() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  await client.query("CREATE EXTENSION IF NOT EXISTS vector;");
  await client.end();
  console.log("pgvector extension enabled");
}

main().catch((error) => {
  console.error("Failed to enable pgvector", error);
  process.exit(1);
});
