"""Real-time data research module for AgroFlow Intelligence.

Uses DuckDuckGo search + Claude Haiku to gather current data about
Michoacan agriculture: market prices, weather, export news, buyer activity.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from typing import Any

import httpx

HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Michoacan farming region coordinates
REGIONS = {
    "Uruapan": (19.4181, -102.0534),
    "Tancitaro": (19.3467, -102.2256),
    "Los Reyes": (19.5876, -102.4712),
    "Periban": (19.5012, -102.4234),
    "Tacambaro": (19.2345, -101.4567),
}

# Farm-to-region mapping for weather alerts
REGION_FARMS = {
    "Uruapan": ["farm-001", "farm-006"],
    "Tancitaro": ["farm-007", "farm-008"],
    "Los Reyes": ["farm-009", "farm-010"],
    "Periban": ["farm-008"],
    "Tacambaro": ["farm-011"],
}


# ── Helpers ────────────────────────────────────────────────────

def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _future_date(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


async def _search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo search, returning list of {title, body, href}."""
    try:
        from ddgs import DDGS
        # Run sync ddgs in a thread to avoid blocking
        def _do_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        return await asyncio.get_event_loop().run_in_executor(None, _do_search)
    except Exception:
        return []


async def _search_with_delay(query: str, max_results: int = 5) -> list[dict]:
    """Search with a small random delay to avoid rate limiting."""
    delay = random.uniform(0.3, 0.8)
    await asyncio.sleep(delay)
    return await _search_ddg(query, max_results)


async def _ask_haiku(system: str, prompt: str) -> str:
    """Send a prompt to Claude Haiku and return text response."""
    try:
        import anthropic
        client = anthropic.Anthropic()

        def _call():
            msg = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text

        return await asyncio.get_event_loop().run_in_executor(None, _call)
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'


def _parse_json(text: str) -> Any:
    """Extract JSON from Claude response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for marker in ("```json", "```"):
        if marker in text:
            try:
                start = text.index(marker) + len(marker)
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (ValueError, json.JSONDecodeError):
                pass
    return None


# ── Research Functions ─────────────────────────────────────────

async def research_market_prices() -> list[dict]:
    """Search for current market prices for Michoacan crops."""
    queries = [
        "avocado price per kg USD 2026",
        "Mexico avocado export price today",
        "berry blueberry price wholesale 2026",
        "lemon price Mexico export",
        "Hass avocado wholesale price April 2026",
    ]

    all_results = []
    for q in queries:
        results = await _search_with_delay(q, max_results=3)
        all_results.extend(results)

    # Also try USDA market news (best effort)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://marketnews.usda.gov/mnp/fv-nav-byCom",
                params={"type": "shipPrice", "commodity": "AVOCADOS"},
            )
            if resp.status_code == 200:
                all_results.append({"title": "USDA Market News", "body": resp.text[:2000], "href": str(resp.url)})
    except Exception:
        pass

    if not all_results:
        return _default_prices()

    # Format search results for Claude
    search_text = "\n\n".join(
        f"Source: {r.get('href', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('body', '')}"
        for r in all_results[:15]
    )

    system = (
        "You are an agricultural commodity price analyst. Extract current market prices "
        "from search results. Return ONLY valid JSON, no other text."
    )
    prompt = f"""Based on these search results about agricultural commodity prices, extract the best current price data.

Search Results:
{search_text}

Today's date: {_today()}

Return a JSON array with objects like:
[
  {{"crop_type": "avocado", "market": "US", "price_per_kg_usd": 3.20, "trend": "up", "source": "source name"}},
  {{"crop_type": "avocado", "market": "EU", "price_per_kg_usd": 3.60, "trend": "stable", "source": "source name"}},
  {{"crop_type": "avocado", "market": "US (organic)", "price_per_kg_usd": 3.50, "trend": "up", "source": "source name"}},
  {{"crop_type": "avocado", "market": "domestic", "price_per_kg_usd": 2.80, "trend": "down", "source": "source name"}},
  {{"crop_type": "berry", "market": "US", "price_per_kg_usd": 5.50, "trend": "up", "source": "source name"}},
  {{"crop_type": "berry", "market": "EU", "price_per_kg_usd": 6.00, "trend": "up", "source": "source name"}},
  {{"crop_type": "berry", "market": "Asia", "price_per_kg_usd": 5.80, "trend": "stable", "source": "source name"}},
  {{"crop_type": "lemon", "market": "US", "price_per_kg_usd": 1.50, "trend": "stable", "source": "source name"}},
  {{"crop_type": "lemon", "market": "domestic", "price_per_kg_usd": 1.20, "trend": "down", "source": "source name"}}
]

