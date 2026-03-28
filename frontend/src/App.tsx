import { Routes, Route, Link, Navigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import DoctorPortal from "./pages/DoctorPortal";
import PatientPortal from "./pages/PatientPortal";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

export default function App() {
  const { user, signOut, loading, isDoctor, isPatient } = useAuth();

  // Determine the home route based on user role
  const getHomeRoute = () => {
    if (isDoctor) return "/doctor";
    if (isPatient) return "/patient";
    return "/doctor"; // Demo mode: skip login, go straight to demo
  };

  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to={user ? getHomeRoute() : "/"} className="flex items-center gap-2">
            <span className="text-xl font-bold text-blue-600">MediGuardAI</span>
            <span className="text-sm text-gray-400">Multi-Agent Demo</span>
          </Link>
        </div>
        <div className="flex gap-4 items-center">
          {!loading && user ? (
            <>
              {/* Show Doctor Portal link only for doctors */}
              {isDoctor && (
                <Link
                  to="/doctor"
                  className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  Doctor Portal
                </Link>
              )}
              {/* Show Patient Portal link only for patients */}
              {isPatient && (
                <Link
                  to="/patient"
                  className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  Patient Portal
                </Link>
              )}
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-gray-200">
                <div className="flex flex-col items-end">
                  <span className="text-sm text-gray-600">
                    {user.profile?.name || user.email}
                  </span>
                  <span className="text-xs text-gray-400 capitalize">
                    {user.profile?.role || "User"}
                  </span>
                </div>
                <button
                  onClick={() => signOut()}
                  className="px-3 py-1.5 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                >
                  Sign out
                </button>
              </div>
            </>
          ) : !loading ? (
            <>
              <Link
                to="/login"
                className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Sign up
              </Link>
            </>
          ) : null}
        </div>
      </nav>

      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Home route - redirect based on role */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              {isDoctor ? (
                <Navigate to="/doctor" replace />
              ) : isPatient ? (
                <Navigate to="/patient" replace />
              ) : (
                <Navigate to="/login" replace />
              )}
            </ProtectedRoute>
          }
        />

        {/* Doctor Portal - HACKATHON DEMO: accessible without login */}
        <Route
          path="/doctor"
          element={<DoctorPortal />}
        />

        {/* Patient Portal - only for patients */}
        <Route
          path="/patient"
          element={
            <ProtectedRoute requiredRole="patient">
              <PatientPortal />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}
