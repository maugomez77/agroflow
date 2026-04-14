"""AI analysis functions for AgroFlow Intelligence.

Calls Claude (Sonnet) for supply chain intelligence.
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic

MODEL = "claude-sonnet-4-20250514"


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _ask(system: str, prompt: str) -> str:
    """Send a prompt to Claude and return the text response."""
    client = _client()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _to_json(text: str) -> dict | list:
    """Try to parse JSON from Claude's response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to extract JSON block
    for marker in ("```json", "```"):
        if marker in text:
            start = text.index(marker) + len(marker)
            end = text.index("```", start)
            return json.loads(text[start:end].strip())
    return {"raw": text}


SYSTEM = (
    "You are an expert agricultural supply chain analyst specializing in "
    "Mexican avocado and berry exports from Michoacan. Respond with actionable, "
    "data-driven insights. Return valid JSON when asked."
)


def analyze_supply_chain(farms: list[dict], harvests: list[dict], shipments: list[dict]) -> dict:
    """Full supply chain analysis with optimization suggestions."""
    prompt = f"""Analyze this Michoacan agricultural supply chain and provide optimization suggestions.

Farms: {json.dumps(farms[:6], indent=2)}
Recent Harvests: {json.dumps(harvests[:10], indent=2)}
Active Shipments: {json.dumps([{{k: v for k, v in s.items() if k != 'temperature_logs'}} for s in shipments], indent=2)}

Return JSON with:
{{
  "summary": "brief overall assessment",
  "optimizations": [
    {{"title": "...", "description": "...", "estimated_savings_usd": 0, "priority": "high/medium/low"}}
  ],
  "risks": [
    {{"title": "...", "description": "...", "likelihood": "high/medium/low", "impact_usd": 0}}
  ],
  "kpis": {{
    "utilization_pct": 0,
    "quality_rate_pct": 0,
    "on_time_delivery_pct": 0
  }}
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def predict_yield(farm: dict, weather_data: list[dict]) -> dict:
    """AI yield prediction for a specific farm."""
    prompt = f"""Predict the next harvest yield for this farm given current weather conditions.

Farm: {json.dumps(farm, indent=2)}
Weather Alerts: {json.dumps(weather_data, indent=2)}

