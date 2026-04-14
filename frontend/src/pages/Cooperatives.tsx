import { useEffect, useState } from "react";
import {
  getCooperatives,
  getCooperativeAggregated,
  optimizeCooperative,
} from "../services/api";
import type { Cooperative, CooperativeAggregated } from "../types";
import { useI18n } from "../i18n";

export default function Cooperatives() {
  const { t } = useI18n();
  const [coops, setCoops] = useState<Cooperative[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [aggregated, setAggregated] = useState<CooperativeAggregated | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeResult, setOptimizeResult] = useState<unknown>(null);

  useEffect(() => {
    getCooperatives()
      .then((r) => {
        setCoops(r.data);
        if (r.data.length > 0) setSelectedId(r.data[0].id);
      })
      .catch((e) => setError(e?.response?.data?.detail?.message || t.common.error))
      .finally(() => setLoading(false));
  }, [t.common.error]);

  useEffect(() => {
    if (!selectedId) return;
    setAggregated(null);
    getCooperativeAggregated(selectedId)
      .then((r) => setAggregated(r.data))
      .catch(() => setAggregated(null));
  }, [selectedId]);

  const runOptimize = async () => {
    if (!selectedId) return;
    setOptimizing(true);
    setOptimizeResult(null);
    try {
      const res = await optimizeCooperative(selectedId);
      setOptimizeResult(res.data);
    } catch (e: any) {
      setOptimizeResult({ error: e?.response?.data?.detail || "Failed" });
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) return <div className="loading">{t.common.loading}</div>;
  if (error) return <div className="empty">{error}</div>;

  const selected = coops.find((c) => c.id === selectedId);

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: "0.85rem", color: "var(--text-light)" }}>
        {t.coop.subtitle} — {coops.length} {t.coop.title.toLowerCase()}
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        {coops.map((c) => (
          <div
            key={c.id}
            className="buyer-card"
            style={{
              cursor: "pointer",
              borderColor: c.id === selectedId ? "#16a34a" : undefined,
              borderWidth: c.id === selectedId ? "2px" : "1px",
            }}
            onClick={() => setSelectedId(c.id)}
          >
            <h4>{c.name}</h4>
            <div className="country">{c.region}</div>
            <div className="buyer-details">
              <span>
                <em>{t.common.members}</em>
                <strong>{c.member_farm_ids.length}</strong>
              </span>
              <span>
                <em>{t.common.crop}</em>
                <strong>{c.primary_crop}</strong>
              </span>
              <span>
                <em>{t.coop.founded}</em>
                <strong>{c.founded_year}</strong>
              </span>
              <span>
                <em>{t.coop.revenueSplit}</em>
                <strong>{c.revenue_split_pct}%</strong>
              </span>
            </div>
            {c.certifications.length > 0 && (
              <div className="certs">
                {c.certifications.map((cert) => (
                  <span key={cert} className="badge green">
                    {cert}
                  </span>
                ))}
              </div>
            )}
            <p style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--text-light)" }}>
              {c.description}
            </p>
          </div>
        ))}
      </div>

      {selected && aggregated && (
        <div
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.5rem",
            marginBottom: 24,
          }}
        >
          <h3 style={{ marginBottom: 16 }}>
            {t.coop.aggregateMetrics}: {selected.name}
          </h3>
          <div className="grid-3">
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.coop.totalHarvest}
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                {aggregated.total_harvest_kg.toLocaleString()} kg
              </div>
            </div>
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.common.hectares}
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                {aggregated.total_hectares.toFixed(0)}
              </div>
            </div>
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.coop.gradeAPercent}
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                {aggregated.grade_a_pct.toFixed(1)}%
              </div>
            </div>
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.coop.totalValue}
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>
                ${aggregated.total_value_usd.toLocaleString()}
              </div>
            </div>
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.coop.toMembers} ({selected.revenue_split_pct}%)
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>
                ${aggregated.member_distribution_usd.toLocaleString()}
              </div>
            </div>
            <div>
              <em style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
                {t.coop.coopFee} ({selected.coop_fee_pct}%)
              </em>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#eab308" }}>
                ${aggregated.coop_fee_usd.toLocaleString()}
              </div>
            </div>
          </div>
          <button
            onClick={runOptimize}
            disabled={optimizing}
            style={{
              marginTop: 16,
              padding: "0.6rem 1.2rem",
              background: "#16a34a",
              color: "#fff",
              border: 0,
              borderRadius: "6px",
              cursor: optimizing ? "wait" : "pointer",
              fontWeight: 600,
            }}
          >
            {optimizing ? t.common.loading : t.coop.runOptimize}
          </button>
          {optimizeResult != null && (
            <pre
              style={{
                marginTop: 16,
                background: "#0a0a0a",
                color: "#a3e635",
                padding: "1rem",
                borderRadius: "6px",
                overflowX: "auto",
                fontSize: "0.75rem",
                maxHeight: 360,
              }}
            >
              {JSON.stringify(optimizeResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </>
  );
}
