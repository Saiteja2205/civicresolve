import { Link } from "react-router-dom";

function ArrowIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M5 12h13M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function HomePage() {
  return (
    <main className="home-page">
      <nav className="home-nav">
        <Link
          to="/"
          className="home-logo"
        >
          <span className="home-logo-mark">
            CR
          </span>

          <span className="home-logo-text">
            <strong>CivicResolve</strong>
            <small>Intelligent grievance resolution</small>
          </span>
        </Link>

        <div className="home-nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
          <a href="#transparency">Transparency</a>
        </div>

        <div className="home-nav-actions">
          <Link
            to="/login"
            className="home-login-link"
          >
            Sign in
          </Link>

          <Link
            to="/register"
            className="home-nav-button"
          >
            Get started
            <ArrowIcon />
          </Link>
        </div>
      </nav>

      <section className="home-hero">
        <div className="home-hero-copy">
          <div className="home-status">
            <span className="home-status-dot" />
            <span>SMART CIVIC RESOLUTION PLATFORM</span>
          </div>

          <h1>
            Report.
            <br />
            Track.
            <br />
            <span>Resolve.</span>
          </h1>

          <p className="home-hero-description">
            A modern citizen platform that turns everyday grievances
            into structured, trackable and transparent resolutions.
            Powered by intelligent automation and designed around
            citizens.
          </p>

          <div className="home-hero-actions">
            <Link
              to="/register"
              className="home-primary-button"
            >
              Report a grievance
              <ArrowIcon />
            </Link>

            <Link
              to="/login"
              className="home-secondary-button"
            >
              Track a complaint
            </Link>
          </div>

          <div className="home-hero-meta">
            <span>
              <strong>AI</strong>
              assisted analysis
            </span>

            <span>
              <strong>24/7</strong>
              complaint visibility
            </span>

            <span>
              <strong>100%</strong>
              lifecycle tracking
            </span>
          </div>
        </div>

        <div className="home-hero-visual">
          <div className="hero-orbit hero-orbit-one" />
          <div className="hero-orbit hero-orbit-two" />

          <div className="hero-dashboard-card">
            <div className="hero-dashboard-top">
              <div>
                <span>COMPLAINT OVERVIEW</span>
                <strong>Live resolution flow</strong>
              </div>

              <span className="hero-live">
                <i />
                LIVE
              </span>
            </div>

            <div className="hero-score">
              <div>
                <span>Resolution health</span>
                <strong>94%</strong>
              </div>

              <div className="hero-progress">
                <span />
              </div>
            </div>

            <div className="hero-flow">
              <div className="hero-flow-item active">
                <span>01</span>
                <div>
                  <strong>Submitted</strong>
                  <small>Complaint received</small>
                </div>
              </div>

              <div className="hero-flow-line" />

              <div className="hero-flow-item active">
                <span>02</span>
                <div>
                  <strong>AI Analysis</strong>
                  <small>Issue classified</small>
                </div>
              </div>

              <div className="hero-flow-line" />

              <div className="hero-flow-item">
                <span>03</span>
                <div>
                  <strong>Assigned</strong>
                  <small>Department notified</small>
                </div>
              </div>

              <div className="hero-flow-line" />

              <div className="hero-flow-item">
                <span>04</span>
                <div>
                  <strong>Resolved</strong>
                  <small>Citizen confirms</small>
                </div>
              </div>
            </div>

            <div className="hero-mini-grid">
              <div>
                <span>Priority</span>
                <strong>Normal</strong>
              </div>

              <div>
                <span>Department</span>
                <strong>Municipal</strong>
              </div>

              <div>
                <span>Updates</span>
                <strong>Enabled</strong>
              </div>
            </div>
          </div>

          <div className="hero-floating-card hero-floating-ai">
            <span className="floating-icon">✦</span>
            <div>
              <strong>AI analysis</strong>
              <small>Issue classified</small>
            </div>
            <span className="floating-check">✓</span>
          </div>

          <div className="hero-floating-card hero-floating-alert">
            <span className="floating-alert-dot" />
            <div>
              <strong>Status updated</strong>
              <small>Your complaint is in progress</small>
            </div>
          </div>
        </div>
      </section>

      <section className="home-trust-strip">
        <span>BUILT FOR BETTER CIVIC SERVICES</span>

        <div>
          <span>Citizen-first</span>
          <span>AI-assisted</span>
          <span>Transparent</span>
          <span>Accountable</span>
        </div>
      </section>

      <section
        id="features"
        className="home-section"
      >
        <div className="home-section-heading">
          <span className="home-section-kicker">
            ONE PLATFORM. COMPLETE VISIBILITY.
          </span>

          <h2>
            Everything needed to move
            <span> grievances forward.</span>
          </h2>

          <p>
            CivicResolve connects citizens, intelligent analysis and
            resolution teams in one structured workflow.
          </p>
        </div>

        <div className="feature-grid">
          <article className="feature-card feature-card-large">
            <div className="feature-number">01</div>
            <div className="feature-icon">✦</div>
            <h3>AI-powered analysis</h3>
            <p>
              Complaints are intelligently analyzed, categorized and
              routed to help reduce manual triage.
            </p>
            <span className="feature-link">
              Intelligent routing
              <ArrowIcon />
            </span>
          </article>

          <article className="feature-card">
            <div className="feature-number">02</div>
            <div className="feature-icon">◎</div>
            <h3>Multilingual complaints</h3>
            <p>
              Citizens can communicate naturally while preserving
              their original complaint.
            </p>
            <span className="feature-link">
              Language-aware
              <ArrowIcon />
            </span>
          </article>

          <article className="feature-card">
            <div className="feature-number">03</div>
            <div className="feature-icon">◉</div>
            <h3>Voice input</h3>
            <p>
              Speak your grievance instead of typing it from start
              to finish.
            </p>
            <span className="feature-link">
              Voice enabled
              <ArrowIcon />
            </span>
          </article>

          <article className="feature-card">
            <div className="feature-number">04</div>
            <div className="feature-icon">↗</div>
            <h3>Real-time tracking</h3>
            <p>
              Follow every meaningful status change through a clear
              complaint lifecycle.
            </p>
            <span className="feature-link">
              Full visibility
              <ArrowIcon />
            </span>
          </article>

          <article className="feature-card feature-card-wide">
            <div className="feature-number">05</div>
            <div className="feature-icon">◌</div>
            <h3>Resolution, feedback & reopen</h3>
            <p>
              Citizens can provide resolution feedback and reopen a
              complaint when an issue remains unresolved.
            </p>
            <span className="feature-link">
              Citizen feedback loop
              <ArrowIcon />
            </span>
          </article>

          <article className="feature-card">
            <div className="feature-number">06</div>
            <div className="feature-icon">⌁</div>
            <h3>Smart notifications</h3>
            <p>
              Stay informed when your complaint reaches important
              milestones.
            </p>
            <span className="feature-link">
              Never miss an update
              <ArrowIcon />
            </span>
          </article>
        </div>
      </section>

      <section
        id="how-it-works"
        className="home-process-section"
      >
        <div className="home-process-heading">
          <span className="home-section-kicker">
            HOW IT WORKS
          </span>

          <h2>
            From complaint to
            <span> resolution.</span>
          </h2>

          <p>
            A structured workflow gives citizens clarity while
            helping resolution teams act on the right information.
          </p>
        </div>

        <div className="process-timeline">
          <div className="process-step">
            <span>01</span>
            <div className="process-line" />
            <h3>Report</h3>
            <p>
              Submit your issue with text, voice and supporting
              evidence.
            </p>
          </div>

          <div className="process-step">
            <span>02</span>
            <div className="process-line" />
            <h3>Understand</h3>
            <p>
              AI analyzes the complaint and prepares structured
              information.
            </p>
          </div>

          <div className="process-step">
            <span>03</span>
            <div className="process-line" />
            <h3>Route</h3>
            <p>
              The complaint moves toward the relevant department
              and officer.
            </p>
          </div>

          <div className="process-step">
            <span>04</span>
            <div className="process-line" />
            <h3>Resolve</h3>
            <p>
              Track progress, receive updates and provide feedback
              after resolution.
            </p>
          </div>
        </div>
      </section>

      <section
        id="transparency"
        className="home-transparency-section"
      >
        <div className="transparency-panel">
          <div>
            <span className="home-section-kicker">
              TRANSPARENCY BY DESIGN
            </span>

            <h2>
              No more wondering
              <span> “what happened?”</span>
            </h2>

            <p>
              CivicResolve makes the complaint journey visible.
              Citizens can understand where their grievance is,
              what stage it has reached and what happens next.
            </p>

            <Link
              to="/register"
              className="home-primary-button"
            >
              Start your first complaint
              <ArrowIcon />
            </Link>
          </div>

          <div className="transparency-list">
            <div>
              <span>01</span>
              <strong>Complaint submitted</strong>
              <small>Your issue enters the system.</small>
            </div>

            <div>
              <span>02</span>
              <strong>AI-assisted analysis</strong>
              <small>Information is structured for processing.</small>
            </div>

            <div>
              <span>03</span>
              <strong>Department workflow</strong>
              <small>The issue moves through resolution stages.</small>
            </div>

            <div>
              <span>04</span>
              <strong>Resolution feedback</strong>
              <small>Your response closes the feedback loop.</small>
            </div>
          </div>
        </div>
      </section>

      <section className="home-ai-section">
        <div className="ai-visual">
          <div className="ai-glow" />
          <div className="ai-core">
            <span>CR</span>
          </div>

          <div className="ai-ring ai-ring-one" />
          <div className="ai-ring ai-ring-two" />
          <div className="ai-ring ai-ring-three" />
        </div>

        <div className="ai-copy">
          <span className="home-section-kicker">
            INTELLIGENCE WITHOUT COMPLEXITY
          </span>

          <h2>
            Technology that works
            <span> behind the scenes.</span>
          </h2>

          <p>
            CivicResolve uses AI to help transform unstructured
            citizen complaints into useful information for the
            resolution workflow while keeping the citizen experience
            simple.
          </p>

          <div className="ai-points">
            <div>
              <span>✓</span>
              <strong>Understand complaints</strong>
            </div>

            <div>
              <span>✓</span>
              <strong>Support categorization</strong>
            </div>

            <div>
              <span>✓</span>
              <strong>Assist prioritization</strong>
            </div>

            <div>
              <span>✓</span>
              <strong>Preserve the citizen's original voice</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="home-final-cta">
        <span className="home-section-kicker">
          YOUR CITY. YOUR VOICE.
        </span>

        <h2>
          Ready to make your
          <span> grievance count?</span>
        </h2>

        <p>
          Create your free citizen account and bring your first
          grievance into a transparent resolution workflow.
        </p>

        <Link
          to="/register"
          className="home-primary-button home-final-button"
        >
          Create your citizen account
          <ArrowIcon />
        </Link>
      </section>

      <footer className="home-footer">
        <div className="home-footer-brand">
          <span className="home-logo-mark">
            CR
          </span>

          <div>
            <strong>CivicResolve</strong>
            <span>
              GenAI-powered intelligent grievance & tracking system
            </span>
          </div>
        </div>

        <div className="home-footer-links">
          <Link to="/login">Sign in</Link>
          <Link to="/register">Register</Link>
        </div>

        <span className="home-footer-copy">
          Built for transparent civic resolution.
        </span>
      </footer>
    </main>
  );
}

export default HomePage;