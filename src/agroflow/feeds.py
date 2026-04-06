"""Real-time data feeds from free public APIs.

Fetches live weather, soil, and trade data for Michoacan farms.
All sources are free and require NO API keys.

Sources:
  - Open-Meteo: weather forecasts and soil data
  - UN Comtrade: avocado export volumes (with cached fallback)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, date
from typing import Any

import httpx

# ── Farm locations (Michoacan) ────────────────────────────────

FARMS = [
    {"id": "farm-001", "name": "Rancho Los Aguacates",    "region": "Uruapan",         "lat": 19.4181, "lng": -102.0534},
    {"id": "farm-002", "name": "Huerta El Paraiso",       "region": "Tancitaro",       "lat": 19.3467, "lng": -102.2256},
    {"id": "farm-003", "name": "Finca San Miguel",        "region": "Periban",         "lat": 19.5012, "lng": -102.4234},
    {"id": "farm-004", "name": "Rancho La Esperanza",     "region": "Uruapan",         "lat": 19.4181, "lng": -102.0534},
    {"id": "farm-005", "name": "Huerta Don Sergio",       "region": "Tancitaro",       "lat": 19.3467, "lng": -102.2256},
    {"id": "farm-006", "name": "Aguacates del Valle",     "region": "Uruapan",         "lat": 19.4181, "lng": -102.0534},
    {"id": "farm-007", "name": "Finca Tancitaro Gold",    "region": "Tancitaro",       "lat": 19.3467, "lng": -102.2256},
    {"id": "farm-008", "name": "Rancho Verde Periban",    "region": "Periban",         "lat": 19.5012, "lng": -102.4234},
    {"id": "farm-009", "name": "Berries Los Reyes",       "region": "Los Reyes",       "lat": 19.5876, "lng": -102.4712},
    {"id": "farm-010", "name": "Frutillas del Sur",       "region": "Los Reyes",       "lat": 19.5876, "lng": -102.4712},
    {"id": "farm-011", "name": "Berry Paradise Tacambaro","region": "Tacambaro",       "lat": 19.2345, "lng": -101.4567},
    {"id": "farm-012", "name": "Citricos Ario",           "region": "Ario de Rosales", "lat": 19.2012, "lng": -101.7234},
]

# Unique coordinates to avoid duplicate API calls
UNIQUE_LOCATIONS: dict[str, dict] = {}
for _f in FARMS:
    key = f"{_f['lat']},{_f['lng']}"
    if key not in UNIQUE_LOCATIONS:
        UNIQUE_LOCATIONS[key] = {"lat": _f["lat"], "lng": _f["lng"], "region": _f["region"], "farm_ids": []}
    UNIQUE_LOCATIONS[key]["farm_ids"].append(_f["id"])

# WMO weather codes
_WEATHER_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

TIMEOUT = 10.0


# ── Weather ───────────────────────────────────────────────────

async def fetch_weather(lat: float, lng: float) -> dict | None:
    """Fetch 7-day forecast from Open-Meteo for a single location."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "America/Mexico_City",
        "forecast_days": 7,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def fetch_all_farm_weather() -> dict:
    """Fetch weather for all unique farm locations concurrently.

    Returns:
        {
            "locations": [
                {
                    "region": str,
                    "farm_ids": [str],
                    "current": {"temp_c", "humidity", "precipitation_mm", "wind_kmh", "weather_code", "description"},
                    "daily": [{"date", "temp_max", "temp_min", "precip_mm", "precip_prob"}],
                },
                ...
            ],
            "alerts": [
                {"region", "alert_type", "severity", "description", "forecast_date", "affected_farms"},
                ...
            ],
            "fetched_at": str,
        }
    """
    tasks = []
    loc_keys = list(UNIQUE_LOCATIONS.keys())
    for key in loc_keys:
        loc = UNIQUE_LOCATIONS[key]
        tasks.append(fetch_weather(loc["lat"], loc["lng"]))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    locations: list[dict] = []
    alerts: list[dict] = []

    for key, result in zip(loc_keys, results):
        loc = UNIQUE_LOCATIONS[key]
        if isinstance(result, Exception) or result is None:
            continue

        data = result
        current = data.get("current", {})
        daily = data.get("daily", {})

        # Parse current conditions
        weather_code = current.get("weather_code", 0)
        current_parsed = {
            "temp_c": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation", 0),
            "wind_kmh": current.get("wind_speed_10m", 0),
            "weather_code": weather_code,
            "description": _WEATHER_DESCRIPTIONS.get(weather_code, "Unknown"),
        }

        # Parse daily forecast
        daily_dates = daily.get("time", [])
        daily_max = daily.get("temperature_2m_max", [])
        daily_min = daily.get("temperature_2m_min", [])
        daily_precip = daily.get("precipitation_sum", [])
        daily_prob = daily.get("precipitation_probability_max", [])

        daily_parsed = []
        for i in range(len(daily_dates)):
            daily_parsed.append({
                "date": daily_dates[i],
                "temp_max": daily_max[i] if i < len(daily_max) else None,
                "temp_min": daily_min[i] if i < len(daily_min) else None,
                "precip_mm": daily_precip[i] if i < len(daily_precip) else None,
                "precip_prob": daily_prob[i] if i < len(daily_prob) else None,
            })

        locations.append({
            "region": loc["region"],
            "farm_ids": loc["farm_ids"],
            "current": current_parsed,
            "daily": daily_parsed,
        })

        # Generate alerts from real data
        _generate_alerts(loc["region"], loc["farm_ids"], current_parsed, daily_parsed, alerts)

    return {
        "locations": locations,
        "alerts": alerts,
        "fetched_at": datetime.now().isoformat(),
    }


