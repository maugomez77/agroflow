import { useEffect, useState } from "react";
import { getSubscription, updateSubscription } from "../services/api";
import type { SubscriptionInfo, SubscriptionTier } from "../types";
import { useI18n } from "../i18n";

export default function Subscription() {
  const { t } = useI18n();
  const [info, setInfo] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<SubscriptionTier | null>(null);

  const refresh = () =>
    getSubscription()
      .then((r) => setInfo(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => {
    refresh();
  }, []);

  const switchTier = async (tier: SubscriptionTier) => {
    setUpdating(tier);
    try {
      await updateSubscription(tier, info?.organization, info?.seats);
      await refresh();
    } finally {
      setUpdating(null);
    }
  };

  if (loading || !info) return <div className="loading">{t.common.loading}</div>;

  const tiers: SubscriptionTier[] = ["starter", "pro", "enterprise"];
  const tierLabel: Record<SubscriptionTier, string> = {
    starter: t.tier.starter,
    pro: t.tier.pro,
    enterprise: t.tier.enterprise,
  };

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: "0.85rem", color: "var(--text-light)" }}>
        {t.tier.current}: <strong>{tierLabel[info.tier]}</strong>
        {" · "}
        {info.organization} · {info.seats} seats
      </div>

      <div className="grid-3">
        {tiers.map((tier) => {
          const meta = info.all_tiers[tier];
          const isCurrent = info.tier === tier;
          return (
            <div
              key={tier}
              className="buyer-card"
              style={{
                borderColor: isCurrent ? "#16a34a" : undefined,
                borderWidth: isCurrent ? "2px" : "1px",
              }}
            >
              <h4>{tierLabel[tier]}</h4>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: 700,
                  color: "#16a34a",
                  marginBottom: 8,
                }}
              >
                ${meta.price_usd_monthly.toFixed(0)}
                <span style={{ fontSize: "0.85rem", color: "var(--text-light)" }}>
                  {t.tier.pricePerMonth}
                </span>
              </div>
              <div style={{ marginBottom: 12, fontSize: "0.85rem" }}>
                <strong>{meta.features.length}</strong> {t.tier.features.toLowerCase()}
              </div>
              <ul
                style={{
                  paddingLeft: 16,
                  fontSize: "0.75rem",
                  color: "var(--text-light)",
                  maxHeight: 200,
                  overflowY: "auto",
                  marginBottom: 12,
                }}
              >
                {meta.features.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              {isCurrent ? (
                <div
                  style={{
                    padding: "0.6rem",
                    background: "#16a34a",
                    color: "#fff",
                    textAlign: "center",
                    borderRadius: "6px",
                    fontWeight: 600,
                  }}
                >
                  ✓ {t.tier.current}
                </div>
              ) : (
                <button
                  onClick={() => switchTier(tier)}
                  disabled={updating === tier}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    background: "#16a34a",
                    color: "#fff",
                    border: 0,
                    borderRadius: "6px",
                    cursor: updating === tier ? "wait" : "pointer",
                    fontWeight: 600,
                  }}
                >
                  {updating === tier ? t.common.loading : `${t.tier.changeTo} ${tierLabel[tier]}`}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
