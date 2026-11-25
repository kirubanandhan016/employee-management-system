import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, Lock, Mail, ShieldCheck } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { extractErrorMessage } from "../services/api";
import ErrorAlert from "../components/ErrorAlert";

const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@company.com", password: "Admin@123" },
  { label: "HR Manager", email: "hr@company.com", password: "HrManager@123" },
  { label: "Employee", email: "employee@company.com", password: "Employee@123" },
];

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Invalid email or password"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-brand-50 via-white to-slate-100">
      <div className="hidden w-1/2 flex-col justify-between bg-brand-700 p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 backdrop-blur-xs">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">PeoplePulse EMS</span>
        </div>

        <div className="max-w-md space-y-5">
          <h2 className="text-4xl font-bold leading-tight tracking-tight">
            Workforce operations, payroll, and analytics in one place.
          </h2>
          <p className="text-base leading-relaxed text-brand-100">
            Secure role-based platform built with FastAPI, PostgreSQL, SQLAlchemy 2.0, and React for modern HR teams.
          </p>
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="rounded-xl bg-white/10 p-4">
              <p className="text-2xl font-bold">RBAC</p>
              <p className="mt-1 text-xs text-brand-100">Admin, HR Manager & Employee isolation</p>
            </div>
            <div className="rounded-xl bg-white/10 p-4">
              <p className="text-2xl font-bold">Argon2</p>
              <p className="mt-1 text-xs text-brand-100">JWT auth & salted password hashing</p>
            </div>
          </div>
        </div>

        <p className="text-xs text-brand-200">© 2026 PeoplePulse Enterprise EMS</p>
      </div>

      <div className="flex flex-1 items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center lg:text-left">
            <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white lg:hidden">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Sign in to your account</h1>
            <p className="mt-1.5 text-sm text-slate-500">Enter your company credentials to access your dashboard</p>
          </div>

          <div className="card p-6 sm:p-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <ErrorAlert message={error} onDismiss={() => setError("")} />

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Email Address</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field pl-9"
                    placeholder="name@company.com"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pl-9"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button type="submit" disabled={submitting} className="btn-primary w-full py-2.5">
                {submitting ? "Signing in..." : "Sign In"}
                {!submitting && <ArrowRight className="h-4 w-4" />}
              </button>
            </form>

            <div className="mt-6 border-t border-slate-100 pt-5">
              <p className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                Quick-fill Demo Credentials
              </p>
              <div className="grid grid-cols-3 gap-2">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.label}
                    type="button"
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword(acc.password);
                      setError("");
                    }}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2 text-xs font-semibold text-slate-700 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                  >
                    {acc.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <p className="text-center text-sm text-slate-600">
            New employee?{" "}
            <Link to="/register" className="font-semibold text-brand-600 hover:text-brand-700">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