def _generate_alerts(
    region: str,
    farm_ids: list[str],
    current: dict,
    daily: list[dict],
    alerts: list[dict],
) -> None:
    """Generate weather alerts only for genuinely concerning conditions."""

    for day in daily:
        d = day["date"]
        t_min = day.get("temp_min")
        t_max = day.get("temp_max")
        precip = day.get("precip_mm")
        prob = day.get("precip_prob")

        # Frost alert: min temp < 4 C
        if t_min is not None and t_min < 4:
            sev = "critical" if t_min < 0 else ("high" if t_min < 2 else "medium")
            alerts.append({
                "region": region,
                "alert_type": "frost",
                "severity": sev,
                "description": (
                    f"Frost warning for {region}: minimum temperature forecast at {t_min:.1f} C on {d}. "
                    f"Avocado trees are vulnerable below 4 C. Protect young trees and recently set fruit."
                ),
                "forecast_date": d,
                "affected_farms": farm_ids,
            })

        # Heat alert: max temp > 35 C
        if t_max is not None and t_max > 35:
            sev = "critical" if t_max > 40 else ("high" if t_max > 37 else "medium")
            alerts.append({
                "region": region,
                "alert_type": "heat",
                "severity": sev,
                "description": (
                    f"Heat stress alert for {region}: maximum temperature forecast at {t_max:.1f} C on {d}. "
                    f"Berry crops at risk of sunburn. Increase irrigation frequency."
                ),
                "forecast_date": d,
                "affected_farms": farm_ids,
            })

        # Rain alert: > 30mm precipitation or > 80% probability
        if precip is not None and precip > 30:
            sev = "critical" if precip > 60 else ("high" if precip > 40 else "medium")
            alerts.append({
                "region": region,
                "alert_type": "rain",
                "severity": sev,
                "description": (
                    f"Heavy rain alert for {region}: {precip:.1f} mm forecast on {d} "
                    f"(probability {prob}%). Potential harvest delays and flooding risk."
                ),
                "forecast_date": d,
                "affected_farms": farm_ids,
            })
        elif prob is not None and prob > 80 and (precip is None or precip <= 30):
            alerts.append({
                "region": region,
                "alert_type": "rain",
                "severity": "low",
                "description": (
                    f"Rain likely in {region}: {prob}% probability on {d} "
                    f"({precip:.1f} mm expected). Monitor conditions."
                ),
                "forecast_date": d,
                "affected_farms": farm_ids,
            })

    # Wind alert from current conditions: > 40 km/h
    wind = current.get("wind_kmh", 0)
    if wind and wind > 40:
        sev = "high" if wind > 60 else "medium"
        alerts.append({
            "region": region,
            "alert_type": "wind",
            "severity": sev,
            "description": (
                f"Strong wind alert for {region}: current wind speed {wind:.1f} km/h. "
                f"Secure greenhouse covers and irrigation equipment. Risk of crop damage."
            ),
            "forecast_date": datetime.now().strftime("%Y-%m-%d"),
            "affected_farms": farm_ids,
        })


