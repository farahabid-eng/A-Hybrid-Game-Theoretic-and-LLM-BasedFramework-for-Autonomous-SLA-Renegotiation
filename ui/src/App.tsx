import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import SLAs from "./pages/SLAs";
import BATNAConfig from "./pages/BATNAConfig";
import ProfileConfig from "./pages/ProfileConfig";
import ViolationSim from "./pages/ViolationSim";
import Negotiation from "./pages/Negotiation";
import Validation from "./pages/Validation";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/slas" element={<SLAs />} />
        <Route path="/slas/:slaId/batnas" element={<BATNAConfig />} />
        <Route path="/slas/:slaId/profiles" element={<ProfileConfig />} />
        <Route path="/workflows/:id/simulate" element={<ViolationSim />} />
        <Route path="/workflows/:id/negotiation" element={<Negotiation />} />
        <Route path="/workflows/:id/validation" element={<Validation />} />
      </Routes>
    </Layout>
  );
}
