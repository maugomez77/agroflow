import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Sprout,
  Truck,
  Users,
  ShieldCheck,
  FileText,
  BrainCircuit,
  Network,
  Satellite,
  ScrollText,
  CreditCard,
} from "lucide-react";
import { useI18n } from "../i18n";

export default function Layout() {
  const location = useLocation();
  const { lang, setLang, t } = useI18n();

  const navItems = [
    { to: "/", label: t.nav.dashboard, icon: LayoutDashboard, key: "dashboard" },
    { to: "/farms", label: t.nav.farms, icon: Sprout, key: "farms" },
    { to: "/shipments", label: t.nav.shipments, icon: Truck, key: "shipments" },
    { to: "/buyers", label: t.nav.buyers, icon: Users, key: "buyers" },
    { to: "/quality", label: t.nav.quality, icon: ShieldCheck, key: "quality" },
    { to: "/documents", label: t.nav.documents, icon: FileText, key: "documents" },
    { to: "/analyze", label: t.nav.analyze, icon: BrainCircuit, key: "analyze" },
    { to: "/cooperatives", label: t.nav.cooperatives, icon: Network, key: "cooperatives" },
    { to: "/satellite", label: t.nav.satellite, icon: Satellite, key: "satellite" },
    { to: "/compliance", label: t.nav.compliance, icon: ScrollText, key: "compliance" },
    { to: "/subscription", label: t.nav.subscription, icon: CreditCard, key: "subscription" },
  ];

  const pageTitles: Record<string, string> = {
    "/": t.pageTitle.dashboard,
    "/farms": t.pageTitle.farms,
    "/shipments": t.pageTitle.shipments,
    "/buyers": t.pageTitle.buyers,
    "/quality": t.pageTitle.quality,
    "/documents": t.pageTitle.documents,
    "/analyze": t.pageTitle.analyze,
    "/cooperatives": t.pageTitle.cooperatives,
    "/satellite": t.pageTitle.satellite,
    "/compliance": t.pageTitle.compliance,
    "/subscription": t.pageTitle.subscription,
  };

  const basePath = "/" + location.pathname.split("/")[1];
  const title = pageTitles[basePath] ?? t.appName;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>{t.appName}</h1>
          <p>{t.appSubtitle}</p>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon, key }) => (
            <NavLink
              key={key}
              to={to}
              end={to === "/"}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <Icon />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer" style={{ padding: "1rem", borderTop: "1px solid #2a2a2a" }}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <button
              onClick={() => setLang("en")}
              style={{
                padding: "0.35rem 0.6rem",
                background: lang === "en" ? "#16a34a" : "transparent",
                color: lang === "en" ? "#fff" : "#aaa",
                border: "1px solid #2a2a2a",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              EN
            </button>
            <button
              onClick={() => setLang("es")}
              style={{
                padding: "0.35rem 0.6rem",
                background: lang === "es" ? "#16a34a" : "transparent",
                color: lang === "es" ? "#fff" : "#aaa",
                border: "1px solid #2a2a2a",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              ES
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="main-content">
        <header className="header">
          <h2>{title}</h2>
          <div className="header-right">
            <span>{t.appName} {t.appSubtitle} v0.2</span>
          </div>
        </header>
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
