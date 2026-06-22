"use client";

import { useState, useEffect } from "react";
import { Loader2, Database } from "lucide-react";
import { apiGet, type Vendor, type Subscription, type PricingRecord } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";

export default function DataPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [pricing, setPricing] = useState<PricingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"vendors" | "subscriptions" | "pricing">("vendors");

  useEffect(() => {
    Promise.all([
      apiGet<{ vendors: Vendor[] }>("/data/vendors").catch(() => ({ vendors: [] })),
      apiGet<{ subscriptions: Subscription[] }>("/data/subscriptions").catch(() => ({ subscriptions: [] })),
      apiGet<{ pricing: PricingRecord[] }>("/data/pricing").catch(() => ({ pricing: [] })),
    ])
      .then(([v, s, p]) => {
        setVendors(v.vendors);
        setSubscriptions(s.subscriptions);
        setPricing(p.pricing);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading data...
      </div>
    );

  return (
    <div className="space-y-6">
      <PageIntro page="data" />

      <div className="flex items-center gap-2">
        <Database className="h-5 w-5" />
        <h2 className="text-2xl font-bold">Data & Components</h2>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {(["vendors", "subscriptions", "pricing"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`border-b-2 px-4 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab} ({tab === "vendors" ? vendors.length : tab === "subscriptions" ? subscriptions.length : pricing.length})
          </button>
        ))}
      </div>

      {/* Vendors table */}
      {activeTab === "vendors" && (
        <div className="overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left">Vendor Code</th>
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">Country</th>
                <th className="px-4 py-2 text-left">AI Risk Tier</th>
                <th className="px-4 py-2 text-left">AI Processing Posture</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((v) => (
                <tr key={v.vendorCode} className="border-t">
                  <td className="px-4 py-2 font-mono text-xs">{v.vendorCode}</td>
                  <td className="px-4 py-2 font-medium">{v.name}</td>
                  <td className="px-4 py-2">{v.country}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                      v.aiRiskTier === "HIGH" ? "bg-red-100 text-red-800" :
                      v.aiRiskTier === "MEDIUM" ? "bg-yellow-100 text-yellow-800" :
                      "bg-green-100 text-green-800"
                    }`}>
                      {v.aiRiskTier}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs">{v.aiProcessingPosture}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Subscriptions table */}
      {activeTab === "subscriptions" && (
        <div className="overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left">Subscription</th>
                <th className="px-4 py-2 text-left">Vendor</th>
                <th className="px-4 py-2 text-right">Annual Cost (USD)</th>
                <th className="px-4 py-2 text-left">Renewal Date</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Owner</th>
              </tr>
            </thead>
            <tbody>
              {subscriptions.map((s) => (
                <tr key={s.subscriptionCode} className="border-t">
                  <td className="px-4 py-2 font-mono text-xs">{s.subscriptionCode}</td>
                  <td className="px-4 py-2">{s.vendorCode}</td>
                  <td className="px-4 py-2 text-right font-mono">${s.annualCostUsd.toLocaleString()}</td>
                  <td className="px-4 py-2">{s.renewalDate}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                      s.status === "ACTIVE" ? "bg-green-100 text-green-800" :
                      s.status === "PENDING_RENEWAL" ? "bg-yellow-100 text-yellow-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs">{s.owner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pricing table */}
      {activeTab === "pricing" && (
        <div className="overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left">Vendor</th>
                <th className="px-4 py-2 text-left">Software</th>
                <th className="px-4 py-2 text-right">Annual Unit Price</th>
                <th className="px-4 py-2 text-right">Min Seats</th>
                <th className="px-4 py-2 text-left">Data Residency</th>
                <th className="px-4 py-2 text-left">Support Tier</th>
              </tr>
            </thead>
            <tbody>
              {pricing.map((p) => (
                <tr key={p.software_code} className="border-t">
                  <td className="px-4 py-2 font-medium">{p.vendor_name}</td>
                  <td className="px-4 py-2">{p.software_name}</td>
                  <td className="px-4 py-2 text-right font-mono">${p.annual_unit_price_usd}</td>
                  <td className="px-4 py-2 text-right">{p.minimum_seats}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded px-2 py-0.5 text-xs ${
                      p.data_residency_available ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    }`}>
                      {p.data_residency_available ? "Available" : "Not Available"}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs">{p.included_support_tier}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
