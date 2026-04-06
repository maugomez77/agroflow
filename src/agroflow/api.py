"""FastAPI backend for AgroFlow Intelligence."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import store
from . import ai as ai_module
from .demo import async_generate_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-research real-time data in background after startup."""
    import asyncio

    async def _background_research():
        data = store.load()
        if not data.get("farms"):
            try:
                await async_generate_demo_data()
            except Exception:
                pass

    # Launch research in background so the port binds immediately
    asyncio.create_task(_background_research())
    yield


app = FastAPI(
    title="AgroFlow Intelligence API",
    description="AI-powered agricultural supply chain intelligence for Michoacan, Mexico",
    version="0.1.0",
    lifespan=lifespan,
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


# ── Live Data Feeds ───────────────────────────────────────────

@app.get("/v1/weather/live")
async def live_weather():
    """Fetch real-time weather for all farm locations from Open-Meteo."""
    from .feeds import fetch_all_farm_weather
    try:
        return await fetch_all_farm_weather()
    except Exception as e:
        raise HTTPException(503, f"Weather service unavailable: {e}")


@app.get("/v1/trade")
async def trade_data():
    """Fetch real Mexico avocado export data from UN Comtrade."""
    from .feeds import fetch_comtrade_exports
    try:
        return await fetch_comtrade_exports()
    except Exception as e:
        raise HTTPException(503, f"Trade data service unavailable: {e}")


@app.get("/v1/soil/{farm_id}")
async def soil_health(farm_id: str):
    """Fetch real soil data for a specific farm."""
    from .feeds import FARMS, fetch_soil_data, _classify_soil_health
    farm = next((f for f in FARMS if f["id"] == farm_id), None)
    if not farm:
        raise HTTPException(404, f"Farm {farm_id} not found in feeds registry.")
    raw = await fetch_soil_data(farm["lat"], farm["lng"])
    if not raw:
        raise HTTPException(503, "Soil data service unavailable.")
    hourly = raw.get("hourly", {})
    temps = hourly.get("soil_temperature_0cm", [])
    moisture = hourly.get("soil_moisture_0_to_1cm", [])
    avg_temp = sum(t for t in temps if t is not None) / max(len([t for t in temps if t is not None]), 1) if temps else None
    avg_moisture = sum(m for m in moisture if m is not None) / max(len([m for m in moisture if m is not None]), 1) if moisture else None
    health, details = _classify_soil_health(avg_temp, avg_moisture)
    return {
        "farm_id": farm_id,
        "region": farm["region"],
        "soil_temp_c": round(avg_temp, 1) if avg_temp else None,
        "soil_moisture_m3": round(avg_moisture, 3) if avg_moisture else None,
        "health_status": health,
        "details": details,
        "raw_hourly": {"soil_temperature_0cm": temps, "soil_moisture_0_to_1cm": moisture},
    }


@app.get("/v1/soil")
async def all_soil_health():
    """Fetch real soil data for all farms."""
    from .feeds import fetch_all_soil_health
    try:
        return await fetch_all_soil_health()
    except Exception as e:
        raise HTTPException(503, f"Soil data service unavailable: {e}")
