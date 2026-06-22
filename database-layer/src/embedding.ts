export const EMBEDDING_DIMENSION = Number(process.env.EMBEDDING_DIMENSION ?? 8);
export const EMBEDDING_PROVIDER = process.env.EMBEDDING_PROVIDER ?? "placeholder";
export const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL ?? "deterministic-placeholder";
export const FOUNDRY_LOCAL_ENDPOINT = process.env.FOUNDRY_LOCAL_ENDPOINT ?? "";
export const OPENAI_API_KEY = process.env.OPENAI_API_KEY ?? "";
export const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL ?? "https://api.openai.com/v1";

export function createDeterministicEmbedding(input: string): number[] {
  const vector = new Array<number>(EMBEDDING_DIMENSION).fill(0);

  for (let index = 0; index < input.length; index += 1) {
    const slot = index % EMBEDDING_DIMENSION;
    vector[slot] += input.charCodeAt(index) * 0.001;
  }

  return vector.map((value, index) => Number((value / (index + 1)).toFixed(6)));
}

export function toPgvectorLiteral(values: number[]): string {
  return `[${values.map((value) => Number(value).toFixed(6)).join(",")}]`;
}

/**
 * Create an embedding vector using the configured provider.
 *
 * Falls back to deterministic placeholder embeddings when the provider is
 * "placeholder" or when no API key / endpoint is configured.
 */
export async function createEmbedding(input: string): Promise<number[]> {
  const provider = EMBEDDING_PROVIDER.toLowerCase();

  if (provider === "openai" && OPENAI_API_KEY) {
    return createOpenAIEmbedding(input, OPENAI_API_KEY, EMBEDDING_MODEL, OPENAI_BASE_URL);
  }

  if (provider === "microsoft-foundry-local" && FOUNDRY_LOCAL_ENDPOINT) {
    return createFoundryLocalEmbedding(input, FOUNDRY_LOCAL_ENDPOINT, EMBEDDING_MODEL);
  }

  return createDeterministicEmbedding(input);
}

async function createOpenAIEmbedding(
  input: string,
  apiKey: string,
  model: string,
  baseUrl: string,
): Promise<number[]> {
  const response = await fetch(`${baseUrl}/embeddings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model, input }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI embeddings API error: ${response.status} ${response.statusText}`);
  }

  const payload = (await response.json()) as { data: Array<{ embedding: number[] }> };
  return payload.data[0].embedding;
}

async function createFoundryLocalEmbedding(
  input: string,
  endpoint: string,
  model: string,
): Promise<number[]> {
  const baseUrl = endpoint.replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/v1/embeddings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer local",
    },
    body: JSON.stringify({ model, input }),
  });

  if (!response.ok) {
    throw new Error(
      `Foundry Local embeddings API error: ${response.status} ${response.statusText}`,
    );
  }

  const payload = (await response.json()) as { data: Array<{ embedding: number[] }> };
  return payload.data[0].embedding;
}
