export const EMBEDDING_DIMENSION = Number(process.env.EMBEDDING_DIMENSION ?? 8);

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
