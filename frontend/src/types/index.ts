/* AgroFlow Intelligence — TypeScript types matching Python Pydantic models */

export type CropType = "avocado" | "berry" | "lemon" | "mango";
export type QualityGrade = "A" | "B" | "C";
export type ShipmentStatus = "preparing" | "in_transit" | "customs" | "delivered";
export type DestinationType = "US" | "EU" | "Asia" | "domestic";
export type AlertType = "frost" | "rain" | "heat" | "wind";
export type Severity = "low" | "medium" | "high" | "critical";
export type PriceTrend = "up" | "down" | "stable";
export type DocType = "phytosanitary" | "customs" | "origin" | "invoice";
export type DocStatus = "pending" | "approved" | "rejected";
export type CertificationType = "organic" | "global_gap" | "fair_trade";
export type InsightType = "optimization" | "risk" | "opportunity";
export type Priority = "low" | "medium" | "high" | "critical";

export interface Farm {
  id: string;
  name: string;
  location_lat: number;
  location_lng: number;
  crop_type: CropType;
  hectares: number;
  owner: string;
  contact: string;
  created_at: string;
}

export interface TempReading {
  timestamp: string;
  temperature_c: number;
  location: string;
}

export interface Harvest {
  id: string;
  farm_id: string;
  crop_type: CropType;
  quantity_kg: number;
  quality_grade: QualityGrade;
  harvest_date: string;
  estimated_value_usd: number;
}

export interface Shipment {
  id: string;
  harvest_ids: string[];
  destination: DestinationType;
  status: ShipmentStatus;
  carrier: string;
  container_id: string;
  departure_date: string;
  eta: string;
  temperature_logs: TempReading[];
  documents: string[];
}

export interface BuyerMatch {
  id: string;
  buyer_name: string;
  country: string;
  crop_interest: CropType;
  volume_needed_kg: number;
  price_per_kg_usd: number;
  certification_required: CertificationType[];
  matched_farms: string[];
}

export interface WeatherAlert {
  id: string;
  region: string;
  alert_type: AlertType;
  severity: Severity;
  forecast_date: string;
  description: string;
  affected_farms: string[];
}

export interface MarketPrice {
  crop_type: CropType;
  market: string;
  price_per_kg_usd: number;
  trend: PriceTrend;
  date: string;
  source: string;
}

export interface QualityInspection {
  id: string;
  harvest_id: string;
  inspector: string;
  ph_level: number;
  brix_level: number;
  defect_pct: number;
  pesticide_residue: boolean;
  certification_status: string;
  inspection_date: string;
}

export interface ExportDocument {
  id: string;
  shipment_id: string;
  doc_type: DocType;
  status: DocStatus;
  issued_date: string;
  expiry_date: string;
}

export interface SupplyChainInsight {
  id: string;
  insight_type: InsightType;
  title: string;
  description: string;
  affected_entities: string[];
  priority: Priority;
  created_at: string;
}

export interface DemoStats {
  total_farms: number;
  total_hectares: number;
  active_shipments: number;
  monthly_export_tons: number;
  revenue_ytd_usd: number;
  top_buyers: string[];
}

export interface AnalysisResult {
  supply_chain: string;
  risks: string;
  market: string;
}
