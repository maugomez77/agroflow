import { useEffect, useState } from "react";
import { getBuyers } from "../services/api";
import type { BuyerMatch } from "../types";

const certLabel: Record<string, string> = {
  organic: "Organic",
  global_gap: "GlobalGAP",
  fair_trade: "Fair Trade",
};

const certColor: Record<string, string> = {
  organic: "green",
  global_gap: "blue",
  fair_trade: "purple",
};

export default function Buyers() {
  const [buyers, setBuyers] = useState<BuyerMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBuyers()
      .then((r) => setBuyers(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading buyers...</div>;

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: "0.85rem", color: "var(--text-light)" }}>
        {buyers.length} buyer matches
      </div>
      <div className="grid-3">
        {buyers.map((b) => (
          <div key={b.id} className="buyer-card">
            <h4>{b.buyer_name}</h4>
            <div className="country">{b.country}</div>
            <div className="buyer-details">
              <span>
                <em>Crop Interest</em>
                <strong>{b.crop_interest}</strong>
              </span>
              <span>
                <em>Volume Needed</em>
                <strong>{b.volume_needed_kg.toLocaleString()} kg</strong>
              </span>
              <span>
                <em>Price/kg</em>
                <strong>${b.price_per_kg_usd.toFixed(2)}</strong>
              </span>
              <span>
                <em>Matched Farms</em>
                <strong>{b.matched_farms.length}</strong>
              </span>
            </div>
            {b.certification_required.length > 0 && (
              <div className="certs">
                {b.certification_required.map((c) => (
                  <span key={c} className={`badge ${certColor[c] || "green"}`}>
                    {certLabel[c] || c}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      {buyers.length === 0 && <div className="empty">No buyer matches.</div>}
    </>
  );
}