# ── UN Comtrade (Trade Data) ─────────────────────────────────

# Cached fallback data based on real UN Comtrade historical records
_COMTRADE_FALLBACK = {
    "source": "UN Comtrade (cached historical data)",
    "reporter": "Mexico",
    "hs_code": "080440",
    "commodity": "Avocados, fresh or dried",
    "years": {
        "2023": {
            "total_export_value_usd": 3_147_000_000,
            "total_volume_kg": 1_278_000_000,
            "top_partners": [
                {"country": "United States", "value_usd": 2_784_000_000, "volume_kg": 1_092_000_000},
                {"country": "Canada", "value_usd": 112_000_000, "volume_kg": 48_000_000},
                {"country": "Japan", "value_usd": 89_000_000, "volume_kg": 38_000_000},
                {"country": "Netherlands", "value_usd": 42_000_000, "volume_kg": 21_000_000},
                {"country": "Spain", "value_usd": 31_000_000, "volume_kg": 16_000_000},
            ],
        },
        "2024": {
            "total_export_value_usd": 3_312_000_000,
            "total_volume_kg": 1_340_000_000,
            "top_partners": [
                {"country": "United States", "value_usd": 2_921_000_000, "volume_kg": 1_142_000_000},
                {"country": "Canada", "value_usd": 125_000_000, "volume_kg": 53_000_000},
                {"country": "Japan", "value_usd": 96_000_000, "volume_kg": 42_000_000},
                {"country": "Netherlands", "value_usd": 48_000_000, "volume_kg": 24_000_000},
                {"country": "Spain", "value_usd": 35_000_000, "volume_kg": 18_000_000},
            ],
        },
    },
    "live": False,
}


async def fetch_comtrade_exports() -> dict:
    """Fetch Mexico avocado export data from UN Comtrade.

    The public preview API is attempted first. If it fails (common due to
    rate limits or endpoint changes), cached historical data is returned.
    """
    # Try the UN Comtrade public preview API (no key needed for preview)
    urls_to_try = [
        "https://comtradeapi.un.org/public/v1/preview/C/A/HS/484/0/080440?period=2023,2024",
        "https://comtradeapi.un.org/public/v1/preview/C/A/HS/484/0/080440",
    ]

    for url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("data", [])
                    if records:
                        return _parse_comtrade(records)
        except Exception:
            continue

    # Return cached fallback
    return _COMTRADE_FALLBACK


def _parse_comtrade(records: list[dict]) -> dict:
    """Parse UN Comtrade response records into a clean structure."""
    years: dict[str, dict] = {}
    for rec in records:
        period = str(rec.get("period", ""))
        partner = rec.get("partnerDesc", "World")
        value = rec.get("primaryValue", 0) or 0
        qty = rec.get("qty", 0) or 0

        if period not in years:
            years[period] = {"total_export_value_usd": 0, "total_volume_kg": 0, "top_partners": []}

        if partner == "World":
            years[period]["total_export_value_usd"] = value
            years[period]["total_volume_kg"] = qty
        else:
            years[period]["top_partners"].append({
                "country": partner,
                "value_usd": value,
                "volume_kg": qty,
            })

    # Sort partners by value
    for y in years.values():
        y["top_partners"].sort(key=lambda x: x["value_usd"], reverse=True)
        y["top_partners"] = y["top_partners"][:5]

    return {
        "source": "UN Comtrade (live)",
        "reporter": "Mexico",
        "hs_code": "080440",
        "commodity": "Avocados, fresh or dried",
        "years": years,
        "live": True,
    }


# ── Soil Data (Crop Health Proxy) ─────────────────────────────

