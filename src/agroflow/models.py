"""Pydantic models for AgroFlow Intelligence."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class CropType(str, Enum):
    avocado = "avocado"
    berry = "berry"
    lemon = "lemon"
    mango = "mango"


class QualityGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class ShipmentStatus(str, Enum):
    preparing = "preparing"
    in_transit = "in_transit"
    customs = "customs"
    delivered = "delivered"


class Destination(str, Enum):
    US = "US"
    EU = "EU"
    Asia = "Asia"
    domestic = "domestic"


class AlertType(str, Enum):
    frost = "frost"
    rain = "rain"
    heat = "heat"
    wind = "wind"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class PriceTrend(str, Enum):
    up = "up"
    down = "down"
    stable = "stable"


class DocType(str, Enum):
    phytosanitary = "phytosanitary"
    customs = "customs"
    origin = "origin"
    invoice = "invoice"


class DocStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CertificationType(str, Enum):
    organic = "organic"
    global_gap = "global_gap"
    fair_trade = "fair_trade"


class InsightType(str, Enum):
    optimization = "optimization"
    risk = "risk"
    opportunity = "opportunity"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# --- Models ---

class Farm(BaseModel):
    id: str
    name: str
    location_lat: float
    location_lng: float
    crop_type: CropType
    hectares: float
    owner: str
    contact: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class TempReading(BaseModel):
    timestamp: str
    temperature_c: float
    location: str


class Harvest(BaseModel):
    id: str
    farm_id: str
    crop_type: CropType
    quantity_kg: float
    quality_grade: QualityGrade
    harvest_date: str
    estimated_value_usd: float


class Shipment(BaseModel):
    id: str
    harvest_ids: list[str]
    destination: Destination
    status: ShipmentStatus
    carrier: str
    container_id: str
    departure_date: str
    eta: str
    temperature_logs: list[TempReading] = []
    documents: list[str] = []


class BuyerMatch(BaseModel):
    id: str
    buyer_name: str
    country: str
    crop_interest: CropType
    volume_needed_kg: float
    price_per_kg_usd: float
    certification_required: list[CertificationType] = []
    matched_farms: list[str] = []


class WeatherAlert(BaseModel):
    id: str
    region: str
    alert_type: AlertType
    severity: Severity
    forecast_date: str
    description: str
    affected_farms: list[str] = []


class MarketPrice(BaseModel):
    crop_type: CropType
    market: str
    price_per_kg_usd: float
    trend: PriceTrend
    date: str
    source: str


class QualityInspection(BaseModel):
    id: str
    harvest_id: str
    inspector: str
    ph_level: float
    brix_level: float
    defect_pct: float
    pesticide_residue: bool
    certification_status: str
    inspection_date: str


class ExportDocument(BaseModel):
    id: str
    shipment_id: str
    doc_type: DocType
    status: DocStatus
    issued_date: str
    expiry_date: str


class SupplyChainInsight(BaseModel):
    id: str
    insight_type: InsightType
    title: str
    description: str
    affected_entities: list[str] = []
    priority: Priority
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DemoStats(BaseModel):
    total_farms: int
    total_hectares: float
    active_shipments: int
    monthly_export_tons: float
    revenue_ytd_usd: float
    top_buyers: list[str] = []
