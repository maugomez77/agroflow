/**
 * AgroFlow i18n — English + Spanish translations.
 *
 * Per Council CLAUDE.md standard: LatAm projects ship both EN and ES versions
 * with a user-selectable language toggle.
 */

import { createContext, useContext } from "react";

export type Language = "en" | "es";

export interface TranslationDict {
  appName: string;
  appSubtitle: string;
  nav: {
    dashboard: string;
    farms: string;
    shipments: string;
    buyers: string;
    quality: string;
    documents: string;
    analyze: string;
    cooperatives: string;
    satellite: string;
    compliance: string;
    subscription: string;
  };
  pageTitle: {
    dashboard: string;
    farms: string;
    shipments: string;
    buyers: string;
    quality: string;
    documents: string;
    analyze: string;
    cooperatives: string;
    satellite: string;
    compliance: string;
    subscription: string;
  };
  common: {
    loading: string;
    noData: string;
    error: string;
    refresh: string;
    view: string;
    details: string;
    total: string;
    members: string;
    hectares: string;
    region: string;
    crop: string;
    status: string;
    revenue: string;
    back: string;
  };
  tier: {
    starter: string;
    pro: string;
    enterprise: string;
    current: string;
    upgrade: string;
    features: string;
    pricePerMonth: string;
    changeTo: string;
    gateMessage: string;
  };
  coop: {
    title: string;
    subtitle: string;
    memberFarms: string;
    revenueSplit: string;
    coopFee: string;
    founded: string;
    certifications: string;
    aggregateMetrics: string;
    totalHarvest: string;
    gradeAPercent: string;
    totalValue: string;
    toMembers: string;
    runOptimize: string;
  };
  satellite: {
    title: string;
    subtitle: string;
    ndvi: string;
    evi: string;
    solarRadiation: string;
    cloudCover: string;
    vegetationStatus: string;
    fetchLive: string;
    excellent: string;
    good: string;
    fair: string;
    stressed: string;
    critical: string;
  };
  phyto: {
    title: string;
    subtitle: string;
    certNumber: string;
    aphisId: string;
    destination: string;
    issued: string;
    expires: string;
    coverage: string;
    requirementsMet: string;
    requirementsMissing: string;
    runRisk: string;
    runAiRisk: string;
    riskLevel: string;
    riskScore: string;
    estimatedLoss: string;
    riskFactors: string;
    recommendations: string;
  };
  languages: {
    english: string;
    spanish: string;
  };
}

