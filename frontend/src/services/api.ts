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
  Cooperative,
  CooperativeAggregated,
  SubscriptionInfo,
  SubscriptionTier,
  PhytoCertificate,
  PhytoComplianceCheck,
  RejectionRiskAssessment,
  SatelliteReading,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
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

/* ── Cooperatives ───────────────────────────── */
export const getCooperatives = () =>
  api.get<Cooperative[]>("/v1/cooperatives");
export const getCooperative = (id: string) =>
  api.get<Cooperative>(`/v1/cooperatives/${id}`);
export const getCooperativeAggregated = (id: string) =>
  api.get<CooperativeAggregated>(`/v1/cooperatives/${id}/aggregated`);
export const optimizeCooperative = (id: string) =>
  api.post(`/v1/cooperatives/${id}/optimize`);

/* ── Satellite / NDVI ───────────────────────── */
export const getSatelliteAll = () =>
  api.get<SatelliteReading[]>("/v1/satellite");
export const getSatelliteFarm = (farmId: string) =>
  api.get<SatelliteReading>(`/v1/satellite/${farmId}`);
export const getSatelliteCached = () =>
  api.get<SatelliteReading[]>("/v1/satellite/cached/all");

/* ── Phytosanitary Compliance ───────────────── */
export const getPhytoCertificates = (params?: {
  shipment_id?: string;
  farm_id?: string;
}) => api.get<PhytoCertificate[]>("/v1/phyto/certificates", { params });
export const checkPhytoCertificate = (id: string) =>
  api.get<PhytoComplianceCheck>(`/v1/phyto/certificates/${id}/check`);
export const assessPhytoRisk = (id: string, value?: number) =>
  api.post<RejectionRiskAssessment>(
    `/v1/phyto/certificates/${id}/risk`,
    null,
    { params: { shipment_value_usd: value ?? 50000 } }
  );
export const aiPhytoRisk = (id: string) =>
  api.post(`/v1/phyto/certificates/${id}/ai-risk`);
export const getPhytoRequirements = (destination: string, cropType: string) =>
  api.get(`/v1/phyto/requirements/${destination}/${cropType}`);

/* ── Subscription ──────────────────────────── */
export const getSubscription = () => api.get<SubscriptionInfo>("/v1/subscription");
export const updateSubscription = (
  tier: SubscriptionTier,
  organization?: string,
  seats: number = 1
) =>
  api.post("/v1/subscription", null, {
    params: { tier, organization, seats },
  });

export default api;
