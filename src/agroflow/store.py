"""Persistence layer for AgroFlow.

Hybrid: Postgres JSONB blob when DATABASE_URL is set (Render), JSON file fallback
for local dev / CLI. Render free tier has ephemeral disk — JSON would be wiped on
every cold start, so production must use Postgres.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .database import SessionLocal, KVStore, is_db_enabled
from .models import (
    BuyerMatch,
    Cooperative,
    DemoStats,
    ExportDocument,
    Farm,
    Harvest,
    MarketPrice,
    NDVIReading,
    PhytoCertificate,
    QualityInspection,
    RejectionRiskAssessment,
    Shipment,
    Subscription,
    SubscriptionTier,
    SupplyChainInsight,
    WeatherAlert,
)

STORE_PATH = Path.home() / ".agroflow" / "store.json"

_EMPTY: dict = {
    "farms": [],
    "harvests": [],
    "shipments": [],
    "buyer_matches": [],
    "weather_alerts": [],
    "market_prices": [],
    "quality_inspections": [],
    "export_documents": [],
    "insights": [],
    "stats": None,
    "cooperatives": [],
    "phyto_certificates": [],
    "rejection_risks": [],
    "ndvi_readings": [],
    "subscription": None,
}


_KV_KEY = "main"


def _ensure_dir() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    if is_db_enabled():
        with SessionLocal() as s:
            row = s.get(KVStore, _KV_KEY)
            if row and row.value:
                return {**_EMPTY, **row.value}
            return {**_EMPTY}
    _ensure_dir()
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {**_EMPTY}


def save(data: dict) -> None:
    if is_db_enabled():
        with SessionLocal() as s:
            row = s.get(KVStore, _KV_KEY)
            if row:
                row.value = data
            else:
                s.add(KVStore(key=_KV_KEY, value=data))
            s.commit()
        return
    _ensure_dir()
    STORE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# --- Farms ---

def add_farm(farm: Farm) -> None:
    data = load()
    data["farms"].append(farm.model_dump())
    save(data)


def list_farms() -> list[Farm]:
    data = load()
    return [Farm(**f) for f in data.get("farms", [])]


def get_farm(farm_id: str) -> Optional[Farm]:
    for f in list_farms():
        if f.id == farm_id:
            return f
    return None


# --- Harvests ---

def add_harvest(harvest: Harvest) -> None:
    data = load()
    data["harvests"].append(harvest.model_dump())
    save(data)


def list_harvests(farm_id: Optional[str] = None) -> list[Harvest]:
    data = load()
    harvests = [Harvest(**h) for h in data.get("harvests", [])]
    if farm_id:
        harvests = [h for h in harvests if h.farm_id == farm_id]
    return harvests


# --- Shipments ---

def add_shipment(shipment: Shipment) -> None:
    data = load()
    data["shipments"].append(shipment.model_dump())
    save(data)


def list_shipments(status: Optional[str] = None) -> list[Shipment]:
    data = load()
    shipments = [Shipment(**s) for s in data.get("shipments", [])]
    if status:
        shipments = [s for s in shipments if s.status == status]
    return shipments


def update_shipment_status(shipment_id: str, new_status: str) -> bool:
    data = load()
    for s in data.get("shipments", []):
        if s["id"] == shipment_id:
            s["status"] = new_status
            save(data)
            return True
    return False


# --- Buyer Matches ---

def add_buyer_match(match: BuyerMatch) -> None:
    data = load()
    data["buyer_matches"].append(match.model_dump())
    save(data)


def list_buyer_matches() -> list[BuyerMatch]:
    data = load()
    return [BuyerMatch(**b) for b in data.get("buyer_matches", [])]


# --- Market Prices ---

def get_market_prices() -> list[MarketPrice]:
    data = load()
    return [MarketPrice(**p) for p in data.get("market_prices", [])]


# --- Weather Alerts ---

def get_weather_alerts() -> list[WeatherAlert]:
    data = load()
    return [WeatherAlert(**w) for w in data.get("weather_alerts", [])]


# --- Quality Inspections ---

def get_quality_inspections(harvest_id: Optional[str] = None) -> list[QualityInspection]:
    data = load()
    inspections = [QualityInspection(**q) for q in data.get("quality_inspections", [])]
    if harvest_id:
        inspections = [q for q in inspections if q.harvest_id == harvest_id]
    return inspections


# --- Export Documents ---

def get_export_documents(shipment_id: Optional[str] = None) -> list[ExportDocument]:
    data = load()
    docs = [ExportDocument(**d) for d in data.get("export_documents", [])]
    if shipment_id:
        docs = [d for d in docs if d.shipment_id == shipment_id]
    return docs


# --- Insights ---

def get_insights() -> list[SupplyChainInsight]:
    data = load()
    return [SupplyChainInsight(**i) for i in data.get("insights", [])]


# --- Stats ---

def get_stats() -> Optional[DemoStats]:
    data = load()
    s = data.get("stats")
    if s:
        return DemoStats(**s)
    return None


# --- Cooperatives ---

def add_cooperative(coop: Cooperative) -> None:
    data = load()
    data.setdefault("cooperatives", []).append(coop.model_dump())
    save(data)


def list_cooperatives() -> list[Cooperative]:
    data = load()
    return [Cooperative(**c) for c in data.get("cooperatives", [])]


def get_cooperative(coop_id: str) -> Optional[Cooperative]:
    for c in list_cooperatives():
        if c.id == coop_id:
            return c
    return None


def aggregate_cooperative(coop_id: str) -> Optional[dict]:
    """Compute aggregated metrics for a cooperative across its member farms."""
    coop = get_cooperative(coop_id)
    if not coop:
        return None
    member_ids = set(coop.member_farm_ids)
    member_farms = [f for f in list_farms() if f.id in member_ids]
    member_harvests = [h for h in list_harvests() if h.farm_id in member_ids]
    total_kg = sum(h.quantity_kg for h in member_harvests)
    total_value = sum(h.estimated_value_usd for h in member_harvests)
    member_share = total_value * (coop.revenue_split_pct / 100.0)
    coop_share = total_value * (coop.coop_fee_pct / 100.0)
    grade_a_kg = sum(h.quantity_kg for h in member_harvests if h.quality_grade == "A")
    return {
        "cooperative": coop.model_dump(),
        "member_count": len(member_farms),
        "total_hectares": sum(f.hectares for f in member_farms),
        "total_harvest_kg": total_kg,
        "total_value_usd": round(total_value, 2),
        "member_distribution_usd": round(member_share, 2),
        "coop_fee_usd": round(coop_share, 2),
        "grade_a_pct": round((grade_a_kg / total_kg * 100) if total_kg else 0, 1),
        "harvests_count": len(member_harvests),
    }


# --- Phytosanitary Certificates ---

def add_phyto_certificate(cert: PhytoCertificate) -> None:
    data = load()
    data.setdefault("phyto_certificates", []).append(cert.model_dump())
    save(data)


def list_phyto_certificates(
    shipment_id: Optional[str] = None,
    farm_id: Optional[str] = None,
) -> list[PhytoCertificate]:
    data = load()
    items = [PhytoCertificate(**c) for c in data.get("phyto_certificates", [])]
    if shipment_id:
        items = [c for c in items if c.shipment_id == shipment_id]
    if farm_id:
        items = [c for c in items if c.farm_id == farm_id]
    return items


def get_phyto_certificate(cert_id: str) -> Optional[PhytoCertificate]:
    for c in list_phyto_certificates():
        if c.id == cert_id:
            return c
    return None


def add_rejection_risk(risk: RejectionRiskAssessment) -> None:
    data = load()
    data.setdefault("rejection_risks", []).append(risk.model_dump())
    save(data)


def list_rejection_risks() -> list[RejectionRiskAssessment]:
    data = load()
    return [RejectionRiskAssessment(**r) for r in data.get("rejection_risks", [])]


# --- NDVI / Satellite Readings ---

def add_ndvi_reading(reading: NDVIReading) -> None:
    data = load()
    data.setdefault("ndvi_readings", []).append(reading.model_dump())
    save(data)


def list_ndvi_readings(farm_id: Optional[str] = None) -> list[NDVIReading]:
    data = load()
    items = [NDVIReading(**r) for r in data.get("ndvi_readings", [])]
    if farm_id:
        items = [r for r in items if r.farm_id == farm_id]
    return items


def replace_ndvi_readings(readings: list[NDVIReading]) -> None:
    data = load()
    data["ndvi_readings"] = [r.model_dump() for r in readings]
    save(data)


# --- Subscription ---

def get_subscription() -> Subscription:
    data = load()
    s = data.get("subscription")
    if s:
        return Subscription(**s)
    return Subscription()


def set_subscription(sub: Subscription) -> None:
    data = load()
    data["subscription"] = sub.model_dump()
    save(data)


# Tier features map (used by tier gating in api.py and CLI)
TIER_FEATURES: dict[str, list[str]] = {
    "starter": [
        "farms",
        "harvests",
        "shipments",
        "buyers",
        "quality",
        "weather",
        "prices",
        "documents",
    ],
    "pro": [
        "farms",
        "harvests",
        "shipments",
        "buyers",
        "quality",
        "weather",
        "prices",
        "documents",
        "satellite",
        "ai_analyze",
        "ai_predict",
        "ai_optimize",
        "ai_market_report",
        "phyto_compliance",
    ],
    "enterprise": [
        "farms",
        "harvests",
        "shipments",
        "buyers",
        "quality",
        "weather",
        "prices",
        "documents",
        "satellite",
        "ai_analyze",
        "ai_predict",
        "ai_optimize",
        "ai_market_report",
        "phyto_compliance",
        "cooperatives",
        "ai_phyto_risk",
        "ai_cooperative_optimize",
        "multi_org",
        "priority_support",
    ],
}


TIER_PRICING: dict[str, float] = {
    "starter": 0.0,
    "pro": 99.0,
    "enterprise": 499.0,
}


def tier_allows(tier: str, feature: str) -> bool:
    return feature in TIER_FEATURES.get(tier, [])
