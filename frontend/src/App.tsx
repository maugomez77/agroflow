import { useMemo, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Farms from "./pages/Farms";
import FarmDetail from "./pages/FarmDetail";
import Shipments from "./pages/Shipments";
import ShipmentDetail from "./pages/ShipmentDetail";
import Buyers from "./pages/Buyers";
import Quality from "./pages/Quality";
import Documents from "./pages/Documents";
import Analyze from "./pages/Analyze";
import Cooperatives from "./pages/Cooperatives";
import Satellite from "./pages/Satellite";
import Compliance from "./pages/Compliance";
import Subscription from "./pages/Subscription";
import {
  I18nContext,
  loadStoredLang,
  persistLang,
  translations,
} from "./i18n";
import type { Language } from "./i18n";

export default function App() {
  const [lang, setLangState] = useState<Language>(loadStoredLang());
  const value = useMemo(
    () => ({
      lang,
      setLang: (next: Language) => {
        setLangState(next);
        persistLang(next);
      },
      t: translations[lang],
    }),
    [lang]
  );

  return (
    <I18nContext.Provider value={value}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="farms" element={<Farms />} />
            <Route path="farms/:id" element={<FarmDetail />} />
            <Route path="shipments" element={<Shipments />} />
            <Route path="shipments/:id" element={<ShipmentDetail />} />
            <Route path="buyers" element={<Buyers />} />
            <Route path="quality" element={<Quality />} />
            <Route path="documents" element={<Documents />} />
            <Route path="analyze" element={<Analyze />} />
            <Route path="cooperatives" element={<Cooperatives />} />
            <Route path="satellite" element={<Satellite />} />
            <Route path="compliance" element={<Compliance />} />
            <Route path="subscription" element={<Subscription />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </I18nContext.Provider>
  );
}
