import { useState } from "react";
import { CalendarClock, CalendarOff, CheckCircle2, Clock, DollarSign } from "lucide-react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import ErrorAlert from "../components/ErrorAlert";
import { AttendanceTrendChart } from "../components/Charts";
import { attendanceService } from "../services/attendanceService";
import { extractErrorMessage } from "../services/api";
import { useAuth } from "../hooks/useAuth";

export default function EmployeeDashboard({ data, onRefresh }) {
  const { user } = useAuth();
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  const todayAtt = data.today_attendance;
  const canCheckIn = !todayAtt;
  const canCheckOut = Boolean(todayAtt && todayAtt.check_in && !todayAtt.check_out);

  const handleCheckIn = async () => {
    setError("");
    setActionLoading(true);
    try {
      await attendanceService.checkIn({});
      await onRefresh();
    } catch (err) {
      setError(extractErrorMessage(err, "Check-in failed"));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckOut = async () => {
    setError("");
    setActionLoading(true);
    try {
      await attendanceService.checkOut({});
      await onRefresh();
    } catch (err) {
      setError(extractErrorMessage(err, "Check-out failed"));
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-gradient-to-r from-brand-700 to-brand-600 p-6 text-white shadow-sm">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-100">Employee Self-Service</p>
          <h2 className="mt-1 text-2xl font-bold">Welcome back, {user?.full_name}</h2>
          <p className="mt-1 text-sm text-brand-100">
            {user?.employee_code ? `Employee ID: ${user.employee_code}` : "Manage your attendance, leave requests, and payslips"}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {canCheckIn && (
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-brand-700 shadow-sm transition hover:bg-brand-50 disabled:opacity-60"
            >
              <Clock className="h-4 w-4" />
              {actionLoading ? "Recording..." : "Check In Today"}
            </button>
          )}
          {canCheckOut && (
            <button
              type="button"
              onClick={handleCheckOut}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:opacity-60"
            >
              <CheckCircle2 className="h-4 w-4" />
              {actionLoading ? "Recording..." : "Check Out"}
            </button>
          )}
          {!canCheckIn && !canCheckOut && (
            <span className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold text-white">
              <CheckCircle2 className="h-4 w-4" />
              Shift Completed ({todayAtt?.work_hours || 0}h)
            </span>
          )}
        </div>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Today's Status"
          value={todayAtt ? todayAtt.status.replace("_", " ").toUpperCase() : "Not Checked In"}
          subtitle={
            todayAtt?.check_in
              ? `In: ${new Date(todayAtt.check_in).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}${
                  todayAtt.check_out
                    ? ` · Out: ${new Date(todayAtt.check_out).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                    : ""
                }`
              : "Tap Check In Today to start your shift"
          }
          icon={CalendarClock}
          accent="blue"
        />
        <StatCard
          title="Pending Leave Requests"
          value={data.pending_leave_requests}
          subtitle="Awaiting review"
          icon={CalendarOff}
          accent="amber"
        />
        <StatCard
          title="Latest Net Salary"
          value={
            data.latest_salary
              ? `$${Number(data.latest_salary.net_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
              : "No Payslip"
          }
          subtitle={
            data.latest_salary
              ? `Period ${String(data.latest_salary.pay_month).padStart(2, "0")}/${data.latest_salary.pay_year} · ${data.latest_salary.payment_status}`
              : "No salary records yet"
          }
          icon={DollarSign}
          accent="emerald"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AttendanceTrendChart data={data.attendance_trend} />

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">My Leave History</h3>
              <p className="text-xs text-slate-500">Recent time-off applications</p>
            </div>
            <Link to="/leaves" className="btn-primary px-3 py-1.5 text-xs">
              Apply for Leave
            </Link>
          </div>
          <div className="mt-4 divide-y divide-slate-100">
            {data.recent_leaves.length === 0 ? (
              <p className="py-8 text-center text-xs text-slate-400">You have not submitted any leave requests yet.</p>
            ) : (
              data.recent_leaves.map((leave) => (
                <div key={leave.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <p className="text-sm font-medium capitalize text-slate-900">{leave.leave_type} Leave</p>
                    <p className="text-xs text-slate-500">
                      {leave.start_date} to {leave.end_date} ({leave.days_count}d)
                    </p>
                  </div>
                  <StatusBadge value={leave.status} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
