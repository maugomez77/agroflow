"""FastAPI backend for AgroFlow Intelligence."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import store
from . import ai as ai_module
from .demo import async_generate_demo_data

app = FastAPI(
    title="AgroFlow Intelligence API",
    description="AI-powered agricultural supply chain intelligence for Michoacan, Mexico",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "service": "agroflow"}


# ── Farms ──────────────────────────────────────────────────────

@app.post("/v1/refresh")
async def refresh_data():
    """Re-research and refresh all data with current market conditions."""
    await async_generate_demo_data()
    return {"status": "refreshed", "message": "Data refreshed with real-time market research."}


@app.get("/v1/farms")
def list_farms():
    return [f.model_dump() for f in store.list_farms()]


@app.get("/v1/farms/{farm_id}")
def get_farm(farm_id: str):
    farm = store.get_farm(farm_id)
    if not farm:
        raise HTTPException(404, "Farm not found")
    return farm.model_dump()


# ── Harvests ───────────────────────────────────────────────────

@app.get("/v1/harvests")
def list_harvests(
    farm_id: Optional[str] = Query(None),
    crop_type: Optional[str] = Query(None),
):
    items = store.list_harvests(farm_id)
    if crop_type:
        items = [h for h in items if h.crop_type == crop_type]
    return [h.model_dump() for h in items]


# ── Shipments ──────────────────────────────────────────────────

@app.get("/v1/shipments")
def list_shipments(status: Optional[str] = Query(None)):
    return [s.model_dump() for s in store.list_shipments(status)]


@app.get("/v1/shipments/{shipment_id}")
def get_shipment(shipment_id: str):
    for s in store.list_shipments():
        if s.id == shipment_id:
            return s.model_dump()
    raise HTTPException(404, "Shipment not found")


# ── Buyers ─────────────────────────────────────────────────────

@app.get("/v1/buyers")
def list_buyers():
    return [b.model_dump() for b in store.list_buyer_matches()]


# ── Weather ────────────────────────────────────────────────────

@app.get("/v1/weather")
def list_weather():
    return [w.model_dump() for w in store.get_weather_alerts()]


# ── Prices ─────────────────────────────────────────────────────

@app.get("/v1/prices")
def list_prices():
    return [p.model_dump() for p in store.get_market_prices()]


# ── Quality ────────────────────────────────────────────────────

@app.get("/v1/quality")
def list_quality(harvest_id: Optional[str] = Query(None)):
    return [q.model_dump() for q in store.get_quality_inspections(harvest_id)]


# ── Documents ──────────────────────────────────────────────────

@app.get("/v1/documents")
def list_documents(shipment_id: Optional[str] = Query(None)):
    return [d.model_dump() for d in store.get_export_documents(shipment_id)]


# ── Insights ───────────────────────────────────────────────────

@app.get("/v1/insights")
def list_insights():
    return [i.model_dump() for i in store.get_insights()]


# ── Stats ──────────────────────────────────────────────────────

@app.get("/v1/stats")
def get_stats():
    stats = store.get_stats()
    if not stats:
        raise HTTPException(404, "No stats available. Load demo data first.")
    return stats.model_dump()


# ── AI Endpoints ───────────────────────────────────────────────

@app.post("/v1/analyze")
def run_analysis():
    farms = [f.model_dump() for f in store.list_farms()]
    harvests = [h.model_dump() for h in store.list_harvests()]
    shipments = [s.model_dump() for s in store.list_shipments()]
    if not farms:
        raise HTTPException(400, "No data. Load demo data first.")
    return ai_module.analyze_supply_chain(farms, harvests, shipments)


@app.post("/v1/predict/{farm_id}")
def run_prediction(farm_id: str):
    farm = store.get_farm(farm_id)
    if not farm:
        raise HTTPException(404, "Farm not found")
    weather = [w.model_dump() for w in store.get_weather_alerts()]
    return ai_module.predict_yield(farm.model_dump(), weather)


@app.post("/v1/optimize")
def run_optimization():
    shipments = [s.model_dump() for s in store.list_shipments()]
    if not shipments:
        raise HTTPException(400, "No shipments. Load demo data first.")
    return ai_module.optimize_logistics(shipments)


@app.post("/v1/report")
def run_report():
    prices = [p.model_dump() for p in store.get_market_prices()]
    if not prices:
        raise HTTPException(400, "No price data. Load demo data first.")
    return ai_module.generate_market_report(prices)
