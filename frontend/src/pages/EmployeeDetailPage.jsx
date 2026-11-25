import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Building2, Calendar, DollarSign, Mail, Phone } from "lucide-react";
import { employeeService } from "../services/employeeService";
import { attendanceService } from "../services/attendanceService";
import { salaryService } from "../services/salaryService";
import { extractErrorMessage } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";
import StatusBadge from "../components/StatusBadge";

export default function EmployeeDetailPage() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [salaries, setSalaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDetails = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [empData, attData, salData] = await Promise.all([
        employeeService.getById(id),
        attendanceService.list({ employee_id: id, page: 1, page_size: 5 }),
        salaryService.list({ employee_id: id, page: 1, page_size: 5 }),
      ]);
      setEmployee(empData);
      setAttendance(attData.items || []);
      setSalaries(salData.items || []);
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to load employee profile"));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadDetails();
  }, [loadDetails]);

  if (loading) return <LoadingSpinner label="Loading employee profile..." />;
  if (error) return <ErrorAlert message={error} />;
  if (!employee) return null;

  return (
    <div className="space-y-6">
      <Link to="/employees" className="inline-flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-700">
        <ArrowLeft className="h-4 w-4" />
        Back to Employee Directory
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-lg font-bold text-white">
              {employee.first_name[0]}
              {employee.last_name[0]}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-slate-900">{employee.full_name}</h2>
                <StatusBadge value={employee.status} />
              </div>
              <p className="text-sm text-slate-500">
                {employee.job_title} · {employee.employee_code}
              </p>
            </div>
          </div>

          <div className="rounded-xl bg-brand-50 px-4 py-2.5 text-right">
            <p className="text-xs font-semibold text-brand-700">Monthly Base Salary</p>
            <p className="text-lg font-bold text-brand-900">
              ${Number(employee.base_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 border-t border-slate-100 pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex items-center gap-2.5 text-sm text-slate-600">
            <Mail className="h-4 w-4 text-slate-400" />
            <span>{employee.email}</span>
          </div>
          <div className="flex items-center gap-2.5 text-sm text-slate-600">
            <Phone className="h-4 w-4 text-slate-400" />
            <span>{employee.phone || "No phone provided"}</span>
          </div>
          <div className="flex items-center gap-2.5 text-sm text-slate-600">
            <Building2 className="h-4 w-4 text-slate-400" />
            <span>{employee.department_name || "Unassigned Department"}</span>
          </div>
          <div className="flex items-center gap-2.5 text-sm text-slate-600">
            <Calendar className="h-4 w-4 text-slate-400" />
            <span>Hired {employee.hire_date}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900">Recent Attendance</h3>
          <div className="mt-4 divide-y divide-slate-100">
            {attendance.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-400">No attendance history yet.</p>
            ) : (
              attendance.map((att) => (
                <div key={att.id} className="flex items-center justify-between py-2.5 text-sm">
                  <div>
                    <p className="font-medium text-slate-800">{att.date}</p>
                    <p className="text-xs text-slate-500">
                      {att.work_hours ? `${att.work_hours} hrs worked` : "Check-out pending"}
                    </p>
                  </div>
                  <StatusBadge value={att.status} />
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900">Recent Salary Records</h3>
          <div className="mt-4 divide-y divide-slate-100">
            {salaries.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-400">No salary records generated yet.</p>
            ) : (
              salaries.map((sal) => (
                <div key={sal.id} className="flex items-center justify-between py-2.5 text-sm">
                  <div className="flex items-center gap-2.5">
                    <DollarSign className="h-4 w-4 text-brand-600" />
                    <div>
                      <p className="font-medium text-slate-800">
                        {String(sal.pay_month).padStart(2, "0")}/{sal.pay_year}
                      </p>
                      <p className="text-xs text-slate-500">
                        Net: ${Number(sal.net_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                  </div>
                  <StatusBadge value={sal.payment_status} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
