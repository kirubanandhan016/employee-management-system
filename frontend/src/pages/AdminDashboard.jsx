import { Building2, CalendarCheck, CalendarOff, DollarSign, UserCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import {
  AttendanceTrendChart,
  DepartmentDistributionChart,
  PayrollTrendChart,
} from "../components/Charts";

export default function AdminDashboard({ data }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Executive Admin Overview</h2>
          <p className="text-sm text-slate-500">Company-wide headcount, attendance, leaves, and payroll metrics</p>
        </div>
        <div className="flex gap-2.5">
          <Link to="/employees" className="btn-secondary">
            Manage Employees
          </Link>
          <Link to="/salaries" className="btn-primary">
            Run Payroll
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Employees"
          value={data.total_employees}
          subtitle={`${data.active_employees} active · ${data.inactive_employees} inactive`}
          icon={Users}
          accent="blue"
        />
        <StatCard
          title="Today's Attendance"
          value={data.today_present + data.today_late}
          subtitle={`${data.today_present} on time · ${data.today_late} late`}
          icon={CalendarCheck}
          accent="emerald"
        />
        <StatCard
          title="Pending Leaves"
          value={data.pending_leave_requests}
          subtitle="Awaiting HR/Admin review"
          icon={CalendarOff}
          accent="amber"
        />
        <StatCard
          title="Latest Monthly Payroll"
          value={`$${Number(data.monthly_payroll_total || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          subtitle={`${data.total_departments} active departments`}
          icon={DollarSign}
          accent="indigo"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AttendanceTrendChart data={data.attendance_trend} />
        <PayrollTrendChart data={data.payroll_trend} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <DepartmentDistributionChart departments={data.department_stats} />

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Recent Leave Requests</h3>
              <p className="text-xs text-slate-500">Latest employee time-off submissions</p>
            </div>
            <Link to="/leaves" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
              View all
            </Link>
          </div>

          <div className="mt-4 divide-y divide-slate-100">
            {data.recent_leaves.length === 0 ? (
              <p className="py-8 text-center text-xs text-slate-400">No leave requests submitted yet.</p>
            ) : (
              data.recent_leaves.map((leave) => (
                <div key={leave.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{leave.employee_name}</p>
                    <p className="text-xs text-slate-500">
                      <span className="capitalize">{leave.leave_type}</span> · {leave.start_date} to {leave.end_date} (
                      {leave.days_count}d)
                    </p>
                  </div>
                  <StatusBadge value={leave.status} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <UserCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500">Active Workforce Rate</p>
            <p className="text-base font-bold text-slate-900">
              {data.total_employees > 0
                ? `${Math.round((data.active_employees / data.total_employees) * 100)}%`
                : "0%"}
            </p>
          </div>
        </div>
        <div className="card flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500">Departments</p>
            <p className="text-base font-bold text-slate-900">{data.total_departments} Units</p>
          </div>
        </div>
        <div className="card flex items-center gap-3 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <CalendarCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500">On Leave / Absent Today</p>
            <p className="text-base font-bold text-slate-900">{data.today_on_leave + data.today_absent}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
