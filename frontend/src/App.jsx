import { useEffect, useState } from "react";
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
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
import HomePage from "./pages/HomePage.jsx";
import LoadingScreen from "./pages/LoadingScreen.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import SLADashboard from "./pages/SLADashboard.jsx";
import ActivityPage from "./pages/ActivityPage.jsx";

function LoginPage() {
  const { login, isAuthenticated, isLoadingUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState(
    location.state?.email || "",
  );
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (location.state?.registered) {
      setError("");
      window.history.replaceState(
        {},
        document.title,
        window.location.pathname,
      );
    }
  }, [location.state]);

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

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
    <main className="auth-page">
      <section className="auth-showcase">
        <Link
          to="/"
          className="auth-brand"
        >
          <span className="auth-brand-mark">
            CR
          </span>

          <span>
            <strong>CivicResolve</strong>
            <small>Intelligent grievance resolution</small>
          </span>
        </Link>

        <div className="auth-showcase-content">
          <span className="auth-kicker">
            CIVIC SERVICE, REIMAGINED
          </span>

          <h1>
            Your issue deserves
            <span> visibility.</span>
          </h1>

          <p>
            Sign in to report grievances, track progress, receive
            updates and stay connected with the resolution journey.
          </p>

          <div className="auth-benefits">
            <div>
              <span className="benefit-icon">01</span>
              <div>
                <strong>Report</strong>
                <p>
                  Submit structured complaints with supporting
                  information.
                </p>
              </div>
            </div>

            <div>
              <span className="benefit-icon">02</span>
              <div>
                <strong>Track</strong>
                <p>
                  See exactly where your complaint stands.
                </p>
              </div>
            </div>

            <div>
              <span className="benefit-icon">03</span>
              <div>
                <strong>Resolve</strong>
                <p>
                  Follow the complete path from submission to
                  resolution.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-showcase-footer">
          <span>AI-assisted</span>
          <span>Multilingual</span>
          <span>Transparent</span>
          <span>Citizen-first</span>
        </div>
      </section>

      <section className="auth-form-section">
        <div className="auth-card">
          <div className="auth-card-heading">
            <span className="auth-kicker">
              SECURE ACCESS
            </span>

            <h2>Welcome back</h2>

            <p>
              Sign in to continue to your CivicResolve workspace.
            </p>
          </div>

          {location.state?.registered && (
            <div className="auth-message auth-message-success">
              <span>✓</span>
              Account created successfully. You can sign in now.
            </div>
          )}

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <div className="auth-field">
              <label htmlFor="email">
                Email address
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
            </div>

            <div className="auth-field">
              <label htmlFor="password">
                Password
              </label>

              <div className="auth-password">
                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current,
                    )
                  }
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {error && (
              <div className="auth-message auth-message-error">
                <span>!</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >
              {loading
                ? "Signing in..."
                : "Sign in"}
            </button>
          </form>

          <div className="auth-switch">
            Don't have an account?
            <Link to="/register">
              Create one
            </Link>
          </div>

          <p className="auth-security">
            Secure access for CivicResolve citizens and authorized
            personnel.
          </p>
        </div>
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

function PublicHomeRoute() {
  const {
    isAuthenticated,
    isLoadingUser,
  } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <HomePage />;
}

function PublicRegisterRoute() {
  const {
    isAuthenticated,
    isLoadingUser,
  } = useAuth();

  if (isLoadingUser) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <RegisterPage />;
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<PublicHomeRoute />}
      />

      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/register"
        element={<PublicRegisterRoute />}
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
          path="profile"
          element={
            <RoleRoute
              allowedRoles={[
                "USER",
                "OFFICER",
                "ADMIN",
              ]}
            >
              <ProfilePage />
            </RoleRoute>
          }
        />

        <Route
          path="activity"
          element={
            <RoleRoute
              allowedRoles={[
                "USER",
                "OFFICER",
                "ADMIN",
              ]}
            >
              <ActivityPage />
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
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />
    </Routes>
  );
}

export default App;