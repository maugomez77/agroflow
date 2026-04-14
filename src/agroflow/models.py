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
    rose = "rose"
    chrysanthemum = "chrysanthemum"
    gerbera = "gerbera"
    lily = "lily"


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


# --- Cooperatives ---

class Cooperative(BaseModel):
    id: str
    name: str
    region: str
    member_farm_ids: list[str] = []
    primary_crop: CropType
    contact: str
    revenue_split_pct: float = 85.0  # % of revenue distributed to members
    coop_fee_pct: float = 15.0
    certifications: list[CertificationType] = []
    founded_year: int
    description: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- Subscription Tiers ---

class SubscriptionTier(str, Enum):
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class Subscription(BaseModel):
    tier: SubscriptionTier = SubscriptionTier.starter
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    organization: str = "Default Organization"
    seats: int = 1
    price_usd_monthly: float = 0.0
    features: list[str] = []


# --- Phytosanitary Compliance (SENASICA → APHIS) ---

class PhytoStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    inspection_scheduled = "inspection_scheduled"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class RiskLevel(str, Enum):
    very_low = "very_low"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class PhytoRequirement(BaseModel):
    code: str
    description: str
    destination: Destination
    crop_type: CropType
    mandatory: bool = True
    issuing_authority: str = "SENASICA"


class PhytoCertificate(BaseModel):
    id: str
    shipment_id: Optional[str] = None
    farm_id: str
    crop_type: CropType
    destination: Destination
    senasica_cert_number: Optional[str] = None
    aphis_inspection_id: Optional[str] = None
    status: PhytoStatus = PhytoStatus.draft
    issued_date: Optional[str] = None
    expiry_date: Optional[str] = None
    inspection_date: Optional[str] = None
    requirements_met: list[str] = []
    requirements_missing: list[str] = []
    rejection_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RejectionRiskAssessment(BaseModel):
    certificate_id: str
    risk_level: RiskLevel
    risk_score: float  # 0.0 to 1.0
    factors: list[str] = []
    recommendations: list[str] = []
    estimated_loss_usd: float = 0.0
    assessed_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- Satellite / NDVI Vegetation Monitoring ---

class VegetationStatus(str, Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    stressed = "stressed"
    critical = "critical"


class NDVIReading(BaseModel):
    farm_id: str
    region: str
    date: str
    ndvi: float  # -1.0 to 1.0 (vegetation index)
    evi: Optional[float] = None  # enhanced vegetation index
    solar_radiation: Optional[float] = None  # MJ/m²/day
    cloud_cover_pct: Optional[float] = None
    status: VegetationStatus
    details: str = ""
    source: str = "NASA POWER"
