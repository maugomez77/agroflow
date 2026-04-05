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

export default function App() {
  return (
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
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
