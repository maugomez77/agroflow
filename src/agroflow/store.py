"""JSON file store for AgroFlow Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import (
    BuyerMatch,
    DemoStats,
    ExportDocument,
    Farm,
    Harvest,
    MarketPrice,
    QualityInspection,
    Shipment,
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
}


def _ensure_dir() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    _ensure_dir()
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {**_EMPTY}


def save(data: dict) -> None:
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
