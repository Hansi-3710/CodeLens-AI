/**
 * Root component: nav shell + routes. Auth guard is intentionally simple
 * (redirect to /login if no token) — see core/security.py on the backend
 * for the actual JWT validation; the frontend only avoids showing pages
 * that would immediately 401.
 *
 * Pages are lazy-loaded (React.lazy + Suspense): the production build
 * flagged a 661KB main chunk (recharts + react-query + axios all in one
 * bundle) — splitting per-route means a first visit to /login doesn't pay
 * for ExperimentResults/Visualization's chart code it doesn't use yet.
 *
 * Belongs to: frontend/src/
 * Phase: 7 (Frontend); code-splitting added in the post-audit hardening pass.
 */
import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, Link, useLocation } from "react-router-dom";

const CreateExperiment = lazy(() => import("./pages/CreateExperiment"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const ExperimentResults = lazy(() => import("./pages/ExperimentResults"));
const Login = lazy(() => import("./pages/Login"));
const ModelComparison = lazy(() => import("./pages/ModelComparison"));
const Visualization = lazy(() => import("./pages/Visualization"));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

function PageLoading() {
  return (
    <div className="flex items-center justify-center py-24" role="status" aria-live="polite">
      <span className="text-mist text-sm font-mono">Loading…</span>
    </div>
  );
}

function NavShell({ children }: { children: React.ReactNode }) {
  const isAuthed = !!localStorage.getItem("access_token");
  return (
    <div className="min-h-screen bg-ink">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:bg-signal focus:text-white focus:px-3 focus:py-2 focus:rounded focus:z-50"
      >
        Skip to content
      </a>
      <header className="border-b border-white/10">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="font-mono text-sm text-paper tracking-tight">
            llm-code-intelligence<span className="text-signal">/</span>
          </Link>
          {isAuthed && (
            <button
              onClick={() => {
                localStorage.removeItem("access_token");
                window.location.href = "/login";
              }}
              className="text-xs font-mono text-mist hover:text-paper transition-colors"
              aria-label="Sign out"
            >
              sign out
            </button>
          )}
        </div>
      </header>
      <main id="main-content" className="max-w-6xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <NavShell>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/experiments/new" element={<RequireAuth><CreateExperiment /></RequireAuth>} />
          <Route path="/experiments/:id" element={<RequireAuth><ExperimentResults /></RequireAuth>} />
          <Route path="/experiments/:id/compare" element={<RequireAuth><ModelComparison /></RequireAuth>} />
          <Route path="/experiments/:id/visualize" element={<RequireAuth><Visualization /></RequireAuth>} />
        </Routes>
      </Suspense>
    </NavShell>
  );
}
