import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import ContextForm from "./pages/ContextForm";
import Negotiation from "./pages/Negotiation";
import Validation from "./pages/Validation";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/workflows/:id/context" element={<ContextForm />} />
        <Route path="/workflows/:id/negotiation" element={<Negotiation />} />
        <Route path="/workflows/:id/validation" element={<Validation />} />
      </Routes>
    </Layout>
  );
}
