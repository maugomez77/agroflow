import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ArrowLeft } from "lucide-react";
import { getShipment } from "../services/api";
import type { Shipment } from "../types";

const statusColor: Record<string, string> = {
  preparing: "blue",
  in_transit: "yellow",
  customs: "orange",
  delivered: "green",
};

export default function ShipmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getShipment(id)
      .then((r) => setShipment(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Loading shipment...</div>;
  if (!shipment) return <div className="empty">Shipment not found.</div>;

  const tempData = shipment.temperature_logs.map((t) => ({
    time: new Date(t.timestamp).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
    }),
    temp: t.temperature_c,
    location: t.location,
  }));

  return (
    <>
      <button
        className="btn btn-secondary"
        onClick={() => navigate("/shipments")}
        style={{ marginBottom: 20 }}
      >
        <ArrowLeft size={16} /> Back to Shipments
      </button>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h3>Shipment {shipment.id.slice(0, 12)}</h3>
          <span className={`badge ${statusColor[shipment.status] || "blue"}`}>
            {shipment.status.replace("_", " ")}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, fontSize: "0.88rem" }}>
          <div><strong>Destination:</strong> {shipment.destination}</div>
          <div><strong>Carrier:</strong> {shipment.carrier}</div>
          <div><strong>Container:</strong> {shipment.container_id}</div>
          <div><strong>ETA:</strong> {shipment.eta}</div>
          <div><strong>Departure:</strong> {shipment.departure_date}</div>
          <div><strong>Harvests:</strong> {shipment.harvest_ids.length}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Temperature Log</h3>
        </div>
        {tempData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tempData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" fontSize={11} />
                <YAxis
                  domain={["auto", "auto"]}
                  unit="C"
                  fontSize={11}
                />
                <Tooltip
                  formatter={(v) => [`${v} C`, "Temperature"]}
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#2d5016"
                  strokeWidth={2}
                  dot={{ fill: "#8bc34a", r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="empty">No temperature readings recorded.</div>
        )}
      </div>
    </>
  );
}