crop_type must be one of: avocado, berry, lemon
market can be: US, EU, Asia, domestic, US (organic)
trend must be one of: up, down, stable
Use actual prices from the search results when available. For crops/markets not covered in search results, use your best current knowledge.
Include at least 9 entries covering all crops and major markets."""

    response = await _ask_haiku(system, prompt)
    parsed = _parse_json(response)

    if isinstance(parsed, list) and len(parsed) > 0:
        # Validate entries
        valid = []
        for p in parsed:
            if all(k in p for k in ("crop_type", "market", "price_per_kg_usd", "trend", "source")):
                if p["crop_type"] in ("avocado", "berry", "lemon"):
                    if p["trend"] in ("up", "down", "stable"):
                        valid.append(p)
        if valid:
            return valid

    return _default_prices()


async def research_weather(regions: list[str] | None = None) -> list[dict]:
    """Fetch weather data for Michoacan farming regions.

    Uses Open-Meteo real-time API (no key needed) as primary source.
    Falls back to DuckDuckGo + Claude if Open-Meteo fails.
    """
    # Try Open-Meteo real-time feeds first (no API key needed)
    try:
        from .feeds import fetch_all_farm_weather
        weather_result = await fetch_all_farm_weather()
        alerts = weather_result.get("alerts", [])
        if alerts:
            # Validate and return real alerts
            valid = []
            for w in alerts:
                if all(k in w for k in ("region", "alert_type", "severity", "description", "forecast_date")):
                    if w["alert_type"] in ("frost", "rain", "heat", "wind"):
                        if w["severity"] in ("low", "medium", "high", "critical"):
                            valid.append(w)
            if valid:
                return valid
        # If Open-Meteo returned data but no alerts, weather is fine --
        # generate a minimal "all clear" style alert from actual data
        locations = weather_result.get("locations", [])
        if locations:
            mild_alerts = []
            for loc in locations:
                cur = loc.get("current", {})
                daily = loc.get("daily", [])
                if cur.get("temp_c") is not None:
                    # Find the most notable condition in the 7-day forecast
                    min_temps = [d["temp_min"] for d in daily if d.get("temp_min") is not None]
                    max_precips = [d["precip_mm"] for d in daily if d.get("precip_mm") is not None]
                    lowest = min(min_temps) if min_temps else cur["temp_c"]
                    highest_rain = max(max_precips) if max_precips else 0

                    if lowest < 8:  # Notable cool temps
                        mild_alerts.append({
                            "region": loc["region"],
                            "alert_type": "frost",
                            "severity": "low",
                            "description": (
                                f"Cool temperatures in {loc['region']}: overnight lows reaching {lowest:.1f} C. "
                                f"Currently {cur['temp_c']:.1f} C. No immediate frost risk but monitor conditions."
                            ),
                            "forecast_date": daily[0]["date"] if daily else _today(),
                            "affected_farms": loc["farm_ids"],
                        })
                    elif highest_rain > 10:  # Some rain expected
                        mild_alerts.append({
                            "region": loc["region"],
                            "alert_type": "rain",
                            "severity": "low",
                            "description": (
                                f"Moderate rain expected in {loc['region']}: up to {highest_rain:.1f} mm forecast. "
                                f"Currently {cur['temp_c']:.1f} C. Normal seasonal conditions."
                            ),
                            "forecast_date": daily[0]["date"] if daily else _today(),
                            "affected_farms": loc["farm_ids"],
                        })
            if mild_alerts:
                return mild_alerts
    except Exception:
        pass  # Fall through to DuckDuckGo fallback

    # --- DuckDuckGo + Claude fallback ---
    if regions is None:
        regions = list(REGIONS.keys())

    weather_data = []
    for region in regions:
        results = await _search_with_delay(f"weather {region} Michoacan Mexico today forecast", max_results=3)
        weather_data.append({
            "region": region,
            "search_results": [
                {"title": r.get("title", ""), "body": r.get("body", "")}
                for r in results
            ],
        })

    if not weather_data:
        return _default_weather()

    # Ask Claude to synthesize into weather alerts
    system = (
        "You are an agricultural meteorologist specializing in Michoacan, Mexico. "
        "Analyze weather data and generate alerts ONLY for genuinely concerning conditions. "
        "Return ONLY valid JSON, no other text."
    )

    weather_text = json.dumps(weather_data, indent=2, ensure_ascii=False)
    prompt = f"""Based on this weather data for Michoacan farming regions, generate weather alerts for any concerning agricultural conditions.

