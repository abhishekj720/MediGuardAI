import { Routes, Route, Link } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import DoctorPortal from "./pages/DoctorPortal";
import PatientPortal from "./pages/PatientPortal";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

export default function App() {
  const { user, signOut, loading } = useAuth();

  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-blue-600">MediGuardAI</span>
            <span className="text-sm text-gray-400">Multi-Agent Demo</span>
          </Link>
        </div>
        <div className="flex gap-4 items-center">
          {!loading && user ? (
            <>
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
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-gray-200">
                <span className="text-sm text-gray-600">
                  {user.profile?.name || user.email}
                </span>
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

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DoctorPortal />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doctor"
          element={
            <ProtectedRoute>
              <DoctorPortal />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient"
          element={
            <ProtectedRoute>
              <PatientPortal />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}
