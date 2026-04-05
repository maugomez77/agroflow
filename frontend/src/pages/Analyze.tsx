import { useState } from "react";
import { BrainCircuit, AlertTriangle, BarChart3, Truck } from "lucide-react";
import { runAnalysis, runOptimization, runMarketReport } from "../services/api";

interface Section {
  title: string;
  icon: React.ReactNode;
  content: string | null;
}

export default function Analyze() {
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setSections([]);

    try {
      const [analysisRes, optimizeRes, reportRes] = await Promise.allSettled([
        runAnalysis(),
        runOptimization(),
        runMarketReport(),
      ]);

      const results: Section[] = [];

      if (analysisRes.status === "fulfilled") {
        const d = analysisRes.value.data as unknown as Record<string, string>;
        if (d.supply_chain) {
          results.push({
            title: "Supply Chain Analysis",
            icon: <Truck size={18} />,
            content: d.supply_chain,
          });
        }
        if (d.risks) {
          results.push({
            title: "Risk Assessment",
            icon: <AlertTriangle size={18} />,
            content: d.risks,
          });
        }
        // If the response is a single string
        if (typeof d === "string") {
          results.push({
            title: "Supply Chain Analysis",
            icon: <Truck size={18} />,
            content: d,
          });
        }
      }

      if (optimizeRes.status === "fulfilled") {
        const d = optimizeRes.value.data;
        results.push({
          title: "Logistics Optimization",
          icon: <BrainCircuit size={18} />,
          content: typeof d === "string" ? d : JSON.stringify(d, null, 2),
        });
      }

      if (reportRes.status === "fulfilled") {
        const d = reportRes.value.data;
        results.push({
          title: "Market Report",
          icon: <BarChart3 size={18} />,
          content: typeof d === "string" ? d : JSON.stringify(d, null, 2),
        });
      }

      if (results.length === 0) {
        setError("No analysis results returned. Make sure demo data is loaded.");
      }

      setSections(results);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Analysis failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3>AI-Powered Analysis</h3>
        </div>
        <p style={{ fontSize: "0.88rem", color: "var(--text-light)", marginBottom: 16 }}>
          Run Claude-powered analysis on your supply chain data. This will
          generate insights covering logistics, risks, and market conditions for
          your Michoacan agricultural operations.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleAnalyze}
          disabled={loading}
        >
          <BrainCircuit size={16} />
          {loading ? "Analyzing..." : "Run AI Analysis"}
        </button>
      </div>

      {error && (
        <div className="alert-card critical" style={{ marginBottom: 20 }}>
          <h4>Error</h4>
          <p>{error}</p>
        </div>
      )}

      {sections.map((s, i) => (
        <div key={i} className="card analysis-section" style={{ marginBottom: 16 }}>
          <h3>
            {s.icon} {s.title}
          </h3>
          <div className="content">{s.content}</div>
        </div>
      ))}
    </>
  );
}
