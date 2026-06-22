"use client";

import { useState } from "react";
import { Loader2, Search, Play } from "lucide-react";
import { apiPost, type HybridRetrievalResult } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Callout } from "@/components/common/Callout";
import { CliEquivalent } from "@/components/common/CliEquivalent";
import { Tooltip } from "@/components/common/Tooltip";

export default function RetrievalPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState<number | "">("");
  const [graphLimit, setGraphLimit] = useState<number | "">("");
  const [results, setResults] = useState<HybridRetrievalResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cliEquivalent, setCliEquivalent] = useState<string>("");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiPost<{
        results: HybridRetrievalResult[];
        cli_equivalent: string;
      }>("/retrieval/hybrid", {
        query,
        top_k: topK || null,
        graph_limit: graphLimit || null,
      });
      setResults(data.results);
      setCliEquivalent(data.cli_equivalent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const curatedQueries = [
    "cross-border processing outside the EU subprocessors automated decision making retention",
    "high-impact workflow profiling automated decision support subprocessor cross-border transfer",
    "cross-border outside the EU outside the EEA international transfer safeguards",
  ];

  return (
    <div className="space-y-6">
      <PageIntro page="retrieval" />

      <div className="flex items-center gap-2">
        <Search className="h-5 w-5" />
        <h2 className="text-2xl font-bold">Retrieval & Query</h2>
      </div>

      {/* Query form */}
      <div className="rounded-md border p-4">
        <label className="mb-1 block text-sm font-medium">
          <Tooltip term="pgvector">Query text</Tooltip>
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your compliance query..."
          className="mb-3 w-full rounded-md border p-3 text-sm"
          rows={3}
        />

        <div className="mb-3 flex gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium">
              <Tooltip term="vector_top_k">Top K</Tooltip>
            </label>
            <input
              type="number"
              value={topK}
              onChange={(e) => setTopK(e.target.value ? Number(e.target.value) : "")}
              placeholder="5"
              className="w-24 rounded-md border p-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium">
              <Tooltip term="graph_result_limit">Graph Limit</Tooltip>
            </label>
            <input
              type="number"
              value={graphLimit}
              onChange={(e) => setGraphLimit(e.target.value ? Number(e.target.value) : "")}
              placeholder="25"
              className="w-24 rounded-md border p-2 text-sm"
            />
          </div>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Run Hybrid Retrieval
        </button>
      </div>

      {/* Curated query presets */}
      <div>
        <h3 className="mb-2 text-sm font-medium">Curated Query Presets</h3>
        <div className="space-y-1">
          {curatedQueries.map((q, i) => (
            <button
              key={i}
              onClick={() => setQuery(q)}
              className="block w-full rounded-md border p-2 text-left text-xs hover:bg-accent"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      )}

      {results.length > 0 && <Callout calloutId="hybrid_results" />}

      {/* Results table */}
      {results.length > 0 && (
        <div>
          <h3 className="mb-3 text-lg font-semibold">
            Results ({results.length})
          </h3>
          <div className="overflow-x-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-3 py-2 text-right">
                    <Tooltip term="priority_score">Priority</Tooltip>
                  </th>
                  <th className="px-3 py-2 text-left">Vendor</th>
                  <th className="px-3 py-2 text-left">Software</th>
                  <th className="px-3 py-2 text-right">Annual Cost</th>
                  <th className="px-3 py-2 text-left">Risk</th>
                  <th className="px-3 py-2 text-left">Action</th>
                  <th className="px-3 py-2 text-left">
                    <Tooltip term="matched_sources">Sources</Tooltip>
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2 text-right font-mono text-xs">
                      {r.priority_score.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 font-medium">{r.vendor_name}</td>
                    <td className="px-3 py-2">{r.software_name}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {r.annual_cost_usd ? `$${r.annual_cost_usd.toLocaleString()}` : "N/A"}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      {r.risk_category || "UNKNOWN"} / {r.risk_severity || "UNKNOWN"}
                    </td>
                    <td className="px-3 py-2 text-xs">{r.recommended_review_action}</td>
                    <td className="px-3 py-2 text-xs">
                      {r.matched_sources.join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Evidence excerpts */}
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-medium">Evidence Excerpts</h4>
            <div className="space-y-2">
              {results.map((r, i) => (
                r.evidence_excerpt && (
                  <div key={i} className="rounded-md border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      {r.vendor_name} — {r.source_document}
                    </p>
                    <p className="mt-1 text-sm">{r.evidence_excerpt}</p>
                  </div>
                )
              ))}
            </div>
          </div>

          {cliEquivalent && <CliEquivalent command={cliEquivalent} />}
        </div>
      )}
    </div>
  );
}
