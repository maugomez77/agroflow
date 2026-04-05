import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFarms } from "../services/api";
import type { Farm } from "../types";

export default function Farms() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getFarms()
      .then((r) => setFarms(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading farms...</div>;

  return (
    <div className="card">
      <div className="card-header">
        <h3>All Farms</h3>
        <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
          {farms.length} farms
        </span>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Crop</th>
              <th>Hectares</th>
              <th>Owner</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {farms.map((f) => (
              <tr
                key={f.id}
                className="clickable"
                onClick={() => navigate(`/farms/${f.id}`)}
              >
                <td style={{ fontWeight: 600 }}>{f.name}</td>
                <td>
                  <span className="badge green">{f.crop_type}</span>
                </td>
                <td>{f.hectares}</td>
                <td>{f.owner}</td>
                <td>
                  {f.location_lat.toFixed(3)}, {f.location_lng.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {farms.length === 0 && <div className="empty">No farms found. Load demo data first.</div>}
    </div>
  );
}
