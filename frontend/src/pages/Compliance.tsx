import { useEffect, useState } from "react";
import {
  getPhytoCertificates,
  checkPhytoCertificate,
  assessPhytoRisk,
} from "../services/api";
import type {
  PhytoCertificate,
  PhytoComplianceCheck,
  RejectionRiskAssessment,
  RiskLevel,
} from "../types";
import { useI18n } from "../i18n";

const riskColor: Record<RiskLevel, string> = {
  very_low: "#15803d",
  low: "#16a34a",
  medium: "#eab308",
  high: "#f97316",
  critical: "#dc2626",
};

const statusColor: Record<string, string> = {
  draft: "#6b7280",
  submitted: "#3b82f6",
  inspection_scheduled: "#3b82f6",
  approved: "#16a34a",
  rejected: "#dc2626",
  expired: "#dc2626",
};

export default function Compliance() {
  const { t } = useI18n();
  const [certs, setCerts] = useState<PhytoCertificate[]>([]);
  const [selected, setSelected] = useState<PhytoCertificate | null>(null);
  const [check, setCheck] = useState<PhytoComplianceCheck | null>(null);
  const [risk, setRisk] = useState<RejectionRiskAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPhytoCertificates()
      .then((r) => {
        setCerts(r.data);
        if (r.data.length > 0) setSelected(r.data[0]);
      })
      .catch((e) =>
        setError(e?.response?.data?.detail?.message || t.common.error)
      )
      .finally(() => setLoading(false));
  }, [t.common.error]);

  useEffect(() => {
    if (!selected) return;
    setCheck(null);
    setRisk(null);
    checkPhytoCertificate(selected.id)
      .then((r) => setCheck(r.data))
      .catch(() => {});
  }, [selected]);

  const runRisk = async () => {
    if (!selected) return;
    try {
      const r = await assessPhytoRisk(selected.id, 60000);
      setRisk(r.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail?.message || "Risk assessment failed");
    }
  };

  if (loading) return <div className="loading">{t.common.loading}</div>;
  if (error) return <div className="empty">{error}</div>;

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: "0.85rem", color: "var(--text-light)" }}>
        {t.phyto.subtitle}
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        {certs.map((c) => (
          <div
            key={c.id}
            className="buyer-card"
            style={{
              cursor: "pointer",
              borderColor: c.id === selected?.id ? "#16a34a" : undefined,
              borderWidth: c.id === selected?.id ? "2px" : "1px",
            }}
            onClick={() => setSelected(c)}
          >
            <h4>{c.id}</h4>
            <div className="country">
              {c.farm_id} · {c.crop_type}
            </div>
            <div className="buyer-details">
              <span>
                <em>{t.phyto.destination}</em>
                <strong>{c.destination}</strong>
              </span>
              <span>
                <em>{t.common.status}</em>
                <strong style={{ color: statusColor[c.status] }}>{c.status}</strong>
              </span>
              <span>
                <em>{t.phyto.certNumber}</em>
                <strong style={{ fontSize: "0.7rem" }}>
                  {c.senasica_cert_number || "—"}
                </strong>
              </span>
              <span>
                <em>{t.phyto.expires}</em>
                <strong>{c.expiry_date || "—"}</strong>
              </span>
            </div>
          </div>
        ))}
      </div>

      {selected && check && (
        <div
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.5rem",
            marginBottom: 24,
          }}
        >
          <h3 style={{ marginBottom: 8 }}>
            {selected.id} — {selected.destination}
          </h3>
          <div style={{ marginBottom: 16 }}>
            <strong>{t.phyto.coverage}:</strong>{" "}
            <span style={{ fontSize: "1.5rem", color: check.coverage_pct >= 80 ? "#16a34a" : "#f97316" }}>
              {check.coverage_pct.toFixed(0)}%
            </span>{" "}
            ({check.met_count}/{check.total_requirements})
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <h4 style={{ color: "#16a34a", marginBottom: 8 }}>
                ✓ {t.phyto.requirementsMet}
              </h4>
              {check.met.length === 0 && (
                <div style={{ color: "var(--text-light)" }}>—</div>
              )}
              <ul style={{ paddingLeft: 16, fontSize: "0.85rem" }}>
                {check.met.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ color: "#dc2626", marginBottom: 8 }}>
                ✗ {t.phyto.requirementsMissing}
              </h4>
              {check.missing.length === 0 && (
                <div style={{ color: "var(--text-light)" }}>—</div>
              )}
              <ul style={{ paddingLeft: 16, fontSize: "0.85rem" }}>
                {check.missing.map((m) => {
                  const req = check.requirements.find((r) => r.code === m);
                  return (
                    <li key={m}>
                      <strong>{m}</strong> — {req?.description}
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
          <button
            onClick={runRisk}
            style={{
              marginTop: 16,
              padding: "0.6rem 1.2rem",
              background: "#dc2626",
              color: "#fff",
              border: 0,
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {t.phyto.runRisk}
          </button>

          {risk && (
            <div
              style={{
                marginTop: 16,
                padding: "1rem",
                background: "#0a0a0a",
                borderLeft: `4px solid ${riskColor[risk.risk_level]}`,
                borderRadius: "4px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <div>
                  <strong>{t.phyto.riskLevel}:</strong>{" "}
                  <span
                    style={{
                      color: riskColor[risk.risk_level],
                      fontWeight: 700,
                      textTransform: "uppercase",
                    }}
                  >
                    {risk.risk_level.replace("_", " ")}
                  </span>
                </div>
                <div>
                  <strong>{t.phyto.estimatedLoss}:</strong>{" "}
                  <span style={{ color: "#dc2626", fontWeight: 700 }}>
                    ${risk.estimated_loss_usd.toLocaleString()}
                  </span>
                </div>
              </div>
              <div style={{ marginTop: 12 }}>
                <strong>{t.phyto.riskFactors}:</strong>
                <ul style={{ paddingLeft: 16, fontSize: "0.85rem" }}>
                  {risk.factors.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
              <div style={{ marginTop: 12 }}>
                <strong>{t.phyto.recommendations}:</strong>
                <ul style={{ paddingLeft: 16, fontSize: "0.85rem" }}>
                  {risk.recommendations.slice(0, 6).map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
