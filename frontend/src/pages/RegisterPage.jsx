import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { registerCitizen } from "../services/authService";

function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    password: "",
    passwordConfirm: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function extractError(errorResponse) {
    const data = errorResponse?.response?.data;

    if (!data) {
      return "Registration failed. Please try again.";
    }

    if (typeof data.detail === "string") {
      return data.detail;
    }

    const messages = [];

    Object.entries(data).forEach(([field, value]) => {
      const label =
        field === "password_confirm"
          ? "Password confirmation"
          : field === "first_name"
            ? "First name"
            : field === "last_name"
              ? "Last name"
              : field === "email"
                ? "Email"
                : field === "phone"
                  ? "Phone"
                  : field;

      if (Array.isArray(value)) {
        messages.push(`${label}: ${value.join(" ")}`);
      } else if (typeof value === "string") {
        messages.push(`${label}: ${value}`);
      }
    });

    return messages.length
      ? messages.join(" ")
      : "Registration failed. Please check your details.";
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (form.password !== form.passwordConfirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await registerCitizen(form);

      setSuccess(
        "Your CivicResolve account has been created successfully.",
      );

      setTimeout(() => {
        navigate("/login", {
          replace: true,
          state: {
            registered: true,
            email: form.email,
          },
        });
      }, 1200);
    } catch (registrationError) {
      setError(extractError(registrationError));
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
            YOUR VOICE. YOUR CITY.
          </span>

          <h1>
            Turn a grievance into
            <span> meaningful action.</span>
          </h1>

          <p>
            Create your citizen account and get a transparent,
            intelligent way to report, track and resolve civic
            issues.
          </p>

          <div className="auth-benefits">
            <div>
              <span className="benefit-icon">01</span>
              <div>
                <strong>Report with confidence</strong>
                <p>
                  Submit complaints with evidence, voice or text.
                </p>
              </div>
            </div>

            <div>
              <span className="benefit-icon">02</span>
              <div>
                <strong>Track every step</strong>
                <p>
                  Follow your complaint through its complete lifecycle.
                </p>
              </div>
            </div>

            <div>
              <span className="benefit-icon">03</span>
              <div>
                <strong>Stay informed</strong>
                <p>
                  Receive updates when your complaint changes status.
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
              CREATE ACCOUNT
            </span>

            <h2>Join CivicResolve</h2>

            <p>
              Create your citizen account to start raising and
              tracking grievances.
            </p>
          </div>

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <div className="auth-field-row">
              <div className="auth-field">
                <label htmlFor="firstName">
                  First name
                </label>

                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  value={form.firstName}
                  onChange={handleChange}
                  placeholder="Sai Teja"
                  autoComplete="given-name"
                  required
                />
              </div>

              <div className="auth-field">
                <label htmlFor="lastName">
                  Last name
                </label>

                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  value={form.lastName}
                  onChange={handleChange}
                  placeholder="Puvvada"
                  autoComplete="family-name"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="registerEmail">
                Email address
              </label>

              <input
                id="registerEmail"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>

            <div className="auth-field">
              <label htmlFor="phone">
                Phone number
              </label>

              <input
                id="phone"
                name="phone"
                type="tel"
                value={form.phone}
                onChange={handleChange}
                placeholder="10 digit mobile number"
                autoComplete="tel"
                inputMode="numeric"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="registerPassword">
                Password
              </label>

              <input
                id="registerPassword"
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Create a strong password"
                autoComplete="new-password"
                required
              />
            </div>

            <div className="auth-field">
              <label htmlFor="passwordConfirm">
                Confirm password
              </label>

              <input
                id="passwordConfirm"
                name="passwordConfirm"
                type="password"
                value={form.passwordConfirm}
                onChange={handleChange}
                placeholder="Enter your password again"
                autoComplete="new-password"
                required
              />
            </div>

            {error && (
              <div className="auth-message auth-message-error">
                <span>!</span>
                {error}
              </div>
            )}

            {success && (
              <div className="auth-message auth-message-success">
                <span>✓</span>
                {success}
              </div>
            )}

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >
              {loading
                ? "Creating account..."
                : "Create citizen account"}
            </button>
          </form>

          <div className="auth-switch">
            Already have an account?
            <Link to="/login">
              Sign in
            </Link>
          </div>

          <p className="auth-security">
            Your account is protected with secure authentication.
          </p>
        </div>
      </section>
    </main>
  );
}

export default RegisterPage;