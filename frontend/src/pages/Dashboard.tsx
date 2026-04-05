import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Sprout,
  MapPin,
  Truck,
  Weight,
  DollarSign,
} from "lucide-react";
import { getStats, getWeather, getShipments, getPrices, getInsights } from "../services/api";
import type {
  DemoStats,
  WeatherAlert,
  Shipment,
  MarketPrice,
  SupplyChainInsight,
} from "../types";

const PIE_COLORS = ["#2196f3", "#ffc107", "#ff9800", "#4caf50"];

function trendArrow(t: string) {
  if (t === "up") return <span className="trend-up">&#8593;</span>;
  if (t === "down") return <span className="trend-down">&#8595;</span>;
  return <span className="trend-stable">&#8594;</span>;
}

function priorityBadge(p: string) {
  const map: Record<string, string> = {
    critical: "red",
    high: "orange",
    medium: "yellow",
    low: "green",
  };
  return <span className={`badge ${map[p] || "blue"}`}>{p}</span>;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DemoStats | null>(null);
  const [weather, setWeather] = useState<WeatherAlert[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [prices, setPrices] = useState<MarketPrice[]>([]);
  const [insights, setInsights] = useState<SupplyChainInsight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getStats().then((r) => setStats(r.data)),
      getWeather().then((r) => setWeather(r.data)),
      getShipments().then((r) => setShipments(r.data)),
      getPrices().then((r) => setPrices(r.data)),
      getInsights().then((r) => setInsights(r.data)),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;

  /* Shipment status aggregation for pie chart */
  const statusCounts: Record<string, number> = {};
  shipments.forEach((s) => {
    statusCounts[s.status] = (statusCounts[s.status] || 0) + 1;
  });
  const pieData = Object.entries(statusCounts).map(([name, value]) => ({
    name: name.replace("_", " "),
    value,
  }));

  return (
    <>
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon green"><Sprout size={22} /></div>
          <div className="kpi-info">
            <label>Total Farms</label>
            <div className="value">{stats?.total_farms ?? "-"}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon green"><MapPin size={22} /></div>
          <div className="kpi-info">
            <label>Total Hectares</label>
            <div className="value">{stats?.total_hectares?.toLocaleString() ?? "-"}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon blue"><Truck size={22} /></div>
          <div className="kpi-info">
            <label>Active Shipments</label>
            <div className="value">{stats?.active_shipments ?? "-"}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon orange"><Weight size={22} /></div>
          <div className="kpi-info">
            <label>Monthly Export (tons)</label>
            <div className="value">{stats?.monthly_export_tons?.toLocaleString() ?? "-"}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon green"><DollarSign size={22} /></div>
          <div className="kpi-info">
            <label>Revenue YTD</label>
            <div className="value">
              ${stats?.revenue_ytd_usd?.toLocaleString() ?? "-"}
            </div>
          </div>
        </div>
      </div>

      {/* Weather Alerts */}
      {weather.length > 0 && (
        <>
          <div className="card-header">
            <h3>Weather Alerts</h3>
          </div>
          <div className="alerts-grid">
            {weather.map((w) => (
              <div key={w.id} className={`alert-card ${w.severity}`}>
                <h4>
                  {w.alert_type.toUpperCase()} &mdash; {w.region}
                </h4>
                <p>{w.description}</p>
                <div className="alert-meta">
                  <span>{w.severity}</span>
                  <span>{w.forecast_date}</span>
                  <span>{w.affected_farms.length} farms affected</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="grid-2" style={{ marginTop: 8 }}>
        {/* Shipment Pie Chart */}
        <div className="card">
          <div className="card-header">
            <h3>Shipment Status</h3>
          </div>
          {pieData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name} (${value})`}
                  >
                    {pieData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={PIE_COLORS[i % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty">No shipment data</div>
          )}
        </div>

        {/* Market Prices */}
        <div className="card">
          <div className="card-header">
            <h3>Market Prices</h3>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Crop</th>
                  <th>Market</th>
                  <th>Price/kg</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {prices.map((p, i) => (
                  <tr key={i}>
                    <td>{p.crop_type}</td>
                    <td>{p.market}</td>
                    <td>${p.price_per_kg_usd.toFixed(2)}</td>
                    <td>{trendArrow(p.trend)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Insights */}
      {insights.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="card-header">
            <h3>Recent Supply Chain Insights</h3>
          </div>
          {insights.slice(0, 6).map((ins) => (
            <div key={ins.id} className="insight-item">
              <h4>
                {priorityBadge(ins.priority)} {ins.title}
              </h4>
              <p>{ins.description}</p>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
