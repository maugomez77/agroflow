import { useEffect, useState } from "react";
import { getDocuments } from "../services/api";
import type { ExportDocument } from "../types";

const statusColor: Record<string, string> = {
  pending: "yellow",
  approved: "green",
  rejected: "red",
};

export default function Documents() {
  const [docs, setDocs] = useState<ExportDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDocuments()
      .then((r) => setDocs(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading documents...</div>;

  return (
    <div className="card">
      <div className="card-header">
        <h3>Export Documents</h3>
        <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
          {docs.length} documents
        </span>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Shipment</th>
              <th>Status</th>
              <th>Issued</th>
              <th>Expiry</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td style={{ fontWeight: 600, textTransform: "capitalize" }}>
                  {d.doc_type}
                </td>
                <td>{d.shipment_id.slice(0, 8)}...</td>
                <td>
                  <span className={`badge ${statusColor[d.status] || "blue"}`}>
                    {d.status}
                  </span>
                </td>
                <td>{d.issued_date}</td>
                <td>{d.expiry_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {docs.length === 0 && (
        <div className="empty">No export documents found.</div>
      )}
    </div>
  );
}
