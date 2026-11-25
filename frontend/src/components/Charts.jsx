export function AttendanceTrendChart({ data = [] }) {
  const maxDayTotal = Math.max(
    1,
    ...data.map((d) => (d.present || 0) + (d.late || 0) + (d.absent || 0) + (d.on_leave || 0))
  );

  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">7-Day Attendance Activity</h3>
          <p className="text-xs text-slate-500">Daily check-ins by status</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-brand-600" />
            Present
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
            Late
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
            Absent/Leave
          </span>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="py-10 text-center text-xs text-slate-400">No attendance activity recorded yet.</div>
      ) : (
        <div className="mt-6 flex h-44 items-end justify-between gap-2 sm:gap-4">
          {data.map((point) => {
            const presentPct = ((point.present || 0) / maxDayTotal) * 100;
            const latePct = ((point.late || 0) / maxDayTotal) * 100;
            const otherPct = (((point.absent || 0) + (point.on_leave || 0)) / maxDayTotal) * 100;
            const totalForDay = (point.present || 0) + (point.late || 0) + (point.absent || 0) + (point.on_leave || 0);
            const label = new Date(`${point.date}T00:00:00`).toLocaleDateString(undefined, {
              weekday: "short",
            });

            return (
              <div key={point.date} className="flex flex-1 flex-col items-center gap-2">
                <div className="group relative flex h-32 w-full max-w-[38px] flex-col-reverse overflow-hidden rounded-lg bg-slate-100">
                  <div
                    style={{ height: `${presentPct}%` }}
                    className="w-full bg-brand-600 transition-all duration-300"
                    title={`Present: ${point.present}`}
                  />
                  <div
                    style={{ height: `${latePct}%` }}
                    className="w-full bg-amber-400 transition-all duration-300"
                    title={`Late: ${point.late}`}
                  />
                  <div
                    style={{ height: `${otherPct}%` }}
                    className="w-full bg-rose-400 transition-all duration-300"
                    title={`Absent/Leave: ${(point.absent || 0) + (point.on_leave || 0)}`}
                  />
                </div>
                <div className="text-center">
                  <p className="text-[11px] font-medium text-slate-600">{label}</p>
                  <p className="text-[10px] text-slate-400">{totalForDay}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function DepartmentDistributionChart({ departments = [] }) {
  const maxCount = Math.max(1, ...departments.map((d) => d.employee_count || 0));

  return (
    <div className="card p-5">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">Department Headcount</h3>
        <p className="text-xs text-slate-500">Employees and base payroll allocation</p>
      </div>

      {departments.length === 0 ? (
        <div className="py-10 text-center text-xs text-slate-400">No department metrics available.</div>
      ) : (
        <div className="mt-5 space-y-3.5">
          {departments.map((dept) => {
            const widthPct = Math.round(((dept.employee_count || 0) / maxCount) * 100);
            return (
              <div key={dept.department_id}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700">
                    {dept.department_name}{" "}
                    <span className="text-slate-400">({dept.department_code})</span>
                  </span>
                  <span className="font-semibold text-slate-900">
                    {dept.employee_count} {dept.employee_count === 1 ? "member" : "members"}
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-700 transition-all duration-300"
                    style={{ width: `${Math.max(widthPct, dept.employee_count > 0 ? 6 : 0)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function PayrollTrendChart({ data = [] }) {
  const maxVal = Math.max(1, ...data.map((d) => Number(d.total_net_salary || 0)));

  return (
    <div className="card p-5">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">Monthly Payroll Trend</h3>
        <p className="text-xs text-slate-500">Total net disbursements across recent periods</p>
      </div>

      {data.length === 0 ? (
        <div className="py-10 text-center text-xs text-slate-400">No salary records generated yet.</div>
      ) : (
        <div className="mt-6 flex h-44 items-end justify-between gap-3">
          {data.map((item) => {
            const total = Number(item.total_net_salary || 0);
            const paid = Number(item.paid_amount || 0);
            const heightPct = Math.max(8, Math.round((total / maxVal) * 100));
            const paidPct = total > 0 ? Math.round((paid / total) * 100) : 0;
            return (
              <div key={item.period} className="flex flex-1 flex-col items-center gap-2">
                <p className="text-[11px] font-semibold text-slate-700">
                  ${total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <div className="flex h-28 w-full max-w-[46px] items-end rounded-lg bg-slate-100 p-1">
                  <div
                    style={{ height: `${heightPct}%` }}
                    className="relative w-full overflow-hidden rounded-md bg-brand-200 transition-all duration-300"
                    title={`Total: $${total.toLocaleString()} | Paid: $${paid.toLocaleString()}`}
                  >
                    <div
                      style={{ height: `${paidPct}%` }}
                      className="absolute bottom-0 left-0 right-0 bg-brand-600 transition-all duration-300"
                    />
                  </div>
                </div>
                <p className="text-[11px] font-medium text-slate-500">{item.period}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
