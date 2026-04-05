import axios from "axios";
import type {
  Farm,
  Harvest,
  Shipment,
  BuyerMatch,
  WeatherAlert,
  MarketPrice,
  QualityInspection,
  ExportDocument,
  SupplyChainInsight,
  DemoStats,
  AnalysisResult,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
});

/* ── Farms ─────────────────────────────────── */
export const getFarms = () => api.get<Farm[]>("/v1/farms");
export const getFarm = (id: string) => api.get<Farm>(`/v1/farms/${id}`);

/* ── Harvests ──────────────────────────────── */
export const getHarvests = (farmId?: string) =>
  api.get<Harvest[]>("/v1/harvests", { params: { farm_id: farmId } });

/* ── Shipments ─────────────────────────────── */
export const getShipments = (status?: string) =>
  api.get<Shipment[]>("/v1/shipments", { params: { status } });
export const getShipment = (id: string) =>
  api.get<Shipment>(`/v1/shipments/${id}`);

/* ── Buyers ────────────────────────────────── */
export const getBuyers = () => api.get<BuyerMatch[]>("/v1/buyers");

/* ── Weather ───────────────────────────────── */
export const getWeather = () => api.get<WeatherAlert[]>("/v1/weather");

/* ── Prices ────────────────────────────────── */
export const getPrices = () => api.get<MarketPrice[]>("/v1/prices");

/* ── Quality ───────────────────────────────── */
export const getQuality = (harvestId?: string) =>
  api.get<QualityInspection[]>("/v1/quality", {
    params: { harvest_id: harvestId },
  });

/* ── Documents ─────────────────────────────── */
export const getDocuments = (shipmentId?: string) =>
  api.get<ExportDocument[]>("/v1/documents", {
    params: { shipment_id: shipmentId },
  });

/* ── Insights ──────────────────────────────── */
export const getInsights = () =>
  api.get<SupplyChainInsight[]>("/v1/insights");

/* ── Stats ─────────────────────────────────── */
export const getStats = () => api.get<DemoStats>("/v1/stats");

/* ── AI ────────────────────────────────────── */
export const runAnalysis = () =>
  api.post<AnalysisResult>("/v1/analyze");
export const runPrediction = (farmId: string) =>
  api.post(`/v1/predict/${farmId}`);
export const runOptimization = () => api.post("/v1/optimize");
export const runMarketReport = () => api.post("/v1/report");

export default api;