Weather Data:
{weather_text}

Today: {_today()}
Farm-to-region mapping: {json.dumps(REGION_FARMS)}

IMPORTANT: Only generate alerts for REAL concerning conditions found in the data. Conditions to watch for:
- Frost: temp below 4C (critical for avocado)
- Heat stress: temp above 35C (critical for berries)
- Heavy rain: >40mm expected (harvest delays, flooding)
- Strong wind: >40 km/h (crop damage)
- Drought: very low humidity + high temp

Return a JSON array (can be empty if no concerning conditions):
[
  {{
    "region": "region name",
    "alert_type": "frost|rain|heat|wind",
    "severity": "low|medium|high|critical",
    "description": "Detailed description of the weather concern and impact on crops",
    "forecast_date": "{_future_date(1)}",
    "affected_farms": ["farm-xxx"]
  }}
]

Generate 3-5 alerts if conditions warrant. If weather is mild, generate 1-2 low/medium alerts for the most notable conditions."""

    response = await _ask_haiku(system, prompt)
    parsed = _parse_json(response)

    if isinstance(parsed, list) and len(parsed) > 0:
        valid = []
        for w in parsed:
            if all(k in w for k in ("region", "alert_type", "severity", "description", "forecast_date")):
                if w["alert_type"] in ("frost", "rain", "heat", "wind"):
                    if w["severity"] in ("low", "medium", "high", "critical"):
                        if "affected_farms" not in w:
                            w["affected_farms"] = REGION_FARMS.get(w["region"], [])
                        valid.append(w)
        if valid:
            return valid

    return _default_weather()


async def research_export_news() -> list[dict]:
    """Search for current Michoacan agricultural export news and insights."""
    queries = [
        "Michoacan avocado export news 2026",
        "Mexico berry export update",
        "USDA phytosanitary Mexico avocado",
        "avocado supply chain Michoacan",
        "Mexico agricultural export statistics 2026",
    ]

    all_results = []
    for q in queries:
        results = await _search_with_delay(q, max_results=3)
        all_results.extend(results)

    if not all_results:
        return _default_insights()

    search_text = "\n\n".join(
        f"Source: {r.get('href', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('body', '')}"
        for r in all_results[:15]
    )

    system = (
        "You are a supply chain intelligence analyst for Mexican agricultural exports. "
        "Synthesize news into actionable insights. Return ONLY valid JSON, no other text."
    )
    prompt = f"""Based on these search results about Michoacan agricultural exports, generate supply chain insights.

Search Results:
{search_text}

Today: {_today()}

Return a JSON array of 6-8 insights:
[
  {{
    "insight_type": "opportunity|risk|optimization",
    "title": "Short actionable title",
    "description": "Detailed description with specific data points from the search results. Reference real entities, numbers, and events.",
    "priority": "low|medium|high|critical",
    "affected_entities": ["farm-001", "ship-001", etc.]
  }}
]

insight_type must be one of: opportunity, risk, optimization
priority must be one of: low, medium, high, critical
For affected_entities use realistic farm IDs (farm-001 through farm-012), shipment IDs (ship-001 through ship-008), buyer IDs (buyer-001 through buyer-006), or weather alert IDs (wx-001 through wx-005).

