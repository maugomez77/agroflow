"""FastAPI backend for AgroFlow Intelligence."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import store
from . import ai as ai_module
from . import phyto as phyto_module
from .demo import async_generate_demo_data
from .models import (
    Cooperative,
    NDVIReading,
    PhytoCertificate,
    PhytoStatus,
    Subscription,
    SubscriptionTier,
)


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


# ── Tier Gating ───────────────────────────────────────────────

def require_feature(feature: str):
    """FastAPI dependency that blocks calls if the active tier lacks the feature."""
    def _dep() -> None:
        sub = store.get_subscription()
        if not store.tier_allows(sub.tier.value, feature):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "feature_not_in_tier",
                    "feature": feature,
                    "current_tier": sub.tier.value,
                    "upgrade_to": "pro" if feature in store.TIER_FEATURES["pro"] else "enterprise",
                    "message": f"Feature '{feature}' requires a higher subscription tier.",
                },
            )
    return _dep


# ── Subscription ──────────────────────────────────────────────

@app.get("/v1/subscription")
def get_subscription():
    sub = store.get_subscription()
    return {
        "tier": sub.tier.value,
        "organization": sub.organization,
        "seats": sub.seats,
        "price_usd_monthly": store.TIER_PRICING.get(sub.tier.value, 0.0),
        "features": store.TIER_FEATURES.get(sub.tier.value, []),
        "started_at": sub.started_at,
        "all_tiers": {
            tier: {
                "price_usd_monthly": store.TIER_PRICING.get(tier, 0.0),
                "features": feats,
            }
            for tier, feats in store.TIER_FEATURES.items()
        },
    }


@app.post("/v1/subscription")
def update_subscription(tier: str, organization: Optional[str] = None, seats: int = 1):
    if tier not in ("starter", "pro", "enterprise"):
        raise HTTPException(400, f"Invalid tier '{tier}'. Must be starter/pro/enterprise.")
    sub = Subscription(
        tier=SubscriptionTier(tier),
        organization=organization or "Default Organization",
        seats=seats,
        price_usd_monthly=store.TIER_PRICING.get(tier, 0.0),
        features=store.TIER_FEATURES.get(tier, []),
    )
    store.set_subscription(sub)
    return {"status": "updated", "tier": tier, "features": sub.features}


# ── Cooperatives (Enterprise tier) ────────────────────────────

@app.get("/v1/cooperatives", dependencies=[Depends(require_feature("cooperatives"))])
def list_cooperatives():
    return [c.model_dump() for c in store.list_cooperatives()]


@app.get("/v1/cooperatives/{coop_id}", dependencies=[Depends(require_feature("cooperatives"))])
def get_cooperative(coop_id: str):
    coop = store.get_cooperative(coop_id)
    if not coop:
        raise HTTPException(404, "Cooperative not found")
    return coop.model_dump()


@app.get(
    "/v1/cooperatives/{coop_id}/aggregated",
    dependencies=[Depends(require_feature("cooperatives"))],
)
def get_cooperative_aggregated(coop_id: str):
    agg = store.aggregate_cooperative(coop_id)
    if not agg:
        raise HTTPException(404, "Cooperative not found")
    return agg


@app.post(
    "/v1/cooperatives/{coop_id}/optimize",
    dependencies=[Depends(require_feature("ai_cooperative_optimize"))],
)
def optimize_cooperative(coop_id: str):
    coop = store.get_cooperative(coop_id)
    if not coop:
        raise HTTPException(404, "Cooperative not found")
    member_ids = set(coop.member_farm_ids)
    harvests = [h.model_dump() for h in store.list_harvests() if h.farm_id in member_ids]
    buyers = [b.model_dump() for b in store.list_buyer_matches()]
    return ai_module.optimize_cooperative_pooling(coop.model_dump(), harvests, buyers)


# ── Satellite / NDVI (Pro tier) ───────────────────────────────

@app.get("/v1/satellite", dependencies=[Depends(require_feature("satellite"))])
async def list_satellite():
    """Live NASA POWER NDVI proxy for all farms."""
    from .feeds import fetch_all_satellite
    try:
        return await fetch_all_satellite()
    except Exception as e:
        raise HTTPException(503, f"Satellite service unavailable: {e}")


@app.get("/v1/satellite/{farm_id}", dependencies=[Depends(require_feature("satellite"))])
async def satellite_for_farm(farm_id: str):
    from .feeds import fetch_satellite_for_farm
    data = await fetch_satellite_for_farm(farm_id)
    if not data:
        raise HTTPException(404, "Farm not found or satellite data unavailable")
    return data


@app.get("/v1/satellite/cached/all")
def cached_satellite():
    """Return cached NDVI readings (no live fetch). Available on all tiers."""
    return [r.model_dump() for r in store.list_ndvi_readings()]


# ── Phytosanitary Compliance (Pro tier) ───────────────────────

@app.get("/v1/phyto/requirements/{destination}/{crop_type}")
def get_phyto_requirements(destination: str, crop_type: str):
    reqs = phyto_module.get_requirements(destination, crop_type)
    if not reqs:
        return {"destination": destination, "crop_type": crop_type, "requirements": []}
    return {
        "destination": destination,
        "crop_type": crop_type,
        "requirements": [r.model_dump() for r in reqs],
        "total": len(reqs),
    }


@app.get(
    "/v1/phyto/certificates",
    dependencies=[Depends(require_feature("phyto_compliance"))],
)
def list_phyto_certs(
    shipment_id: Optional[str] = Query(None),
    farm_id: Optional[str] = Query(None),
):
    return [c.model_dump() for c in store.list_phyto_certificates(shipment_id, farm_id)]


@app.get(
    "/v1/phyto/certificates/{cert_id}/check",
    dependencies=[Depends(require_feature("phyto_compliance"))],
)
def check_phyto_cert(cert_id: str):
    cert = store.get_phyto_certificate(cert_id)
    if not cert:
        raise HTTPException(404, "Certificate not found")
    return phyto_module.check_certificate(cert)


@app.post(
    "/v1/phyto/certificates/{cert_id}/risk",
    dependencies=[Depends(require_feature("phyto_compliance"))],
)
def assess_phyto_risk(cert_id: str, shipment_value_usd: float = 50000.0):
    cert = store.get_phyto_certificate(cert_id)
    if not cert:
        raise HTTPException(404, "Certificate not found")
    risk = phyto_module.assess_rejection_risk(cert, shipment_value_usd)
    store.add_rejection_risk(risk)
    return risk.model_dump()


@app.post(
    "/v1/phyto/certificates/{cert_id}/ai-risk",
    dependencies=[Depends(require_feature("ai_phyto_risk"))],
)
def ai_phyto_risk(cert_id: str):
    cert = store.get_phyto_certificate(cert_id)
    if not cert:
        raise HTTPException(404, "Certificate not found")
    reqs = phyto_module.get_requirements(cert.destination, cert.crop_type)
    historical = [
        r.model_dump()
        for r in store.list_rejection_risks()
        if r.risk_level.value in ("high", "critical")
    ][:5]
    return ai_module.assess_phytosanitary_risk(
        cert.model_dump(),
        [r.model_dump() for r in reqs],
        historical,
    )
