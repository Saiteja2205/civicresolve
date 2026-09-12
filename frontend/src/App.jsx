import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./context/AuthContext.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import CitizenDashboard from "./pages/CitizenDashboard.jsx";
import LoadingScreen from "./pages/LoadingScreen.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import "./App.css";

function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="login-page-container">
      <section className="login-brand-panel">
        <div className="login-brand-content">
          <p className="login-eyebrow">
            SMARTER GRIEVANCE MANAGEMENT
          </p>

          <h1>
            Your complaint.
            <br />
            <span>Our responsibility.</span>
          </h1>

          <p className="login-description">
            CivicResolve uses intelligent analysis to classify,
            route, track, and resolve grievances with greater
            transparency and accountability.
          </p>

          <div className="login-features">
            <div>
              <strong>01 &nbsp; Submit</strong>
              <span>Describe your issue in your own words.</span>
            </div>

            <div>
              <strong>02 &nbsp; Track</strong>
              <span>
                Follow your complaint from submission to resolution.
              </span>
            </div>

            <div>
              <strong>03 &nbsp; Resolve</strong>
              <span>
                Get routed to the right department and officer.
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <LoginForm login={login} />
      </section>
    </div>
  );
}

function LoginForm({ login }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setIsLoading(true);

      await login(email.trim(), password);
    } catch (err) {
      const detail = err.response?.data?.detail;

      if (detail) {
        setError(detail);
      } else if (err.response?.status === 401) {
        setError("Invalid email or password.");
      } else {
        setError(
          "Unable to connect to CivicResolve. Please try again.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-card">
      <div className="login-card-header">
        <div className="login-logo">C</div>

        <p className="login-eyebrow">ACCOUNT ACCESS</p>

        <h2>Welcome back</h2>

        <p>
          Sign in to access your CivicResolve workspace.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="login-form">
        <div className="login-field">
          <label htmlFor="email">Email address</label>

          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="login-field">
          <label htmlFor="password">Password</label>

          <div className="password-wrapper">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={isLoading}
            />

            <button
              type="button"
              className="password-toggle"
              onClick={() =>
                setShowPassword((current) => !current)
              }
              disabled={isLoading}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        {error && (
          <div className="login-error" role="alert">
            <span>!</span>
            {error}
          </div>
        )}

        <button
          type="submit"
          className="login-submit"
          disabled={isLoading}
        >
          {isLoading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div className="login-security">
        Secure JWT-authenticated session
      </div>
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoadingUser } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function RoleRoute({ allowedRoles, children }) {
  const { user } = useAuth();

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

function DashboardRedirect() {
  const { user } = useAuth();

  if (user?.role === "USER") {
    return <CitizenDashboard />;
  }

  if (user?.role === "OFFICER") {
    return <OfficerDashboard />;
  }

  if (user?.role === "ADMIN") {
    return <AdminDashboard />;
  }

  return (
    <div className="dashboard-unknown-role">
      <h1>Account configuration error</h1>

      <p>
        Your account has an unsupported CivicResolve role.
      </p>
    </div>
  );
}

function App() {
  const { isAuthenticated, isLoadingUser } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LoginPage />
          )
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardRedirect />} />

        <Route
          path="complaints"
          element={
            <RoleRoute allowedRoles={["USER", "ADMIN"]}>
              <DashboardRedirect />
            </RoleRoute>
          }
        />

        <Route
          path="assigned"
          element={
            <RoleRoute allowedRoles={["OFFICER"]}>
              <OfficerDashboard />
            </RoleRoute>
          }
        />

        <Route
          path="assignments"
          element={
            <RoleRoute allowedRoles={["ADMIN"]}>
              <AdminDashboard />
            </RoleRoute>
          }
        />
      </Route>

      <Route
        path="/"
        element={
          <Navigate
            to={isAuthenticated ? "/dashboard" : "/login"}
            replace
          />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to={isAuthenticated ? "/dashboard" : "/login"}
            replace
          />
        }
      />
    </Routes>
  );
}

export default App;