import { useEffect, useState } from "react";
import { getQuality } from "../services/api";
import type { QualityInspection } from "../types";

function certClass(status: string) {
  const s = status.toLowerCase();
  if (s === "pass" || s === "passed" || s === "approved") return "green";
  if (s === "pending") return "yellow";
  return "red";
}

export default function Quality() {
  const [inspections, setInspections] = useState<QualityInspection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQuality()
      .then((r) => setInspections(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading inspections...</div>;

  return (
    <div className="card">
      <div className="card-header">
        <h3>Quality Inspections</h3>
        <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
          {inspections.length} records
        </span>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Harvest ID</th>
              <th>Inspector</th>
              <th>pH</th>
              <th>Brix</th>
              <th>Defect %</th>
              <th>Pesticide</th>
              <th>Certification</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {inspections.map((q) => (
              <tr key={q.id}>
                <td style={{ fontWeight: 600 }}>{q.harvest_id.slice(0, 8)}...</td>
                <td>{q.inspector}</td>
                <td>{q.ph_level.toFixed(1)}</td>
                <td>{q.brix_level.toFixed(1)}</td>
                <td>{q.defect_pct.toFixed(1)}%</td>
                <td>
                  <span className={`badge ${q.pesticide_residue ? "red" : "green"}`}>
                    {q.pesticide_residue ? "Detected" : "Clear"}
                  </span>
                </td>
                <td>
                  <span className={`badge ${certClass(q.certification_status)}`}>
                    {q.certification_status}
                  </span>
                </td>
                <td>{q.inspection_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {inspections.length === 0 && (
        <div className="empty">No quality inspections found.</div>
      )}
    </div>
  );
}
