"""SENASICA → USDA APHIS phytosanitary compliance for Mexican agricultural exports.

Data source: SENASICA NIMF/ISPM standards and USDA APHIS Plants for Planting Manual.
This module encodes the most common requirements for Michoacán avocado/berry exports
and Estado de México floriculture exports — used for compliance checklist generation
and rejection-risk scoring (no AI required for the deterministic core).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import (
    PhytoCertificate,
    PhytoRequirement,
    PhytoStatus,
    RejectionRiskAssessment,
    RiskLevel,
)


# ── Requirements database (SENASICA + APHIS) ──────────────────
#
# Codes follow SENASICA-MX numbering convention. APHIS rules sourced from
# 7 CFR 319 and APHIS Fruits and Vegetables Import Manual.

REQUIREMENTS: list[dict] = [
    # Avocado → US (Hass / Michoacán protocol)
    {
        "code": "MX-AV-US-01",
        "description": "APHIS-approved orchard registration with SENASICA (must be in Michoacán/Jalisco approved list)",
        "destination": "US",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA / USDA APHIS",
    },
    {
        "code": "MX-AV-US-02",
        "description": "Pest-free orchard certification (free of fruit fly Anastrepha spp.)",
        "destination": "US",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-AV-US-03",
        "description": "Pre-export inspection and phytosanitary certificate (PC) issued ≤14 days before shipment",
        "destination": "US",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-AV-US-04",
        "description": "Treatment for Stenoma catenifer (avocado seed moth) — orchard surveillance + cold treatment if applicable",
        "destination": "US",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-AV-US-05",
        "description": "Tamper-evident, pest-proof packaging with traceable lot codes",
        "destination": "US",
        "crop_type": "avocado",
        "issuing_authority": "USDA APHIS",
    },
    # Avocado → EU
    {
        "code": "MX-AV-EU-01",
        "description": "EU phytosanitary certificate per Regulation (EU) 2016/2031",
        "destination": "EU",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-AV-EU-02",
        "description": "Pesticide residue compliance with EU MRLs (Reg. EC 396/2005)",
        "destination": "EU",
        "crop_type": "avocado",
        "issuing_authority": "SENASICA",
    },
    # Berries → US
    {
        "code": "MX-BR-US-01",
        "description": "GAP/GlobalG.A.P. certification (Primary Production Standard)",
        "destination": "US",
        "crop_type": "berry",
        "issuing_authority": "Third-party certifier",
    },
    {
        "code": "MX-BR-US-02",
        "description": "Phytosanitary certificate from SENASICA — Drosophila suzukii surveillance program",
        "destination": "US",
        "crop_type": "berry",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-BR-US-03",
        "description": "Cold-chain integrity (≤2°C) — temperature logger required",
        "destination": "US",
        "crop_type": "berry",
        "issuing_authority": "USDA APHIS",
    },
    # Cut flowers → US (Estado de México)
    {
        "code": "MX-FL-US-01",
        "description": "USDA APHIS PPQ Form 587 (Application for Permit to Import Plants)",
        "destination": "US",
        "crop_type": "rose",
        "issuing_authority": "USDA APHIS",
    },
    {
        "code": "MX-FL-US-02",
        "description": "SENASICA phytosanitary certificate — flower thrips and aphid surveillance",
        "destination": "US",
        "crop_type": "rose",
        "issuing_authority": "SENASICA",
    },
    {
        "code": "MX-FL-US-03",
        "description": "Stem treatment certification — fumigation with methyl bromide if APHIS-required",
        "destination": "US",
        "crop_type": "rose",
        "issuing_authority": "SENASICA / USDA APHIS",
    },
    # Cut flowers → EU
    {
        "code": "MX-FL-EU-01",
        "description": "EU phytosanitary certificate — Thrips palmi and Bemisia tabaci freedom",
        "destination": "EU",
        "crop_type": "rose",
        "issuing_authority": "SENASICA",
    },
]


def get_requirements(destination: str, crop_type: str) -> list[PhytoRequirement]:
    """Return all phytosanitary requirements for a (destination, crop) pair."""
    out: list[PhytoRequirement] = []
    # Flowers share rules across rose/chrysanthemum/gerbera/lily
    flower_crops = {"rose", "chrysanthemum", "gerbera", "lily"}
    lookup_crop = "rose" if crop_type in flower_crops else crop_type
    for r in REQUIREMENTS:
        if r["destination"] == destination and r["crop_type"] == lookup_crop:
            out.append(PhytoRequirement(
                code=r["code"],
                description=r["description"],
                destination=destination,
                crop_type=crop_type,
                mandatory=True,
                issuing_authority=r["issuing_authority"],
            ))
    return out


def check_certificate(cert: PhytoCertificate) -> dict:
    """Run a deterministic compliance check against requirements DB.

    Returns coverage info (matched / missing requirements) without AI.
    """
    required = get_requirements(cert.destination, cert.crop_type)
    required_codes = {r.code for r in required}
    met = set(cert.requirements_met) & required_codes
    missing = required_codes - met
    return {
        "certificate_id": cert.id,
        "destination": cert.destination,
        "crop_type": cert.crop_type,
        "total_requirements": len(required),
        "met_count": len(met),
        "missing_count": len(missing),
        "coverage_pct": round(len(met) / len(required) * 100, 1) if required else 0.0,
        "met": sorted(met),
        "missing": sorted(missing),
        "requirements": [r.model_dump() for r in required],
    }


def assess_rejection_risk(cert: PhytoCertificate, shipment_value_usd: float = 50000.0) -> RejectionRiskAssessment:
    """Score the risk of APHIS/SENASICA rejection for a phytosanitary certificate.

    Heuristic combines:
      - missing requirements (heaviest weight)
      - certificate expiry status
      - inspection completeness
      - history of rejection_reason
    """
    coverage = check_certificate(cert)
    missing_pct = (coverage["missing_count"] / coverage["total_requirements"]) if coverage["total_requirements"] else 0
    factors: list[str] = []

    score = 0.05  # baseline
    score += missing_pct * 0.7
    if coverage["missing_count"] > 0:
        factors.append(
            f"{coverage['missing_count']} of {coverage['total_requirements']} requirements not met"
        )

    # Expiry check
    if cert.expiry_date:
        try:
            expiry = datetime.strptime(cert.expiry_date, "%Y-%m-%d")
            days_until = (expiry - datetime.now()).days
            if days_until < 0:
                score += 0.3
                factors.append(f"Certificate expired {-days_until} days ago")
            elif days_until < 7:
                score += 0.15
                factors.append(f"Certificate expires in {days_until} days")
        except ValueError:
            pass

    # Inspection completeness
    if cert.status == PhytoStatus.draft:
        score += 0.1
        factors.append("Certificate still in draft status")
    elif cert.status == PhytoStatus.rejected:
        score = max(score, 0.95)
        factors.append(f"Previous rejection: {cert.rejection_reason or 'unspecified'}")

    if not cert.aphis_inspection_id and cert.destination == "US":
        score += 0.08
        factors.append("No APHIS inspection ID recorded")
    if not cert.senasica_cert_number:
        score += 0.08
        factors.append("No SENASICA certificate number assigned")

    score = max(0.0, min(1.0, score))

    if score < 0.15:
        level = RiskLevel.very_low
    elif score < 0.35:
        level = RiskLevel.low
    elif score < 0.6:
        level = RiskLevel.medium
    elif score < 0.8:
        level = RiskLevel.high
    else:
        level = RiskLevel.critical

    recommendations: list[str] = []
    for code in coverage["missing"]:
        req = next((r for r in REQUIREMENTS if r["code"] == code), None)
        if req:
            recommendations.append(f"Complete {code}: {req['description']}")
    if cert.status == PhytoStatus.draft:
        recommendations.append("Submit certificate to SENASICA for inspection scheduling")
    if not cert.aphis_inspection_id and cert.destination == "US":
        recommendations.append("Request APHIS inspection appointment via SENASICA portal")

    estimated_loss = shipment_value_usd * score

    return RejectionRiskAssessment(
        certificate_id=cert.id,
        risk_level=level,
        risk_score=round(score, 3),
        factors=factors,
        recommendations=recommendations,
        estimated_loss_usd=round(estimated_loss, 2),
    )
