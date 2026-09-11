import { useState } from "react";
import { useAuth } from "./context/AuthContext.jsx";
import "./App.css";

function App() {
  const { isAuthenticated, login, logout } = useAuth();

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

      setPassword("");
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

  if (isAuthenticated) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">C</div>

            <div>
              <div className="brand-name">CivicResolve</div>
              <div className="brand-tagline">
                Intelligent grievance resolution
              </div>
            </div>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={logout}
          >
            Sign out
          </button>
        </header>

        <main className="authenticated-page">
          <section className="success-card">
            <div className="success-icon">✓</div>

            <p className="eyebrow">AUTHENTICATION SUCCESSFUL</p>

            <h1>Welcome to CivicResolve</h1>

            <p className="success-text">
              You are securely authenticated. Your citizen,
              officer, or administrator dashboard will be connected
              here next.
            </p>

            <div className="success-status">
              <span className="status-dot" />
              JWT session active
            </div>

            <button
              type="button"
              className="primary-button success-logout"
              onClick={logout}
            >
              Sign out
            </button>
          </section>
        </main>

        <footer className="footer">
          <span>© 2026 CivicResolve</span>
          <span>Secure • Transparent • Accountable</span>
        </footer>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">C</div>

          <div>
            <div className="brand-name">CivicResolve</div>
            <div className="brand-tagline">
              Intelligent grievance resolution
            </div>
          </div>
        </div>

        <div className="topbar-status">
          <span className="status-dot" />
          Secure access
        </div>
      </header>

      <main className="login-page">
        <section className="hero-section">
          <div className="hero-content">
            <p className="eyebrow">SMARTER GRIEVANCE MANAGEMENT</p>

            <h1>
              Your complaint.
              <br />
              <span>Our responsibility.</span>
            </h1>

            <p className="hero-description">
              CivicResolve uses intelligent analysis to classify,
              route, track, and resolve grievances with greater
              transparency and accountability.
            </p>

            <div className="feature-list">
              <div className="feature-item">
                <div className="feature-number">01</div>

                <div>
                  <strong>Submit</strong>
                  <p>Describe your issue in your own words.</p>
                </div>
              </div>

              <div className="feature-item">
                <div className="feature-number">02</div>

                <div>
                  <strong>Track</strong>
                  <p>Follow your complaint from submission to resolution.</p>
                </div>
              </div>

              <div className="feature-item">
                <div className="feature-number">03</div>

                <div>
                  <strong>Resolve</strong>
                  <p>Get routed to the right department and officer.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="login-section">
          <div className="login-card">
            <div className="login-card-header">
              <p className="eyebrow">ACCOUNT ACCESS</p>

              <h2>Welcome back</h2>

              <p>
                Sign in to access your CivicResolve account.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-field">
                <label htmlFor="email">Email address</label>

                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="form-field">
                <div className="password-label-row">
                  <label htmlFor="password">Password</label>
                </div>

                <div className="password-wrapper">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
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
                <div className="error-message" role="alert">
                  <span className="error-icon">!</span>
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                className="primary-button"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="button-spinner" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </button>
            </form>

            <div className="login-security">
              <span className="lock-icon">⌕</span>
              <span>Your connection is protected by JWT authentication.</span>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>© 2026 CivicResolve</span>
        <span>Secure • Transparent • Accountable</span>
      </footer>
    </div>
  );
}

export default App;