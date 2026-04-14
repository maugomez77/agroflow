import { useEffect, useState } from "react";
import { getSatelliteAll, getSatelliteCached } from "../services/api";
import type { SatelliteReading, VegetationStatus } from "../types";
import { useI18n } from "../i18n";

const statusColor: Record<VegetationStatus, string> = {
  excellent: "#15803d",
  good: "#16a34a",
  fair: "#eab308",
  stressed: "#f97316",
  critical: "#dc2626",
};

export default function Satellite() {
  const { t } = useI18n();
  const [readings, setReadings] = useState<SatelliteReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchingLive, setFetchingLive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSatelliteCached()
      .then((r) => setReadings(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const fetchLive = async () => {
    setFetchingLive(true);
    setError(null);
    try {
      const r = await getSatelliteAll();
      setReadings(r.data);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : detail?.message || t.common.error);
    } finally {
      setFetchingLive(false);
    }
  };

  if (loading) return <div className="loading">{t.common.loading}</div>;

  const statusLabel: Record<VegetationStatus, string> = {
    excellent: t.satellite.excellent,
    good: t.satellite.good,
    fair: t.satellite.fair,
    stressed: t.satellite.stressed,
    critical: t.satellite.critical,
  };

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: "0.85rem", color: "var(--text-light)" }}>
        {t.satellite.subtitle}
      </div>

      <button
        onClick={fetchLive}
        disabled={fetchingLive}
        style={{
          marginBottom: 16,
          padding: "0.6rem 1.2rem",
          background: "#16a34a",
          color: "#fff",
          border: 0,
          borderRadius: "6px",
          cursor: fetchingLive ? "wait" : "pointer",
          fontWeight: 600,
        }}
      >
        {fetchingLive ? t.common.loading : t.satellite.fetchLive}
      </button>

      {error && (
        <div className="empty" style={{ marginBottom: 16, color: "#dc2626" }}>
          {error}
        </div>
      )}

      <div className="grid-3">
        {readings.map((r) => (
          <div key={r.farm_id} className="buyer-card">
            <h4>{r.farm_id}</h4>
            <div className="country">{r.region}</div>
            <div className="buyer-details">
              <span>
                <em>{t.satellite.ndvi}</em>
                <strong style={{ color: statusColor[r.status] }}>
                  {r.ndvi.toFixed(2)}
                </strong>
              </span>
              <span>
                <em>{t.satellite.evi}</em>
                <strong>{r.evi != null ? r.evi.toFixed(2) : "—"}</strong>
              </span>
              <span>
                <em>{t.satellite.solarRadiation}</em>
                <strong>
                  {r.solar_radiation != null ? r.solar_radiation.toFixed(1) : "—"}
                </strong>
              </span>
              <span>
                <em>{t.satellite.cloudCover}</em>
                <strong>
                  {r.cloud_cover_pct != null
                    ? `${r.cloud_cover_pct.toFixed(0)}%`
                    : "—"}
                </strong>
              </span>
            </div>
            <div
              style={{
                marginTop: 8,
                padding: "0.4rem 0.8rem",
                borderRadius: 4,
                background: statusColor[r.status],
                color: "#fff",
                fontSize: "0.75rem",
                fontWeight: 700,
                textAlign: "center",
                textTransform: "uppercase",
              }}
            >
              {statusLabel[r.status]}
            </div>
            <p style={{ marginTop: 8, fontSize: "0.75rem", color: "var(--text-light)" }}>
              {r.details}
            </p>
            <div style={{ marginTop: 4, fontSize: "0.7rem", color: "var(--text-light)" }}>
              {r.source} · {r.date}
            </div>
          </div>
        ))}
      </div>
      {readings.length === 0 && <div className="empty">{t.common.noData}</div>}
    </>
  );
}