Make insights specific and actionable, grounded in the actual search results."""

    response = await _ask_haiku(system, prompt)
    parsed = _parse_json(response)

    if isinstance(parsed, list) and len(parsed) > 0:
        valid = []
        for ins in parsed:
            if all(k in ins for k in ("insight_type", "title", "description", "priority")):
                if ins["insight_type"] in ("opportunity", "risk", "optimization"):
                    if ins["priority"] in ("low", "medium", "high", "critical"):
                        if "affected_entities" not in ins:
                            ins["affected_entities"] = []
                        valid.append(ins)
        if valid:
            return valid

    return _default_insights()


async def research_buyer_activity() -> list[dict]:
    """Search for buyer activity and trade patterns for Michoacan exports."""
    queries = [
        "Costco avocado Mexico supplier 2026",
        "Driscoll's berry Mexico Michoacan",
        "Europe avocado import Mexico 2026",
        "Japan avocado import demand 2026",
        "US avocado import volume Mexico wholesale",
    ]

    all_results = []
    for q in queries:
        results = await _search_with_delay(q, max_results=3)
        all_results.extend(results)

    if not all_results:
        return _default_buyers()

    search_text = "\n\n".join(
        f"Source: {r.get('href', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('body', '')}"
        for r in all_results[:12]
    )

    system = (
        "You are a trade intelligence analyst specializing in Mexican agricultural exports. "
        "Generate realistic buyer match data based on current trade activity. "
        "Return ONLY valid JSON, no other text."
    )
    prompt = f"""Based on these search results about Mexican agricultural trade, generate buyer match data for Michoacan farms.

Search Results:
{search_text}

Today: {_today()}

Return a JSON array of 6 buyer matches:
[
  {{
    "buyer_name": "Real company name",
    "country": "US|Mexico|Germany|Japan|UK|Canada",
    "crop_interest": "avocado|berry|lemon",
    "volume_needed_kg": 100000,
    "price_per_kg_usd": 3.20,
    "certification_required": ["organic", "global_gap", "fair_trade"],
    "matched_farms": ["farm-001", "farm-003"]
  }}
]

