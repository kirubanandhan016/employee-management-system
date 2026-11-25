import { useCallback, useEffect, useState } from "react";
import { CalendarClock, CheckCircle2, Clock, Plus } from "lucide-react";
import { attendanceService } from "../services/attendanceService";
import { employeeService } from "../services/employeeService";
import { extractErrorMessage } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import DataTable from "../components/DataTable";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import ErrorAlert from "../components/ErrorAlert";
import Modal from "../components/Modal";

export default function AttendancePage() {
  const { isPrivileged, user } = useAuth();
  const [records, setRecords] = useState([]);
  const [report, setReport] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const [statusFilter, setStatusFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, totalPages: 1, pageSize: 15 });

  const [manualOpen, setManualOpen] = useState(false);
  const [manualForm, setManualForm] = useState({
    employee_id: "",
    date: new Date().toISOString().slice(0, 10),
    status: "present",
    notes: "",
  });

  const loadAttendance = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [listRes, reportRes] = await Promise.all([
        attendanceService.list({
          status: statusFilter || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          page,
          page_size: meta.pageSize,
        }),
        attendanceService.getReport({
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
      ]);
      setRecords(listRes.items || []);
      setMeta({ total: listRes.total, totalPages: listRes.total_pages, pageSize: listRes.page_size });
      setReport(reportRes);
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to fetch attendance records"));
    } finally {
      setLoading(false);
    }
  }, [statusFilter, startDate, endDate, page, meta.pageSize]);

  useEffect(() => {
    loadAttendance();
  }, [loadAttendance]);

  useEffect(() => {
    if (isPrivileged) {
      employeeService
        .list({ page: 1, page_size: 100 })
        .then((res) => setEmployees(res.items || []))
        .catch(() => {});
    }
  }, [isPrivileged]);

  const handleCheckIn = async () => {
    setError("");
    setSuccessMsg("");
    setActionLoading(true);
    try {
      await attendanceService.checkIn({});
      setSuccessMsg("Checked in successfully for today.");
      await loadAttendance();
    } catch (err) {
      setError(extractErrorMessage(err, "Check-in failed"));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckOut = async () => {
    setError("");
    setSuccessMsg("");
    setActionLoading(true);
    try {
      const res = await attendanceService.checkOut({});
      setSuccessMsg(`Checked out successfully. Total hours: ${res.work_hours || 0}h.`);
      await loadAttendance();
    } catch (err) {
      setError(extractErrorMessage(err, "Check-out failed"));
    } finally {
      setActionLoading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setActionLoading(true);
    try {
      await attendanceService.recordManual({
        employee_id: Number(manualForm.employee_id),
        date: manualForm.date,
        status: manualForm.status,
        notes: manualForm.notes || null,
      });
      setManualOpen(false);
      setSuccessMsg("Attendance entry recorded.");
      await loadAttendance();
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to save attendance entry"));
    } finally {
      setActionLoading(false);
    }
  };

  const columns = [
    {
      key: "employee",
      label: "Employee",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.employee_name || "—"}</p>
          <p className="text-xs text-slate-500">
            {row.employee_code} {row.department_name ? `· ${row.department_name}` : ""}
          </p>
        </div>
      ),
    },
    { key: "date", label: "Date" },
    {
      key: "check_in",
      label: "Check In",
      render: (row) => (row.check_in ? new Date(row.check_in).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"),
    },
    {
      key: "check_out",
      label: "Check Out",
      render: (row) => (row.check_out ? new Date(row.check_out).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"),
    },
    {
      key: "work_hours",
      label: "Hours",
      render: (row) => (row.work_hours !== null ? `${row.work_hours}h` : "—"),
    },
    {
      key: "status",
      label: "Status",
      render: (row) => <StatusBadge value={row.status} />,
    },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Attendance Management</h2>
          <p className="text-sm text-slate-500">Daily check-in/out logs, work hours, and attendance reports</p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {user?.employee_id && (
            <>
              <button type="button" onClick={handleCheckIn} disabled={actionLoading} className="btn-primary">
                <Clock className="h-4 w-4" />
                Check In
              </button>
              <button type="button" onClick={handleCheckOut} disabled={actionLoading} className="btn-secondary">
                <CheckCircle2 className="h-4 w-4" />
                Check Out
              </button>
            </>
          )}
          {isPrivileged && (
            <button type="button" onClick={() => setManualOpen(true)} className="btn-secondary">
              <Plus className="h-4 w-4" />
              Record Entry
            </button>
          )}
        </div>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />
      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">
          {successMsg}
        </div>
      )}

      {report && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Present Days" value={report.present_count} subtitle={`${report.start_date} to ${report.end_date}`} icon={CalendarClock} accent="blue" />
          <StatCard title="Late Check-ins" value={report.late_count} subtitle="Within selected range" icon={Clock} accent="amber" />
          <StatCard title="Absent / On Leave" value={report.absent_count + report.on_leave_count} subtitle={`${report.on_leave_count} on leave`} icon={CalendarClock} accent="rose" />
          <StatCard title="Avg Work Hours" value={`${report.average_work_hours}h`} subtitle={`Across ${report.total_records} records`} icon={CheckCircle2} accent="emerald" />
        </div>
      )}

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
        <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }} className="input-field" />
        <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }} className="input-field" />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="input-field">
          <option value="">All Statuses</option>
          <option value="present">Present</option>
          <option value="late">Late</option>
          <option value="half_day">Half Day</option>
          <option value="absent">Absent</option>
          <option value="on_leave">On Leave</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={records}
        loading={loading}
        page={page}
        totalPages={meta.totalPages}
        total={meta.total}
        pageSize={meta.pageSize}
        onPageChange={setPage}
      />

      <Modal isOpen={manualOpen} onClose={() => setManualOpen(false)} title="Manual Attendance Record">
        <form onSubmit={handleManualSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Employee *</label>
            <select
              required
              value={manualForm.employee_id}
              onChange={(e) => setManualForm((p) => ({ ...p, employee_id: e.target.value }))}
              className="input-field"
            >
              <option value="">Select Employee</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name} ({emp.employee_code})
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Date *</label>
              <input
                type="date"
                required
                value={manualForm.date}
                onChange={(e) => setManualForm((p) => ({ ...p, date: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Status *</label>
              <select
                value={manualForm.status}
                onChange={(e) => setManualForm((p) => ({ ...p, status: e.target.value }))}
                className="input-field"
              >
                <option value="present">Present</option>
                <option value="late">Late</option>
                <option value="half_day">Half Day</option>
                <option value="absent">Absent</option>
                <option value="on_leave">On Leave</option>
              </select>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Notes</label>
            <textarea
              rows={2}
              value={manualForm.notes}
              onChange={(e) => setManualForm((p) => ({ ...p, notes: e.target.value }))}
              className="input-field"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => setManualOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={actionLoading} className="btn-primary">
              Save Record
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