Return JSON with:
{{
  "farm_name": "...",
  "predicted_yield_kg": 0,
  "confidence_pct": 0,
  "factors": ["..."],
  "recommendations": ["..."],
  "risk_adjustment_pct": 0
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def match_buyers(harvests: list[dict], buyers: list[dict]) -> dict:
    """Recommend buyer-harvest matches with reasoning."""
    prompt = f"""Match these available harvests with buyer requirements. Optimize for price, volume fit, and certification match.

Available Harvests: {json.dumps(harvests[:10], indent=2)}
Buyers: {json.dumps(buyers, indent=2)}

Return JSON with:
{{
  "matches": [
    {{
      "buyer": "...",
      "harvests": ["harv-xxx"],
      "total_kg": 0,
      "revenue_usd": 0,
      "match_score": 0.0,
      "reasoning": "..."
    }}
  ],
  "unmatched_volume_kg": 0,
  "total_potential_revenue_usd": 0
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def assess_risk(shipments: list[dict], weather: list[dict]) -> dict:
    """Risk assessment for active shipments and weather threats."""
    prompt = f"""Assess risks for these active agricultural shipments and weather conditions in Michoacan.

Active Shipments: {json.dumps([{{k: v for k, v in s.items() if k != 'temperature_logs'}} for s in shipments], indent=2)}
Weather Alerts: {json.dumps(weather, indent=2)}

Return JSON with:
{{
  "overall_risk_level": "low/medium/high/critical",
  "risks": [
    {{
      "entity": "ship-xxx or farm-xxx",
      "risk_type": "weather/logistics/quality/regulatory",
      "description": "...",
      "probability_pct": 0,
      "potential_loss_usd": 0,
      "mitigation": "..."
    }}
  ],
  "immediate_actions": ["..."]
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def optimize_logistics(shipments: list[dict]) -> dict:
    """Routing and timing optimization suggestions."""
    prompt = f"""Optimize logistics for these agricultural shipments from Michoacan, Mexico.

Shipments: {json.dumps(shipments, indent=2)}

Consider: port selection (Lazaro Cardenas vs Manzanillo), carrier efficiency, container consolidation, cold chain requirements, customs processing times.

Return JSON with:
{{
  "recommendations": [
    {{
      "shipment_id": "...",
      "suggestion": "...",
      "estimated_savings_usd": 0,
      "time_saved_days": 0
    }}
  ],
  "consolidation_opportunities": ["..."],
  "total_potential_savings_usd": 0
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def assess_phytosanitary_risk(
    certificate: dict,
    requirements: list[dict],
    historical_rejections: list[dict] | None = None,
) -> dict:
    """AI-powered SENASICA → APHIS rejection-risk analysis with mitigation plan."""
    prompt = f"""You are a Mexican phytosanitary compliance expert advising avocado/berry/flower
exporters from Michoacán and Estado de México. Analyze this certificate against APHIS/SENASICA
requirements and provide a rejection-risk assessment.

Certificate: {json.dumps(certificate, indent=2)}

Required SENASICA/APHIS rules: {json.dumps(requirements, indent=2)}

Historical rejections (recent): {json.dumps(historical_rejections or [], indent=2)}

Return JSON with:
{{
  "risk_level": "very_low/low/medium/high/critical",
  "risk_score": 0.0,
  "primary_concerns": ["..."],
  "mitigation_steps": [
    {{"action": "...", "owner": "exporter/SENASICA/USDA APHIS", "deadline_days": 0, "priority": "high/medium/low"}}
  ],
  "estimated_processing_days": 0,
  "estimated_loss_if_rejected_usd": 0,
  "comparable_rejections_summary": "..."
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def optimize_cooperative_pooling(cooperative: dict, member_harvests: list[dict], buyers: list[dict]) -> dict:
    """Suggest how a cooperative should pool its members' harvests for maximum revenue."""
    prompt = f"""You are advising a Mexican agricultural cooperative on optimal harvest pooling
and buyer allocation. The cooperative aggregates harvests from member farms and negotiates
collectively with international buyers.

Cooperative: {json.dumps(cooperative, indent=2)}
Member Harvests (recent): {json.dumps(member_harvests[:25], indent=2)}
Available Buyers: {json.dumps(buyers, indent=2)}

Return JSON with:
{{
  "summary": "...",
  "pooling_strategy": [
    {{"buyer": "...", "harvest_ids": ["harv-xxx"], "total_kg": 0, "revenue_usd": 0, "rationale": "..."}}
  ],
  "member_distribution": [
    {{"farm_id": "farm-xxx", "share_pct": 0.0, "estimated_payout_usd": 0}}
  ],
  "negotiation_leverage_points": ["..."],
  "total_pooled_revenue_usd": 0,
  "vs_individual_selling_uplift_pct": 0
}}"""
    return _to_json(_ask(SYSTEM, prompt))


def generate_market_report(prices: list[dict], trends: list[dict] | None = None) -> dict:
    """Generate a comprehensive market analysis report."""
    prompt = f"""Generate a market intelligence report for Michoacan agricultural exports.

Current Prices: {json.dumps(prices, indent=2)}

Cover: price trends, demand outlook, competitive landscape, seasonal patterns, and export recommendations for avocado, berry, and lemon crops.

Return JSON with:
{{
  "report_date": "2026-04-04",
  "executive_summary": "...",
  "crop_analyses": [
    {{
      "crop": "avocado/berry/lemon",
      "current_price_range_usd": "x.xx - x.xx",
      "trend": "up/down/stable",
      "demand_outlook": "...",
      "key_markets": ["..."],
      "recommendation": "..."
    }}
  ],
  "market_risks": ["..."],
  "opportunities": ["..."]
}}"""
    return _to_json(_ask(SYSTEM, prompt))
