/**
 * Login / register page. Backend contract: POST /auth/login (OAuth2
 * password form), POST /auth/register (JSON body).
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        await api.register(email, password);
      }
      const token = await api.login(email, password);
      localStorage.setItem("access_token", token);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong. Check your credentials and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="bg-paper border border-line rounded-lg p-8">
        <h1 className="font-mono text-lg text-graphite mb-1">
          {mode === "login" ? "Sign in" : "Create an account"}
        </h1>
        <p className="text-sm text-mist mb-6">
          {mode === "login" ? "Access your experiments." : "Start comparing how models write code."}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wide text-mist mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-line rounded px-3 py-2 text-sm font-mono focus:border-signal outline-none"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-mist mb-1">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-line rounded px-3 py-2 text-sm font-mono focus:border-signal outline-none"
            />
          </div>
          {error && <p className="text-sm text-channel-1 font-mono">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-signal text-white text-sm font-medium rounded px-4 py-2 disabled:opacity-50 hover:opacity-90 transition-opacity"
          >
            {submitting ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <button
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="text-xs text-mist hover:text-graphite mt-4 font-mono"
        >
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
