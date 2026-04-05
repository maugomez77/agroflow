import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getFarm, getHarvests } from "../services/api";
import type { Farm, Harvest } from "../types";
import { ArrowLeft } from "lucide-react";

export default function FarmDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [farm, setFarm] = useState<Farm | null>(null);
  const [harvests, setHarvests] = useState<Harvest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getFarm(id).then((r) => setFarm(r.data)),
      getHarvests(id).then((r) => setHarvests(r.data)),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Loading farm...</div>;
  if (!farm) return <div className="empty">Farm not found.</div>;

  return (
    <>
      <button
        className="btn btn-secondary"
        onClick={() => navigate("/farms")}
        style={{ marginBottom: 20 }}
      >
        <ArrowLeft size={16} /> Back to Farms
      </button>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h3>{farm.name}</h3>
          <span className="badge green">{farm.crop_type}</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, fontSize: "0.88rem" }}>
          <div><strong>Owner:</strong> {farm.owner}</div>
          <div><strong>Contact:</strong> {farm.contact}</div>
          <div><strong>Hectares:</strong> {farm.hectares}</div>
          <div><strong>Location:</strong> {farm.location_lat.toFixed(4)}, {farm.location_lng.toFixed(4)}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Harvests</h3>
          <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            {harvests.length} records
          </span>
        </div>
        {harvests.length > 0 ? (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Crop</th>
                  <th>Quantity (kg)</th>
                  <th>Grade</th>
                  <th>Est. Value</th>
                </tr>
              </thead>
              <tbody>
                {harvests.map((h) => (
                  <tr key={h.id}>
                    <td>{h.harvest_date}</td>
                    <td>{h.crop_type}</td>
                    <td>{h.quantity_kg.toLocaleString()}</td>
                    <td>
                      <span className={`badge ${h.quality_grade === "A" ? "green" : h.quality_grade === "B" ? "yellow" : "red"}`}>
                        Grade {h.quality_grade}
                      </span>
                    </td>
                    <td>${h.estimated_value_usd.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty">No harvests recorded.</div>
        )}
      </div>
    </>
  );
}
