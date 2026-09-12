import { useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import "./App.css";

import { useAuth } from "./context/AuthContext.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";

import AdminDashboard from "./pages/AdminDashboard.jsx";
import AnalyticsDashboard from "./pages/AnalyticsDashboard.jsx";
import CitizenDashboard from "./pages/CitizenDashboard.jsx";
import ComplaintCreatePage from "./pages/ComplaintCreatePage.jsx";
import ComplaintDetailPage from "./pages/ComplaintDetailPage.jsx";
import ComplaintListPage from "./pages/ComplaintListPage.jsx";
import LoadingScreen from "./pages/LoadingScreen.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import SLADashboard from "./pages/SLADashboard.jsx";


function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const loginData = await login(
        email,
        password,
      );

      const loggedInUser = loginData.user;

      if (loggedInUser?.role === "ADMIN") {
        navigate("/dashboard/admin", {
          replace: true,
        });
      } else if (
        loggedInUser?.role === "OFFICER"
      ) {
        navigate("/dashboard/officer", {
          replace: true,
        });
      } else {
        navigate("/dashboard/citizen", {
          replace: true,
        });
      }
    } catch (loginError) {
      console.error(
        "Login failed:",
        loginError,
      );

      const detail =
        loginError?.response?.data?.detail;

      setError(
        detail ||
          "Login failed. Please check your email and password.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand">
          <span className="login-brand-mark">
            CR
          </span>

          <div>
            <p className="login-brand-name">
              CivicResolve
            </p>

            <p className="login-brand-tagline">
              Intelligent grievance resolution
            </p>
          </div>
        </div>

        <div className="login-heading">
          <p className="login-eyebrow">
            SECURE ACCESS
          </p>

          <h1>Welcome back</h1>

          <p>
            Sign in to access your CivicResolve
            workspace.
          </p>
        </div>

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >
          <label htmlFor="email">
            Email
          </label>

          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <label htmlFor="password">
            Password
          </label>

          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="Enter your password"
            autoComplete="current-password"
            required
          />

          {error && (
            <p className="login-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="login-submit"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}


function ProtectedRoute({ children }) {
  const {
    isAuthenticated,
    isLoadingUser,
  } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return children;
}


function RoleRoute({
  allowedRoles,
  children,
}) {
  const {
    user,
    isLoadingUser,
  } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return children;
}


function DashboardRedirect() {
  const { user } = useAuth();

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (user.role === "ADMIN") {
    return (
      <Navigate
        to="/dashboard/admin"
        replace
      />
    );
  }

  if (user.role === "OFFICER") {
    return (
      <Navigate
        to="/dashboard/officer"
        replace
      />
    );
  }

  return (
    <Navigate
      to="/dashboard/citizen"
      replace
    />
  );
}


function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route
          index
          element={<DashboardRedirect />}
        />

        <Route
          path="citizen"
          element={
            <RoleRoute
              allowedRoles={["USER"]}
            >
              <CitizenDashboard />
            </RoleRoute>
          }
        />

        <Route
          path="officer"
          element={
            <RoleRoute
              allowedRoles={["OFFICER"]}
            >
              <OfficerDashboard />
            </RoleRoute>
          }
        />

        <Route
          path="admin"
          element={
            <RoleRoute
              allowedRoles={["ADMIN"]}
            >
              <AdminDashboard />
            </RoleRoute>
          }
        />

        <Route
          path="analytics"
          element={
            <RoleRoute
              allowedRoles={["ADMIN"]}
            >
              <AnalyticsDashboard />
            </RoleRoute>
          }
        />

        <Route
          path="sla"
          element={
            <RoleRoute
              allowedRoles={["ADMIN"]}
            >
              <SLADashboard />
            </RoleRoute>
          }
        />

        <Route
          path="complaints"
          element={
            <RoleRoute
              allowedRoles={[
                "USER",
                "OFFICER",
                "ADMIN",
              ]}
            >
              <ComplaintListPage />
            </RoleRoute>
          }
        />

        <Route
          path="complaints/new"
          element={
            <RoleRoute
              allowedRoles={["USER"]}
            >
              <ComplaintCreatePage />
            </RoleRoute>
          }
        />

        <Route
          path="complaints/:complaintId"
          element={
            <RoleRoute
              allowedRoles={[
                "USER",
                "ADMIN",
              ]}
            >
              <ComplaintDetailPage />
            </RoleRoute>
          }
        />

        <Route
          path="assigned"
          element={
            <RoleRoute
              allowedRoles={["OFFICER"]}
            >
              <ComplaintListPage />
            </RoleRoute>
          }
        />

        <Route
          path="assigned/:complaintId"
          element={
            <RoleRoute
              allowedRoles={["OFFICER"]}
            >
              <ComplaintDetailPage />
            </RoleRoute>
          }
        />
      </Route>

      <Route
        path="/"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />
    </Routes>
  );
}


export default App;