Requirements:
- Use REAL company names that are actual buyers of Mexican produce (e.g. Costco, Walmart, Driscoll's, Aldi, Aeon, Fresh Del Monte, Kroger, etc.)
- crop_interest must be one of: avocado, berry, lemon
- certification_required items must be from: organic, global_gap, fair_trade (can be empty list)
- matched_farms should be from farm-001 to farm-012 (farm-001 to farm-008 are avocado, farm-009 to farm-011 are berry, farm-012 is lemon)
- Prices should reflect current market reality
- Include at least 3 avocado buyers, 2 berry buyers, and 1 lemon or additional buyer"""

    response = await _ask_haiku(system, prompt)
    parsed = _parse_json(response)

    if isinstance(parsed, list) and len(parsed) > 0:
        valid = []
        for b in parsed:
            if all(k in b for k in ("buyer_name", "country", "crop_interest", "volume_needed_kg", "price_per_kg_usd")):
                if b["crop_interest"] in ("avocado", "berry", "lemon"):
                    if "certification_required" not in b:
                        b["certification_required"] = []
                    # Validate certifications
                    b["certification_required"] = [
                        c for c in b["certification_required"]
                        if c in ("organic", "global_gap", "fair_trade")
                    ]
                    if "matched_farms" not in b:
                        b["matched_farms"] = []
                    valid.append(b)
        if valid:
            return valid

    return _default_buyers()


# ── Main Orchestrator ──────────────────────────────────────────

async def run_all_research() -> dict:
    """Run all research functions concurrently and return combined results.

    Returns dict with keys: prices, weather, insights, buyers.
    Each value is a list of dicts ready to populate demo data.
    Failures in any research function fall back to reasonable defaults.
    """
    results = await asyncio.gather(
        research_market_prices(),
        research_weather(),
        research_export_news(),
        research_buyer_activity(),
        return_exceptions=True,
    )

    prices = results[0] if isinstance(results[0], list) else _default_prices()
    weather = results[1] if isinstance(results[1], list) else _default_weather()
    insights = results[2] if isinstance(results[2], list) else _default_insights()
    buyers = results[3] if isinstance(results[3], list) else _default_buyers()

    return {
        "prices": prices,
        "weather": weather,
        "insights": insights,
        "buyers": buyers,
    }


# ── Default Fallbacks ─────────────────────────────────────────

def _default_prices() -> list[dict]:
    """Reasonable fallback prices if research fails."""
    today = _today()
    return [
        {"crop_type": "avocado", "market": "US", "price_per_kg_usd": 3.20, "trend": "up", "source": "Fallback estimate", "date": today},
        {"crop_type": "avocado", "market": "US (organic)", "price_per_kg_usd": 3.50, "trend": "up", "source": "Fallback estimate", "date": today},
        {"crop_type": "avocado", "market": "EU", "price_per_kg_usd": 3.60, "trend": "stable", "source": "Fallback estimate", "date": today},
        {"crop_type": "avocado", "market": "domestic", "price_per_kg_usd": 2.80, "trend": "down", "source": "Fallback estimate", "date": today},
        {"crop_type": "berry", "market": "US", "price_per_kg_usd": 5.50, "trend": "up", "source": "Fallback estimate", "date": today},
        {"crop_type": "berry", "market": "EU", "price_per_kg_usd": 6.00, "trend": "up", "source": "Fallback estimate", "date": today},
        {"crop_type": "berry", "market": "Asia", "price_per_kg_usd": 5.80, "trend": "stable", "source": "Fallback estimate", "date": today},
        {"crop_type": "lemon", "market": "US", "price_per_kg_usd": 1.50, "trend": "stable", "source": "Fallback estimate", "date": today},
        {"crop_type": "lemon", "market": "domestic", "price_per_kg_usd": 1.20, "trend": "down", "source": "Fallback estimate", "date": today},
    ]


def _default_weather() -> list[dict]:
    """Reasonable fallback weather alerts if research fails."""
    return [
        {
            "region": "Uruapan", "alert_type": "frost", "severity": "high",
            "forecast_date": _future_date(2),
            "description": "Frost warning: temperatures expected to drop below 4C overnight in the Uruapan valley. Protect young avocado trees and recently pollinated fruit.",
            "affected_farms": ["farm-001", "farm-006"],
        },
        {
            "region": "Tancitaro", "alert_type": "rain", "severity": "medium",
            "forecast_date": _future_date(1),
            "description": "Heavy rainfall expected (40-60mm) over the next 48 hours. Potential harvest delays and road access issues on mountain routes.",
            "affected_farms": ["farm-007", "farm-008"],
        },
        {
            "region": "Los Reyes", "alert_type": "heat", "severity": "high",
            "forecast_date": _future_date(3),
            "description": "Heat stress alert: daytime temperatures reaching 35C+. Berry crops at risk of sunburn and accelerated ripening. Increase irrigation frequency.",
            "affected_farms": ["farm-009", "farm-010"],
        },
        {
            "region": "Periban", "alert_type": "wind", "severity": "low",
            "forecast_date": _future_date(4),
            "description": "Moderate winds (30-45 km/h) forecast. Minimal impact expected but secure loose greenhouse covers and irrigation equipment.",
            "affected_farms": ["farm-008"],
        },
        {
            "region": "Tacambaro", "alert_type": "rain", "severity": "critical",
            "forecast_date": _today(),
            "description": "Heavy rainfall bringing 80-100mm expected. Flash flood risk in low-lying berry fields. Harvest immediately if possible.",
            "affected_farms": ["farm-011"],
        },
    ]


def _default_insights() -> list[dict]:
    """Reasonable fallback insights if research fails."""
    now = datetime.now().isoformat()
    return [
        {
            "insight_type": "optimization", "priority": "high",
            "title": "Consolidate Uruapan shipments to reduce per-container cost",
            "description": "Farms 001 and 006 in the Uruapan region are shipping separately to the US. Consolidating into shared containers could save $8,200/month in freight costs while maintaining cold chain integrity.",
            "affected_entities": ["farm-001", "farm-006", "ship-001", "ship-005"],
        },
        {
            "insight_type": "risk", "priority": "critical",
            "title": "Frost risk threatens avocado harvest in Uruapan valley",
            "description": "Weather models predict unusual frost event in the coming days. Farms 001 and 006 should activate frost protection. Estimated loss without action: $85,000 in damaged fruit.",
            "affected_entities": ["farm-001", "farm-006", "wx-001"],
        },
        {
            "insight_type": "opportunity", "priority": "high",
            "title": "EU organic avocado premium at multi-year high",
            "description": "EU organic avocado prices are elevated. Farms with organic certification should prioritize EU shipments. Potential revenue uplift of $45,000/month by redirecting US volume to EU.",
            "affected_entities": ["farm-003", "farm-006", "buyer-003"],
        },
        {
            "insight_type": "risk", "priority": "high",
            "title": "Customs delay risk on active shipments",
            "description": "Customs documentation for shipments to Houston may be incomplete. Average clearance takes 3 days; delays risk demurrage charges. Expedite document submission.",
            "affected_entities": ["ship-003", "doc-007"],
        },
        {
            "insight_type": "optimization", "priority": "medium",
            "title": "Berry cold chain optimization available",
            "description": "Temperature logs for berry shipments show room for improvement. Lowering transit temperature by 0.5C extends shelf life by 2 days, reducing spoilage losses by an estimated 4%.",
            "affected_entities": ["ship-006", "farm-009", "farm-010"],
        },
        {
            "insight_type": "opportunity", "priority": "medium",
            "title": "Berry buyer volume increase opportunity for Q2",
            "description": "Major berry buyers have indicated willingness to increase Q2 orders by 25%. Farms 009-011 have capacity if weather cooperates. Estimated additional revenue: $123,750.",
            "affected_entities": ["buyer-005", "farm-009", "farm-010", "farm-011"],
        },
        {
            "insight_type": "risk", "priority": "medium",
            "title": "Quality control concern in berry operations",
            "description": "Recent quality inspections have flagged potential contamination issues. Investigation and corrective measures recommended to maintain export certification.",
            "affected_entities": ["farm-011", "harv-026", "qi-010"],
        },
        {
            "insight_type": "optimization", "priority": "low",
            "title": "Consider redirecting lemon exports to domestic market",
            "description": "Current US lemon prices barely cover export logistics costs. Domestic market with zero export overhead may yield better net margin for farm-012.",
            "affected_entities": ["farm-012"],
        },
    ]


def _default_buyers() -> list[dict]:
    """Reasonable fallback buyer data if research fails."""
    return [
        {
            "buyer_name": "Costco Wholesale", "country": "US",
            "crop_interest": "avocado", "volume_needed_kg": 200000,
            "price_per_kg_usd": 3.20,
            "certification_required": ["global_gap"],
            "matched_farms": ["farm-001", "farm-003", "farm-007"],
        },
        {
            "buyer_name": "Walmart Mexico", "country": "Mexico",
            "crop_interest": "avocado", "volume_needed_kg": 150000,
            "price_per_kg_usd": 2.80,
            "certification_required": [],
            "matched_farms": ["farm-002", "farm-004", "farm-005"],
        },
        {
            "buyer_name": "Aldi Europe", "country": "Germany",
            "crop_interest": "avocado", "volume_needed_kg": 120000,
            "price_per_kg_usd": 3.50,
            "certification_required": ["organic", "global_gap"],
            "matched_farms": ["farm-006", "farm-008"],
        },
        {
            "buyer_name": "Fresh Del Monte", "country": "US",
            "crop_interest": "avocado", "volume_needed_kg": 180000,
            "price_per_kg_usd": 3.10,
            "certification_required": ["global_gap"],
            "matched_farms": ["farm-001", "farm-007"],
        },
        {
            "buyer_name": "Driscoll's", "country": "US",
            "crop_interest": "berry", "volume_needed_kg": 90000,
            "price_per_kg_usd": 5.50,
            "certification_required": ["global_gap", "fair_trade"],
            "matched_farms": ["farm-009", "farm-010", "farm-011"],
        },
        {
            "buyer_name": "Aeon Japan", "country": "Japan",
            "crop_interest": "berry", "volume_needed_kg": 45000,
            "price_per_kg_usd": 6.00,
            "certification_required": ["organic"],
            "matched_farms": ["farm-009", "farm-010"],
        },
    ]