export const translations: Record<Language, TranslationDict> = {
  en: {
    /* App + Navigation */
    appName: "AgroFlow",
    appSubtitle: "Premium Intelligence",
    nav: {
      dashboard: "Dashboard",
      farms: "Farms",
      shipments: "Shipments",
      buyers: "Buyers",
      quality: "Quality",
      documents: "Documents",
      analyze: "AI Analysis",
      cooperatives: "Cooperatives",
      satellite: "Satellite",
      compliance: "Phytosanitary",
      subscription: "Subscription",
    },
    pageTitle: {
      dashboard: "Dashboard",
      farms: "Farm Management",
      shipments: "Shipment Tracking",
      buyers: "Buyer Matching",
      quality: "Quality Inspections",
      documents: "Export Documents",
      analyze: "AI Analysis",
      cooperatives: "Cooperatives",
      satellite: "Satellite Vegetation",
      compliance: "Phytosanitary Compliance",
      subscription: "Premium Subscription",
    },
    /* Common */
    common: {
      loading: "Loading...",
      noData: "No data available",
      error: "Error loading data",
      refresh: "Refresh",
      view: "View",
      details: "Details",
      total: "Total",
      members: "Members",
      hectares: "Hectares",
      region: "Region",
      crop: "Crop",
      status: "Status",
      revenue: "Revenue",
      back: "Back",
    },
    tier: {
      starter: "Starter",
      pro: "Pro",
      enterprise: "Enterprise",
      current: "Current Tier",
      upgrade: "Upgrade",
      features: "Features",
      pricePerMonth: "/mo",
      changeTo: "Switch to",
      gateMessage: "This feature requires a higher subscription tier.",
    },
    coop: {
      title: "Cooperatives",
      subtitle: "Multi-farm pooling and revenue distribution",
      memberFarms: "Member Farms",
      revenueSplit: "Revenue Split",
      coopFee: "Coop Fee",
      founded: "Founded",
      certifications: "Certifications",
      aggregateMetrics: "Aggregated Metrics",
      totalHarvest: "Total Harvest",
      gradeAPercent: "Grade A %",
      totalValue: "Total Value",
      toMembers: "To Members",
      runOptimize: "Run AI Optimization",
    },
    satellite: {
      title: "Satellite Vegetation Monitoring",
      subtitle: "NASA POWER NDVI proxy — detect crop stress before visual symptoms",
      ndvi: "NDVI",
      evi: "EVI",
      solarRadiation: "Solar (MJ/m²)",
      cloudCover: "Cloud Cover",
      vegetationStatus: "Vegetation Status",
      fetchLive: "Fetch Live Data",
      excellent: "Excellent",
      good: "Good",
      fair: "Fair",
      stressed: "Stressed",
      critical: "Critical",
    },
    phyto: {
      title: "SENASICA → APHIS Phytosanitary Compliance",
      subtitle: "Certificate workflow + rejection-risk scoring for Mexican exports",
      certNumber: "SENASICA Certificate",
      aphisId: "APHIS Inspection ID",
      destination: "Destination",
      issued: "Issued",
      expires: "Expires",
      coverage: "Coverage",
      requirementsMet: "Requirements Met",
      requirementsMissing: "Missing Requirements",
      runRisk: "Run Risk Assessment",
      runAiRisk: "AI Risk Analysis",
      riskLevel: "Risk Level",
      riskScore: "Risk Score",
      estimatedLoss: "Estimated Loss",
      riskFactors: "Risk Factors",
      recommendations: "Recommendations",
    },
    languages: {
      english: "English",
      spanish: "Español",
    },
  },
  es: {
    /* App + Navegación */
    appName: "AgroFlow",
    appSubtitle: "Inteligencia Premium",
    nav: {
      dashboard: "Panel",
      farms: "Fincas",
      shipments: "Envíos",
      buyers: "Compradores",
      quality: "Calidad",
      documents: "Documentos",
      analyze: "Análisis IA",
      cooperatives: "Cooperativas",
      satellite: "Satélite",
      compliance: "Fitosanitario",
      subscription: "Suscripción",
    },
    pageTitle: {
      dashboard: "Panel de Control",
      farms: "Gestión de Fincas",
      shipments: "Seguimiento de Envíos",
      buyers: "Emparejamiento de Compradores",
      quality: "Inspecciones de Calidad",
      documents: "Documentos de Exportación",
      analyze: "Análisis con IA",
      cooperatives: "Cooperativas",
      satellite: "Vegetación Satelital",
      compliance: "Cumplimiento Fitosanitario",
      subscription: "Suscripción Premium",
    },
    common: {
      loading: "Cargando...",
      noData: "No hay datos disponibles",
      error: "Error al cargar datos",
      refresh: "Actualizar",
      view: "Ver",
      details: "Detalles",
      total: "Total",
      members: "Miembros",
      hectares: "Hectáreas",
      region: "Región",
      crop: "Cultivo",
      status: "Estado",
      revenue: "Ingresos",
      back: "Volver",
    },
    tier: {
      starter: "Inicial",
      pro: "Profesional",
      enterprise: "Empresarial",
      current: "Plan Actual",
      upgrade: "Mejorar",
      features: "Funciones",
      pricePerMonth: "/mes",
      changeTo: "Cambiar a",
      gateMessage: "Esta función requiere un plan de suscripción superior.",
    },
    coop: {
      title: "Cooperativas",
      subtitle: "Consolidación multi-finca y distribución de ingresos",
      memberFarms: "Fincas Miembro",
      revenueSplit: "Reparto de Ingresos",
      coopFee: "Cuota Cooperativa",
      founded: "Fundada",
      certifications: "Certificaciones",
      aggregateMetrics: "Métricas Agregadas",
      totalHarvest: "Cosecha Total",
      gradeAPercent: "% Grado A",
      totalValue: "Valor Total",
      toMembers: "Para Miembros",
      runOptimize: "Optimizar con IA",
    },
    satellite: {
      title: "Monitoreo Satelital de Vegetación",
      subtitle:
        "Proxy NDVI de NASA POWER — detecta estrés del cultivo antes de los síntomas visuales",
      ndvi: "NDVI",
      evi: "EVI",
      solarRadiation: "Solar (MJ/m²)",
      cloudCover: "Nubosidad",
      vegetationStatus: "Estado de Vegetación",
      fetchLive: "Obtener Datos en Vivo",
      excellent: "Excelente",
      good: "Bueno",
      fair: "Regular",
      stressed: "Estresado",
      critical: "Crítico",
    },
    phyto: {
      title: "Cumplimiento Fitosanitario SENASICA → APHIS",
      subtitle:
        "Flujo de certificados y puntaje de riesgo de rechazo para exportaciones mexicanas",
      certNumber: "Certificado SENASICA",
      aphisId: "ID Inspección APHIS",
      destination: "Destino",
      issued: "Emitido",
      expires: "Vence",
      coverage: "Cobertura",
      requirementsMet: "Requisitos Cumplidos",
      requirementsMissing: "Requisitos Faltantes",
      runRisk: "Evaluar Riesgo",
      runAiRisk: "Análisis de Riesgo con IA",
      riskLevel: "Nivel de Riesgo",
      riskScore: "Puntaje de Riesgo",
      estimatedLoss: "Pérdida Estimada",
      riskFactors: "Factores de Riesgo",
      recommendations: "Recomendaciones",
    },
    languages: {
      english: "English",
      spanish: "Español",
    },
  },
};

interface I18nContextValue {
  lang: Language;
  setLang: (l: Language) => void;
  t: TranslationDict;
}

export const I18nContext = createContext<I18nContextValue>({
  lang: "en",
  setLang: () => {},
  t: translations.en,
});

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}

export function loadStoredLang(): Language {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem("agroflow.lang");
  if (stored === "en" || stored === "es") return stored;
  // Default to Spanish for LatAm market
  const browserLang = window.navigator.language?.toLowerCase() ?? "";
  return browserLang.startsWith("es") ? "es" : "en";
}

export function persistLang(lang: Language): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("agroflow.lang", lang);
}
