import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { UserRole } from "../lib/insforge";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading, isDoctor, isPatient } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    // Redirect to login page, preserving the attempted URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check for required role
  if (requiredRole) {
    const hasRole = 
      (requiredRole === "doctor" && isDoctor) ||
      (requiredRole === "patient" && isPatient);

    if (!hasRole) {
      // Redirect to the appropriate portal based on their actual role
      if (isDoctor) {
        return <Navigate to="/doctor" replace />;
      } else if (isPatient) {
        return <Navigate to="/patient" replace />;
      } else {
        // No role set, redirect to login
        return <Navigate to="/login" replace />;
      }
    }
  }

  return <>{children}</>;
}
