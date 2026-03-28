import { Routes, Route, Link } from "react-router-dom";
import DoctorPortal from "./pages/DoctorPortal";
import PatientPortal from "./pages/PatientPortal";

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold text-blue-600">MediGuardAI</span>
          <span className="text-sm text-gray-400">Multi-Agent Demo</span>
        </div>
        <div className="flex gap-4">
          <Link
            to="/doctor"
            className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Doctor Portal
          </Link>
          <Link
            to="/patient"
            className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Patient Portal
          </Link>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<DoctorPortal />} />
        <Route path="/doctor" element={<DoctorPortal />} />
        <Route path="/patient" element={<PatientPortal />} />
      </Routes>
    </div>
  );
}
