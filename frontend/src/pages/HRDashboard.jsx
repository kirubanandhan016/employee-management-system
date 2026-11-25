import { Building2, CalendarCheck, CalendarOff, Users } from "lucide-react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { AttendanceTrendChart, DepartmentDistributionChart } from "../components/Charts";

export default function HRDashboard({ data }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">HR Operations Dashboard</h2>
          <p className="text-sm text-slate-500">Workforce attendance, onboarding, and leave approval queue</p>
        </div>
        <div className="flex gap-2.5">
          <Link to="/leaves" className="btn-secondary">
            Review Leaves
          </Link>
          <Link to="/employees" className="btn-primary">
            Employee Directory
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Active Employees"
          value={data.active_employees}
          subtitle={`${data.total_employees} total records`}
          icon={Users}
          accent="blue"
        />
        <StatCard
          title="Departments"
          value={data.total_departments}
          subtitle="Active organizational units"
          icon={Building2}
          accent="indigo"
        />
        <StatCard
          title="Checked In Today"
          value={data.today_present + data.today_late}
          subtitle={`${data.today_present} present · ${data.today_late} late`}
          icon={CalendarCheck}
          accent="emerald"
        />
        <StatCard
          title="Pending Leave Queue"
          value={data.pending_leave_requests}
          subtitle="Requires HR approval"
          icon={CalendarOff}
          accent="amber"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AttendanceTrendChart data={data.attendance_trend} />
        <DepartmentDistributionChart departments={data.department_stats} />
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Leave Approval Queue</h3>
            <p className="text-xs text-slate-500">Most recent leave requests across departments</p>
          </div>
          <Link to="/leaves" className="btn-secondary px-3 py-1.5 text-xs">
            Open Leave Manager
          </Link>
        </div>

        <div className="mt-4 divide-y divide-slate-100">
          {data.recent_leaves.length === 0 ? (
            <p className="py-8 text-center text-xs text-slate-400">No leave requests to display.</p>
          ) : (
            data.recent_leaves.map((leave) => (
              <div key={leave.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {leave.employee_name}{" "}
                    <span className="text-xs font-normal text-slate-400">({leave.department_name || "No Dept"})</span>
                  </p>
                  <p className="text-xs text-slate-500">
                    <span className="capitalize">{leave.leave_type}</span> · {leave.start_date} → {leave.end_date} ({leave.days_count} day{leave.days_count > 1 ? "s" : ""})
                  </p>
                </div>
                <StatusBadge value={leave.status} />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
