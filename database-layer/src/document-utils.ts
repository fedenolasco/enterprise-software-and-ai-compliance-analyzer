import { readFile } from "node:fs/promises";
import path from "node:path";

export type ChunkRecord = {
  chunkIndex: number;
  chunkText: string;
  tokenCount: number;
};

export async function readTextFile(filePath: string): Promise<string> {
  return readFile(filePath, "utf8");
}

export function chunkText(content: string, maxCharacters = 500): ChunkRecord[] {
  const normalized = content.replace(/\r\n/g, "\n").trim();
  const paragraphs = normalized.split(/\n\s*\n/g).map((value) => value.trim()).filter(Boolean);
  const chunks: ChunkRecord[] = [];
  let buffer = "";
  let chunkIndex = 0;

  for (const paragraph of paragraphs) {
    const candidate = buffer ? `${buffer}\n\n${paragraph}` : paragraph;

    if (candidate.length > maxCharacters && buffer) {
      chunks.push({ chunkIndex, chunkText: buffer, tokenCount: estimateTokenCount(buffer) });
      chunkIndex += 1;
      buffer = paragraph;
      continue;
    }

    buffer = candidate;
  }

  if (buffer) {
    chunks.push({ chunkIndex, chunkText: buffer, tokenCount: estimateTokenCount(buffer) });
  }

  return chunks;
}

export function inferRisk(content: string) {
  const lower = content.toLowerCase();

  if (lower.includes("outside the eu") || lower.includes("cross-border")) {
    return {
      category: "DATA_RESIDENCY",
      severity: "HIGH",
      score: 0.82,
      summary: "Potential cross-border processing or non-EU hosting commitment detected."
    } as const;
  }

  if (lower.includes("subprocessor") || lower.includes("third-party model")) {
    return {
      category: "SUBPROCESSOR_RISK",
      severity: "HIGH",
      score: 0.78,
      summary: "Subprocessor or third-party model dependency requires governance review."
    } as const;
  }

  if (lower.includes("automated decision") || lower.includes("profiling")) {
    return {
      category: "AUTOMATED_DECISION_MAKING",
      severity: "CRITICAL",
      score: 0.91,
      summary: "Automated decision-making language indicates elevated compliance exposure."
    } as const;
  }

  if (lower.includes("retention") || lower.includes("delete") || lower.includes("erasure")) {
    return {
      category: "DATA_RETENTION",
      severity: "MEDIUM",
      score: 0.62,
      summary: "Data retention or erasure commitments should be validated."
    } as const;
  }

  return {
    category: "SECURITY_CONTROLS",
    severity: "LOW",
    score: 0.28,
    summary: "General compliance evidence chunk stored for retrieval and review."
  } as const;
}

export function resolveDataPath(...segments: string[]): string {
  return path.resolve(process.cwd(), "data", ...segments);
}

function estimateTokenCount(value: string): number {
  return Math.ceil(value.split(/\s+/).filter(Boolean).length * 1.2);
}