async def fetch_soil_data(lat: float, lng: float) -> dict | None:
    """Fetch soil moisture and temperature from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "soil_temperature_0cm,soil_moisture_0_to_1cm",
        "timezone": "America/Mexico_City",
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def fetch_all_soil_health() -> list[dict]:
    """Fetch soil data for all unique locations and estimate crop health.

    Returns list of:
        {"region", "farm_ids", "soil_temp_c", "soil_moisture", "health_status", "details"}
    """
    tasks = []
    loc_keys = list(UNIQUE_LOCATIONS.keys())
    for key in loc_keys:
        loc = UNIQUE_LOCATIONS[key]
        tasks.append(fetch_soil_data(loc["lat"], loc["lng"]))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    soil_health: list[dict] = []

    for key, result in zip(loc_keys, results):
        loc = UNIQUE_LOCATIONS[key]
        if isinstance(result, Exception) or result is None:
            soil_health.append({
                "region": loc["region"],
                "farm_ids": loc["farm_ids"],
                "soil_temp_c": None,
                "soil_moisture": None,
                "health_status": "unknown",
                "details": "Unable to fetch soil data.",
            })
            continue

        hourly = result.get("hourly", {})
        temps = hourly.get("soil_temperature_0cm", [])
        moisture = hourly.get("soil_moisture_0_to_1cm", [])

        avg_temp = sum(t for t in temps if t is not None) / max(len([t for t in temps if t is not None]), 1) if temps else None
        avg_moisture = sum(m for m in moisture if m is not None) / max(len([m for m in moisture if m is not None]), 1) if moisture else None

        # Estimate health status based on soil conditions
        # Avocado ideal: soil temp 15-25 C, moisture 0.15-0.35 m3/m3
        # Berry ideal: soil temp 12-22 C, moisture 0.20-0.40 m3/m3
        health, details = _classify_soil_health(avg_temp, avg_moisture)

        soil_health.append({
            "region": loc["region"],
            "farm_ids": loc["farm_ids"],
            "soil_temp_c": round(avg_temp, 1) if avg_temp is not None else None,
            "soil_moisture": round(avg_moisture, 3) if avg_moisture is not None else None,
            "health_status": health,
            "details": details,
        })

    return soil_health


def _classify_soil_health(temp: float | None, moisture: float | None) -> tuple[str, str]:
    """Classify crop health from soil temperature and moisture."""
    if temp is None or moisture is None:
        return "unknown", "Insufficient data to classify soil health."

    issues: list[str] = []

    # Temperature assessment
    if temp < 10:
        issues.append(f"Soil temperature too cold ({temp:.1f} C) -- root growth slowed")
    elif temp > 30:
        issues.append(f"Soil temperature too hot ({temp:.1f} C) -- heat stress risk")
    elif temp < 15 or temp > 25:
        issues.append(f"Soil temperature slightly outside optimal range ({temp:.1f} C)")

    # Moisture assessment (m3/m3 volumetric)
    if moisture < 0.10:
        issues.append(f"Soil very dry ({moisture:.3f} m3/m3) -- irrigation needed urgently")
    elif moisture < 0.15:
        issues.append(f"Soil moisture low ({moisture:.3f} m3/m3) -- increase irrigation")
    elif moisture > 0.45:
        issues.append(f"Soil waterlogged ({moisture:.3f} m3/m3) -- drainage risk")
    elif moisture > 0.35:
        issues.append(f"Soil moisture high ({moisture:.3f} m3/m3) -- monitor drainage")

    if not issues:
        return "good", f"Soil conditions optimal: {temp:.1f} C, moisture {moisture:.3f} m3/m3."
    elif len(issues) >= 2 or moisture < 0.10 or moisture > 0.45 or temp < 10 or temp > 30:
        return "critical", " | ".join(issues)
    else:
        return "stressed", " | ".join(issues)


# ── Combined Fetch ────────────────────────────────────────────

async def fetch_all_realtime() -> dict:
    """Fetch all real-time data concurrently.

    Returns:
        {
            "weather": {...},       # from fetch_all_farm_weather
            "trade_data": {...},    # from fetch_comtrade_exports
            "soil_health": [...],   # from fetch_all_soil_health
            "fetched_at": str,
        }
    """
    weather_task = fetch_all_farm_weather()
    trade_task = fetch_comtrade_exports()
    soil_task = fetch_all_soil_health()

    results = await asyncio.gather(weather_task, trade_task, soil_task, return_exceptions=True)

    weather = results[0] if not isinstance(results[0], Exception) else {"locations": [], "alerts": [], "fetched_at": datetime.now().isoformat()}
    trade = results[1] if not isinstance(results[1], Exception) else _COMTRADE_FALLBACK
    soil = results[2] if not isinstance(results[2], Exception) else []

    return {
        "weather": weather,
        "trade_data": trade,
        "soil_health": soil,
        "fetched_at": datetime.now().isoformat(),
    }
