import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import RunExplorer from "./pages/RunExplorer";
import FailurePatterns from "./pages/FailurePatterns";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="runs/:runId" element={<RunExplorer />} />
        <Route path="failures" element={<FailurePatterns />} />
      </Route>
    </Routes>
  );
}
