import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Sprout,
  Truck,
  Users,
  ShieldCheck,
  FileText,
  BrainCircuit,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/farms", label: "Farms", icon: Sprout },
  { to: "/shipments", label: "Shipments", icon: Truck },
  { to: "/buyers", label: "Buyers", icon: Users },
  { to: "/quality", label: "Quality", icon: ShieldCheck },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/analyze", label: "AI Analysis", icon: BrainCircuit },
];

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/farms": "Farm Management",
  "/shipments": "Shipment Tracking",
  "/buyers": "Buyer Matching",
  "/quality": "Quality Inspections",
  "/documents": "Export Documents",
  "/analyze": "AI Analysis",
};

export default function Layout() {
  const location = useLocation();
  const basePath = "/" + location.pathname.split("/")[1];
  const title = pageTitles[basePath] ?? "AgroFlow";

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>AgroFlow</h1>
          <p>Michoacan Intelligence</p>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <Icon />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <div className="main-content">
        <header className="header">
          <h2>{title}</h2>
          <div className="header-right">
            <span>AgroFlow Intelligence v0.1</span>
          </div>
        </header>
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
