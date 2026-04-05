"""Demo data generator for AgroFlow Intelligence.

Generates realistic Michoacan agricultural supply chain data,
enhanced with real-time market research when available.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from .models import (
    BuyerMatch,
    CertificationType,
    CropType,
    DemoStats,
    ExportDocument,
    Farm,
    Harvest,
    MarketPrice,
    QualityInspection,
    Shipment,
    SupplyChainInsight,
    TempReading,
    WeatherAlert,
)
from . import store


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _date_offset(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now().isoformat()


def _build_price_lookup(prices: list[dict]) -> dict[tuple[str, str], float]:
    """Build a (crop_type, market) -> price lookup from research prices."""
    lookup: dict[tuple[str, str], float] = {}
    for p in prices:
        key = (p.get("crop_type", ""), p.get("market", ""))
        lookup[key] = p.get("price_per_kg_usd", 0)
    return lookup


def _get_price(lookup: dict, crop: str, grade: str) -> float:
    """Get price per kg for a crop, adjusted by grade."""
    # Try US market first, then any available
    price = lookup.get((crop, "US"), 0)
    if not price:
        for (c, _m), p in lookup.items():
            if c == crop and p > 0:
                price = p
                break
    # Fallback defaults
    if not price:
        price = {"avocado": 3.00, "berry": 5.00, "lemon": 1.50}.get(crop, 2.00)
    # Grade adjustment
    if grade == "A":
        return price
    elif grade == "B":
        return price * 0.80
    else:
        return price * 0.55


async def async_generate_demo_data() -> None:
    """Generate and persist demo data, enriched with real-time research."""
    from .research import run_all_research

    # Run real-time research
    research = await run_all_research()

    # Extract research data
    real_prices = research.get("prices", [])
    real_weather = research.get("weather", [])
    real_insights = research.get("insights", [])
    real_buyers = research.get("buyers", [])

    price_lookup = _build_price_lookup(real_prices)

    # ── Farms (12) — kept as-is (real Michoacan locations) ─────
    farms = [
        Farm(id="farm-001", name="Rancho Los Aguacates", location_lat=19.4181, location_lng=-102.0534,
             crop_type=CropType.avocado, hectares=65, owner="Juan Carlos Mendoza",
             contact="+52 452 123 4567", created_at="2024-03-15T10:00:00"),
        Farm(id="farm-002", name="Huerta El Paraiso", location_lat=19.3467, location_lng=-102.2256,
             crop_type=CropType.avocado, hectares=42, owner="Maria Elena Gutierrez",
             contact="+52 452 234 5678", created_at="2023-11-20T08:00:00"),
        Farm(id="farm-003", name="Finca San Miguel", location_lat=19.5012, location_lng=-102.0678,
             crop_type=CropType.avocado, hectares=55, owner="Roberto Alvarez Perez",
             contact="+52 452 345 6789", created_at="2024-01-10T09:30:00"),
        Farm(id="farm-004", name="Rancho La Esperanza", location_lat=19.3789, location_lng=-102.1345,
             crop_type=CropType.avocado, hectares=38, owner="Ana Patricia Ramirez",
             contact="+52 452 456 7890", created_at="2024-06-05T11:00:00"),
        Farm(id="farm-005", name="Huerta Don Sergio", location_lat=19.2901, location_lng=-102.3012,
             crop_type=CropType.avocado, hectares=28, owner="Sergio Hernandez Luna",
             contact="+52 452 567 8901", created_at="2025-02-14T07:45:00"),
        Farm(id="farm-006", name="Aguacates del Valle", location_lat=19.4567, location_lng=-102.1890,
             crop_type=CropType.avocado, hectares=50, owner="Fernando Castillo Ortiz",
             contact="+52 452 678 9012", created_at="2024-08-22T10:15:00"),
        Farm(id="farm-007", name="Finca Tancitaro Gold", location_lat=19.3456, location_lng=-102.3567,
             crop_type=CropType.avocado, hectares=72, owner="Luis Miguel Torres",
             contact="+52 452 789 0123", created_at="2023-05-30T08:00:00"),
        Farm(id="farm-008", name="Rancho Verde Periban", location_lat=19.5134, location_lng=-102.4012,
             crop_type=CropType.avocado, hectares=35, owner="Carmen Diaz Flores",
             contact="+52 452 890 1234", created_at="2024-11-01T09:00:00"),
        Farm(id="farm-009", name="Berries Los Reyes", location_lat=19.5823, location_lng=-102.4734,
             crop_type=CropType.berry, hectares=22, owner="Patricia Morales Vega",
             contact="+52 354 123 4567", created_at="2024-04-18T10:30:00"),
        Farm(id="farm-010", name="Frutillas del Sur", location_lat=19.5567, location_lng=-102.5001,
             crop_type=CropType.berry, hectares=18, owner="Jorge Navarro Cruz",
             contact="+52 354 234 5678", created_at="2025-01-08T08:15:00"),
        Farm(id="farm-011", name="Berry Paradise Tacambaro", location_lat=19.2345, location_lng=-101.4567,
             crop_type=CropType.berry, hectares=15, owner="Isabel Dominguez Ramos",
             contact="+52 459 345 6789", created_at="2024-09-12T11:45:00"),
        Farm(id="farm-012", name="Citricos Ario", location_lat=19.2012, location_lng=-101.7234,
             crop_type=CropType.lemon, hectares=10, owner="Ricardo Soto Jimenez",
             contact="+52 459 456 7890", created_at="2025-03-01T07:30:00"),
    ]

    # ── Harvests (30) — values adjusted to real prices ────────
    def _val(qty: float, crop: str, grade: str) -> float:
        return round(qty * _get_price(price_lookup, crop, grade), 0)

    harvests = [
        # Avocado harvests (farm-001 to farm-008)
        Harvest(id="harv-001", farm_id="farm-001", crop_type=CropType.avocado,
                quantity_kg=58500, quality_grade="A", harvest_date=_date_offset(-34),
                estimated_value_usd=_val(58500, "avocado", "A")),
        Harvest(id="harv-002", farm_id="farm-001", crop_type=CropType.avocado,
                quantity_kg=52000, quality_grade="A", harvest_date=_date_offset(-20),
                estimated_value_usd=_val(52000, "avocado", "A")),
        Harvest(id="harv-003", farm_id="farm-002", crop_type=CropType.avocado,
                quantity_kg=37800, quality_grade="A", harvest_date=_date_offset(-30),
                estimated_value_usd=_val(37800, "avocado", "A")),
        Harvest(id="harv-004", farm_id="farm-002", crop_type=CropType.avocado,
                quantity_kg=33600, quality_grade="B", harvest_date=_date_offset(-15),
                estimated_value_usd=_val(33600, "avocado", "B")),
        Harvest(id="harv-005", farm_id="farm-003", crop_type=CropType.avocado,
                quantity_kg=49500, quality_grade="A", harvest_date=_date_offset(-37),
                estimated_value_usd=_val(49500, "avocado", "A")),
        Harvest(id="harv-006", farm_id="farm-003", crop_type=CropType.avocado,
                quantity_kg=44000, quality_grade="B", harvest_date=_date_offset(-17),
                estimated_value_usd=_val(44000, "avocado", "B")),
        Harvest(id="harv-007", farm_id="farm-004", crop_type=CropType.avocado,
                quantity_kg=34200, quality_grade="A", harvest_date=_date_offset(-33),
                estimated_value_usd=_val(34200, "avocado", "A")),
        Harvest(id="harv-008", farm_id="farm-004", crop_type=CropType.avocado,
                quantity_kg=30400, quality_grade="B", harvest_date=_date_offset(-13),
                estimated_value_usd=_val(30400, "avocado", "B")),
        Harvest(id="harv-009", farm_id="farm-005", crop_type=CropType.avocado,
                quantity_kg=22400, quality_grade="A", harvest_date=_date_offset(-27),
                estimated_value_usd=_val(22400, "avocado", "A")),
        Harvest(id="harv-010", farm_id="farm-005", crop_type=CropType.avocado,
                quantity_kg=19600, quality_grade="C", harvest_date=_date_offset(-10),
                estimated_value_usd=_val(19600, "avocado", "C")),
        Harvest(id="harv-011", farm_id="farm-006", crop_type=CropType.avocado,
                quantity_kg=45000, quality_grade="A", harvest_date=_date_offset(-32),
                estimated_value_usd=_val(45000, "avocado", "A")),
        Harvest(id="harv-012", farm_id="farm-006", crop_type=CropType.avocado,
                quantity_kg=40000, quality_grade="A", harvest_date=_date_offset(-16),
                estimated_value_usd=_val(40000, "avocado", "A")),
        Harvest(id="harv-013", farm_id="farm-007", crop_type=CropType.avocado,
                quantity_kg=64800, quality_grade="A", harvest_date=_date_offset(-40),
                estimated_value_usd=_val(64800, "avocado", "A")),
        Harvest(id="harv-014", farm_id="farm-007", crop_type=CropType.avocado,
                quantity_kg=57600, quality_grade="A", harvest_date=_date_offset(-23),
                estimated_value_usd=_val(57600, "avocado", "A")),
        Harvest(id="harv-015", farm_id="farm-007", crop_type=CropType.avocado,
                quantity_kg=50400, quality_grade="B", harvest_date=_date_offset(-7),
                estimated_value_usd=_val(50400, "avocado", "B")),
        Harvest(id="harv-016", farm_id="farm-008", crop_type=CropType.avocado,
                quantity_kg=31500, quality_grade="A", harvest_date=_date_offset(-29),
                estimated_value_usd=_val(31500, "avocado", "A")),
        Harvest(id="harv-017", farm_id="farm-008", crop_type=CropType.avocado,
                quantity_kg=28000, quality_grade="B", harvest_date=_date_offset(-11),
                estimated_value_usd=_val(28000, "avocado", "B")),
        # Berry harvests (farm-009, farm-010, farm-011)
        Harvest(id="harv-018", farm_id="farm-009", crop_type=CropType.berry,
                quantity_kg=39600, quality_grade="A", harvest_date=_date_offset(-34),
                estimated_value_usd=_val(39600, "berry", "A")),
        Harvest(id="harv-019", farm_id="farm-009", crop_type=CropType.berry,
                quantity_kg=35200, quality_grade="A", harvest_date=_date_offset(-21),
                estimated_value_usd=_val(35200, "berry", "A")),
        Harvest(id="harv-020", farm_id="farm-009", crop_type=CropType.berry,
                quantity_kg=33000, quality_grade="B", harvest_date=_date_offset(-7),
                estimated_value_usd=_val(33000, "berry", "B")),
        Harvest(id="harv-021", farm_id="farm-010", crop_type=CropType.berry,
                quantity_kg=32400, quality_grade="A", harvest_date=_date_offset(-31),
                estimated_value_usd=_val(32400, "berry", "A")),
        Harvest(id="harv-022", farm_id="farm-010", crop_type=CropType.berry,
                quantity_kg=27000, quality_grade="A", harvest_date=_date_offset(-17),
                estimated_value_usd=_val(27000, "berry", "A")),
        Harvest(id="harv-023", farm_id="farm-010", crop_type=CropType.berry,
                quantity_kg=25200, quality_grade="B", harvest_date=_date_offset(-5),
                estimated_value_usd=_val(25200, "berry", "B")),
        Harvest(id="harv-024", farm_id="farm-011", crop_type=CropType.berry,
                quantity_kg=27000, quality_grade="A", harvest_date=_date_offset(-28),
                estimated_value_usd=_val(27000, "berry", "A")),
        Harvest(id="harv-025", farm_id="farm-011", crop_type=CropType.berry,
                quantity_kg=22500, quality_grade="A", harvest_date=_date_offset(-14),
                estimated_value_usd=_val(22500, "berry", "A")),
        Harvest(id="harv-026", farm_id="farm-011", crop_type=CropType.berry,
                quantity_kg=18000, quality_grade="C", harvest_date=_date_offset(-3),
                estimated_value_usd=_val(18000, "berry", "C")),
        # Lemon harvests (farm-012)
        Harvest(id="harv-027", farm_id="farm-012", crop_type=CropType.lemon,
                quantity_kg=12000, quality_grade="A", harvest_date=_date_offset(-25),
                estimated_value_usd=_val(12000, "lemon", "A")),
        Harvest(id="harv-028", farm_id="farm-012", crop_type=CropType.lemon,
                quantity_kg=10800, quality_grade="A", harvest_date=_date_offset(-13),
                estimated_value_usd=_val(10800, "lemon", "A")),
        Harvest(id="harv-029", farm_id="farm-012", crop_type=CropType.lemon,
                quantity_kg=9600, quality_grade="B", harvest_date=_date_offset(-4),
                estimated_value_usd=_val(9600, "lemon", "B")),
        Harvest(id="harv-030", farm_id="farm-012", crop_type=CropType.lemon,
                quantity_kg=8400, quality_grade="B", harvest_date=_date_offset(-2),
                estimated_value_usd=_val(8400, "lemon", "B")),
    ]

    # ── Shipments (8) — ETAs adjusted to current dates ────────
    shipments = [
        Shipment(
            id="ship-001", harvest_ids=["harv-001", "harv-003", "harv-005"],
            destination="US", status="in_transit", carrier="Maersk",
            container_id="MSKU-7234561", departure_date=_date_offset(-15), eta=_date_offset(4),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-15)}T08:00:00", temperature_c=4.2, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-13)}T14:00:00", temperature_c=4.5, location="Pacific Ocean"),
                TempReading(timestamp=f"{_date_offset(-10)}T06:00:00", temperature_c=4.1, location="Approaching LA"),
                TempReading(timestamp=f"{_date_offset(-7)}T10:00:00", temperature_c=4.3, location="Long Beach Port"),
            ],
            documents=["doc-001", "doc-002", "doc-003"],
        ),
        Shipment(
            id="ship-002", harvest_ids=["harv-007", "harv-011"],
            destination="US", status="in_transit", carrier="MSC",
            container_id="MSCU-4891023", departure_date=_date_offset(-13), eta=_date_offset(6),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-13)}T10:00:00", temperature_c=4.0, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-10)}T12:00:00", temperature_c=4.3, location="Pacific Ocean"),
                TempReading(timestamp=f"{_date_offset(-7)}T08:00:00", temperature_c=4.1, location="En route San Diego"),
            ],
            documents=["doc-004", "doc-005"],
        ),
        Shipment(
            id="ship-003", harvest_ids=["harv-013", "harv-014"],
            destination="US", status="customs", carrier="Hapag-Lloyd",
            container_id="HLCU-3456789", departure_date=_date_offset(-20), eta=_date_offset(1),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-20)}T06:00:00", temperature_c=3.9, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-17)}T14:00:00", temperature_c=4.2, location="Pacific Ocean"),
                TempReading(timestamp=f"{_date_offset(-13)}T08:00:00", temperature_c=4.0, location="Near Houston"),
                TempReading(timestamp=f"{_date_offset(-10)}T16:00:00", temperature_c=4.4, location="Houston Port"),
                TempReading(timestamp=f"{_date_offset(-7)}T10:00:00", temperature_c=4.1, location="US Customs Houston"),
            ],
            documents=["doc-006", "doc-007"],
        ),
        Shipment(
            id="ship-004", harvest_ids=["harv-016", "harv-009"],
            destination="US", status="preparing", carrier="Maersk",
            container_id="MSKU-8901234", departure_date=_date_offset(1), eta=_date_offset(18),
            temperature_logs=[],
            documents=["doc-008"],
        ),
        Shipment(
            id="ship-005", harvest_ids=["harv-002", "harv-012"],
            destination="US", status="in_transit", carrier="MSC",
            container_id="MSCU-5678901", departure_date=_date_offset(-10), eta=_date_offset(8),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-10)}T09:00:00", temperature_c=4.1, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-7)}T15:00:00", temperature_c=4.4, location="Pacific Ocean"),
            ],
            documents=["doc-009"],
        ),
        Shipment(
            id="ship-006", harvest_ids=["harv-018", "harv-021"],
            destination="EU", status="in_transit", carrier="Hapag-Lloyd",
            container_id="HLCU-6789012", departure_date=_date_offset(-17), eta=_date_offset(11),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-17)}T07:00:00", temperature_c=2.1, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-13)}T12:00:00", temperature_c=2.3, location="Atlantic Ocean"),
                TempReading(timestamp=f"{_date_offset(-9)}T10:00:00", temperature_c=2.0, location="Mid-Atlantic"),
                TempReading(timestamp=f"{_date_offset(-5)}T08:00:00", temperature_c=2.2, location="Approaching Rotterdam"),
            ],
            documents=["doc-010", "doc-011"],
        ),
        Shipment(
            id="ship-007", harvest_ids=["harv-019", "harv-024"],
            destination="EU", status="preparing", carrier="Maersk",
            container_id="MSKU-2345678", departure_date=_date_offset(4), eta=_date_offset(28),
            temperature_logs=[],
            documents=["doc-012"],
        ),
        Shipment(
            id="ship-008", harvest_ids=["harv-022", "harv-027"],
            destination="Asia", status="in_transit", carrier="MSC",
            container_id="MSCU-9012345", departure_date=_date_offset(-15), eta=_date_offset(14),
            temperature_logs=[
                TempReading(timestamp=f"{_date_offset(-15)}T06:00:00", temperature_c=3.0, location="Lazaro Cardenas Port"),
                TempReading(timestamp=f"{_date_offset(-11)}T14:00:00", temperature_c=3.2, location="Pacific Ocean"),
                TempReading(timestamp=f"{_date_offset(-7)}T10:00:00", temperature_c=3.1, location="Mid-Pacific"),
            ],
            documents=[],
        ),
    ]

    # ── Buyer Matches (6) — from research ─────────────────────
    buyer_matches = []
    for idx, b in enumerate(real_buyers[:6], start=1):
        buyer_matches.append(BuyerMatch(
            id=f"buyer-{idx:03d}",
            buyer_name=b["buyer_name"],
            country=b["country"],
            crop_interest=CropType(b["crop_interest"]),
            volume_needed_kg=b["volume_needed_kg"],
            price_per_kg_usd=b["price_per_kg_usd"],
            certification_required=[CertificationType(c) for c in b.get("certification_required", [])
                                    if c in ("organic", "global_gap", "fair_trade")],
            matched_farms=b.get("matched_farms", []),
        ))

    # ── Weather Alerts — from research ────────────────────────
    weather_alerts = []
    for idx, w in enumerate(real_weather[:5], start=1):
        alert_type = w.get("alert_type", "rain")
        if alert_type not in ("frost", "rain", "heat", "wind"):
            alert_type = "rain"
        severity = w.get("severity", "medium")
        if severity not in ("low", "medium", "high", "critical"):
            severity = "medium"
        weather_alerts.append(WeatherAlert(
            id=f"wx-{idx:03d}",
            region=w.get("region", "Uruapan"),
            alert_type=alert_type,
            severity=severity,
            forecast_date=w.get("forecast_date", _date_offset(idx)),
            description=w.get("description", "Weather alert for farming region."),
            affected_farms=w.get("affected_farms", []),
        ))

    # ── Market Prices — from research ─────────────────────────
    today = _today()
    market_prices = []
    for p in real_prices:
        crop = p.get("crop_type", "avocado")
        if crop not in ("avocado", "berry", "lemon"):
            continue
        trend = p.get("trend", "stable")
        if trend not in ("up", "down", "stable"):
            trend = "stable"
        market_prices.append(MarketPrice(
            crop_type=CropType(crop),
            market=p.get("market", "US"),
            price_per_kg_usd=p.get("price_per_kg_usd", 3.00),
            trend=trend,
            date=p.get("date", today),
            source=p.get("source", "Market research"),
        ))

    # ── Quality Inspections (10) — kept as structural data ────
    quality_inspections = [
        QualityInspection(id="qi-001", harvest_id="harv-001", inspector="Ing. Carlos Reyes",
                          ph_level=6.2, brix_level=8.5, defect_pct=1.2,
                          pesticide_residue=False, certification_status="GlobalG.A.P. Certified",
                          inspection_date=_date_offset(-33)),
        QualityInspection(id="qi-002", harvest_id="harv-003", inspector="Ing. Laura Medina",
                          ph_level=6.0, brix_level=9.1, defect_pct=2.1,
                          pesticide_residue=False, certification_status="GlobalG.A.P. Certified",
                          inspection_date=_date_offset(-29)),
        QualityInspection(id="qi-003", harvest_id="harv-005", inspector="Ing. Carlos Reyes",
                          ph_level=5.8, brix_level=8.8, defect_pct=1.5,
                          pesticide_residue=False, certification_status="Organic + GlobalG.A.P.",
                          inspection_date=_date_offset(-36)),
        QualityInspection(id="qi-004", harvest_id="harv-013", inspector="Ing. Miguel Sanchez",
                          ph_level=6.1, brix_level=9.3, defect_pct=0.8,
                          pesticide_residue=False, certification_status="GlobalG.A.P. Certified",
                          inspection_date=_date_offset(-39)),
        QualityInspection(id="qi-005", harvest_id="harv-010", inspector="Ing. Laura Medina",
                          ph_level=6.5, brix_level=7.2, defect_pct=7.5,
                          pesticide_residue=False, certification_status="Grade C -- domestic only",
                          inspection_date=_date_offset(-9)),
        QualityInspection(id="qi-006", harvest_id="harv-018", inspector="Ing. Sofia Vargas",
                          ph_level=3.4, brix_level=12.5, defect_pct=2.0,
                          pesticide_residue=False, certification_status="GlobalG.A.P. + Fair Trade",
                          inspection_date=_date_offset(-33)),
        QualityInspection(id="qi-007", harvest_id="harv-021", inspector="Ing. Sofia Vargas",
                          ph_level=3.2, brix_level=13.1, defect_pct=1.8,
                          pesticide_residue=False, certification_status="GlobalG.A.P. Certified",
                          inspection_date=_date_offset(-30)),
        QualityInspection(id="qi-008", harvest_id="harv-024", inspector="Ing. Laura Medina",
                          ph_level=3.5, brix_level=11.8, defect_pct=3.2,
                          pesticide_residue=False, certification_status="Organic Certified",
                          inspection_date=_date_offset(-27)),
        QualityInspection(id="qi-009", harvest_id="harv-027", inspector="Ing. Miguel Sanchez",
                          ph_level=2.3, brix_level=7.0, defect_pct=4.5,
                          pesticide_residue=False, certification_status="Pending inspection",
                          inspection_date=_date_offset(-24)),
        QualityInspection(id="qi-010", harvest_id="harv-026", inspector="Ing. Sofia Vargas",
                          ph_level=3.8, brix_level=10.2, defect_pct=8.0,
                          pesticide_residue=True, certification_status="REJECTED -- residue detected",
                          inspection_date=_date_offset(-2)),
    ]

    # ── Export Documents (12) — dates adjusted ────────────────
    export_documents = [
        ExportDocument(id="doc-001", shipment_id="ship-001", doc_type="phytosanitary",
                       status="approved", issued_date=_date_offset(-17), expiry_date=_date_offset(73)),
        ExportDocument(id="doc-002", shipment_id="ship-001", doc_type="customs",
                       status="approved", issued_date=_date_offset(-16), expiry_date=_date_offset(14)),
        ExportDocument(id="doc-003", shipment_id="ship-001", doc_type="origin",
                       status="approved", issued_date=_date_offset(-17), expiry_date=_date_offset(163)),
        ExportDocument(id="doc-004", shipment_id="ship-002", doc_type="phytosanitary",
                       status="approved", issued_date=_date_offset(-15), expiry_date=_date_offset(75)),
        ExportDocument(id="doc-005", shipment_id="ship-002", doc_type="customs",
                       status="approved", issued_date=_date_offset(-14), expiry_date=_date_offset(16)),
        ExportDocument(id="doc-006", shipment_id="ship-003", doc_type="phytosanitary",
                       status="approved", issued_date=_date_offset(-22), expiry_date=_date_offset(68)),
        ExportDocument(id="doc-007", shipment_id="ship-003", doc_type="customs",
                       status="pending", issued_date=_date_offset(-21), expiry_date=_date_offset(9)),
        ExportDocument(id="doc-008", shipment_id="ship-004", doc_type="phytosanitary",
                       status="pending", issued_date=_date_offset(-2), expiry_date=_date_offset(88)),
        ExportDocument(id="doc-009", shipment_id="ship-005", doc_type="phytosanitary",
                       status="approved", issued_date=_date_offset(-12), expiry_date=_date_offset(78)),
        ExportDocument(id="doc-010", shipment_id="ship-006", doc_type="phytosanitary",
                       status="approved", issued_date=_date_offset(-19), expiry_date=_date_offset(71)),
        ExportDocument(id="doc-011", shipment_id="ship-006", doc_type="invoice",
                       status="approved", issued_date=_date_offset(-18), expiry_date=_date_offset(12)),
        ExportDocument(id="doc-012", shipment_id="ship-007", doc_type="phytosanitary",
                       status="pending", issued_date=_date_offset(-1), expiry_date=_date_offset(89)),
    ]

    # ── Supply Chain Insights — from research ─────────────────
    insights = []
    now = _now_iso()
    for idx, ins in enumerate(real_insights[:8], start=1):
        insight_type = ins.get("insight_type", "optimization")
        if insight_type not in ("optimization", "risk", "opportunity"):
            insight_type = "optimization"
        priority = ins.get("priority", "medium")
        if priority not in ("low", "medium", "high", "critical"):
            priority = "medium"
        insights.append(SupplyChainInsight(
            id=f"ins-{idx:03d}",
            insight_type=insight_type,
            title=ins.get("title", "Supply chain insight"),
            description=ins.get("description", ""),
            affected_entities=ins.get("affected_entities", []),
            priority=priority,
            created_at=now,
        ))

    # ── Stats — computed from actual data ─────────────────────
    total_hectares = sum(f.hectares for f in farms)
    revenue_ytd = sum(h.estimated_value_usd for h in harvests)
    total_kg = sum(h.quantity_kg for h in harvests)
    stats = DemoStats(
        total_farms=len(farms),
        total_hectares=total_hectares,
        active_shipments=len(shipments),
        monthly_export_tons=round(total_kg / 1000, 0),
        revenue_ytd_usd=round(revenue_ytd, 0),
        top_buyers=[b.buyer_name for b in buyer_matches[:6]],
    )

    # ── Persist everything ─────────────────────────────────────
    data = {
        "farms": [f.model_dump() for f in farms],
        "harvests": [h.model_dump() for h in harvests],
        "shipments": [s.model_dump() for s in shipments],
        "buyer_matches": [b.model_dump() for b in buyer_matches],
        "weather_alerts": [w.model_dump() for w in weather_alerts],
        "market_prices": [p.model_dump() for p in market_prices],
        "quality_inspections": [q.model_dump() for q in quality_inspections],
        "export_documents": [d.model_dump() for d in export_documents],
        "insights": [i.model_dump() for i in insights],
        "stats": stats.model_dump(),
    }
    store.save(data)


def generate_demo_data() -> None:
    """Synchronous wrapper for backward compatibility."""
    asyncio.run(async_generate_demo_data())
