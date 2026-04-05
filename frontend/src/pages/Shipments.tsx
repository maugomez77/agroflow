import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getShipments } from "../services/api";
import type { Shipment } from "../types";

const statusColor: Record<string, string> = {
  preparing: "blue",
  in_transit: "yellow",
  customs: "orange",
  delivered: "green",
};

export default function Shipments() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getShipments()
      .then((r) => setShipments(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading shipments...</div>;

  return (
    <div className="card">
      <div className="card-header">
        <h3>All Shipments</h3>
        <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
          {shipments.length} shipments
        </span>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Destination</th>
              <th>Status</th>
              <th>Carrier</th>
              <th>Container</th>
              <th>ETA</th>
            </tr>
          </thead>
          <tbody>
            {shipments.map((s) => (
              <tr
                key={s.id}
                className="clickable"
                onClick={() => navigate(`/shipments/${s.id}`)}
              >
                <td style={{ fontWeight: 600 }}>{s.id.slice(0, 8)}...</td>
                <td>{s.destination}</td>
                <td>
                  <span className={`badge ${statusColor[s.status] || "blue"}`}>
                    {s.status.replace("_", " ")}
                  </span>
                </td>
                <td>{s.carrier}</td>
                <td>{s.container_id}</td>
                <td>{s.eta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {shipments.length === 0 && (
        <div className="empty">No shipments found.</div>
      )}
    </div>
  );
}
