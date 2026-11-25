import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Edit3, Eye, Plus, Search, Trash2, UserX } from "lucide-react";
import { employeeService } from "../services/employeeService";
import { departmentService } from "../services/departmentService";
import { extractErrorMessage } from "../services/api";
import { useDebounce } from "../hooks/useDebounce";
import DataTable from "../components/DataTable";
import StatusBadge from "../components/StatusBadge";
import ErrorAlert from "../components/ErrorAlert";
import ConfirmDialog from "../components/ConfirmDialog";
import EmployeeFormModal from "../components/EmployeeFormModal";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [departmentId, setDepartmentId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, totalPages: 1, pageSize: 10 });

  const [formOpen, setFormOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [confirmState, setConfirmState] = useState({ open: false, mode: null, employee: null });
  const [actionLoading, setActionLoading] = useState(false);

  const loadDepartments = useCallback(async () => {
    try {
      const res = await departmentService.list({ page: 1, page_size: 100 });
      setDepartments(res.items || []);
    } catch {
      // Non-blocking for directory render
    }
  }, []);

  const loadEmployees = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await employeeService.list({
        search: debouncedSearch || undefined,
        department_id: departmentId ? Number(departmentId) : undefined,
        status: statusFilter || undefined,
        page,
        page_size: meta.pageSize,
      });
      setEmployees(res.items);
      setMeta({ total: res.total, totalPages: res.total_pages, pageSize: res.page_size });
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to load employees"));
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, departmentId, statusFilter, page, meta.pageSize]);

  useEffect(() => {
    loadDepartments();
  }, [loadDepartments]);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  const handleConfirmAction = async () => {
    if (!confirmState.employee) return;
    setActionLoading(true);
    setError("");
    try {
      if (confirmState.mode === "deactivate") {
        await employeeService.deactivate(confirmState.employee.id);
      } else if (confirmState.mode === "delete") {
        await employeeService.remove(confirmState.employee.id);
      }
      setConfirmState({ open: false, mode: null, employee: null });
      await loadEmployees();
    } catch (err) {
      setError(extractErrorMessage(err, "Operation failed"));
      setConfirmState({ open: false, mode: null, employee: null });
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
          <Link to={`/employees/${row.id}`} className="font-semibold text-slate-900 hover:text-brand-600">
            {row.full_name}
          </Link>
          <p className="text-xs text-slate-500">
            {row.employee_code} · {row.email}
          </p>
        </div>
      ),
    },
    {
      key: "department_name",
      label: "Department & Role",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-800">{row.job_title}</p>
          <p className="text-xs text-slate-500">{row.department_name || "Unassigned"}</p>
        </div>
      ),
    },
    {
      key: "employment_type",
      label: "Type",
      render: (row) => <span className="capitalize text-slate-600">{row.employment_type.replace("_", " ")}</span>,
    },
    {
      key: "base_salary",
      label: "Base Salary",
      render: (row) => (
        <span className="font-medium text-slate-900">
          ${Number(row.base_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (row) => <StatusBadge value={row.status} />,
    },
    {
      key: "actions",
      label: "Actions",
      headerClassName: "text-right",
      cellClassName: "text-right",
      render: (row) => (
        <div className="inline-flex items-center justify-end gap-1.5">
          <Link
            to={`/employees/${row.id}`}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-brand-600"
            title="View details"
          >
            <Eye className="h-4 w-4" />
          </Link>
          <button
            type="button"
            onClick={() => {
              setEditingEmployee(row);
              setFormOpen(true);
            }}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-brand-600"
            title="Edit employee"
          >
            <Edit3 className="h-4 w-4" />
          </button>
          {row.status === "active" && (
            <button
              type="button"
              onClick={() => setConfirmState({ open: true, mode: "deactivate", employee: row })}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-amber-50 hover:text-amber-600"
              title="Deactivate employee"
            >
              <UserX className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setConfirmState({ open: true, mode: "delete", employee: row })}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
            title="Delete employee"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Employee Directory</h2>
          <p className="text-sm text-slate-500">Onboard, search, filter, and manage company personnel</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setEditingEmployee(null);
            setFormOpen(true);
          }}
          className="btn-primary"
        >
          <Plus className="h-4 w-4" />
          Add Employee
        </button>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-4">
        <div className="relative sm:col-span-2">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name, code, email, or title..."
            className="input-field pl-9"
          />
        </div>
        <select
          value={departmentId}
          onChange={(e) => {
            setDepartmentId(e.target.value);
            setPage(1);
          }}
          className="input-field"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="input-field"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="terminated">Terminated</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={employees}
        loading={loading}
        page={page}
        totalPages={meta.totalPages}
        total={meta.total}
        pageSize={meta.pageSize}
        onPageChange={setPage}
      />

      <EmployeeFormModal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        employee={editingEmployee}
        departments={departments}
        onSaved={loadEmployees}
      />

      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState({ open: false, mode: null, employee: null })}
        onConfirm={handleConfirmAction}
        loading={actionLoading}
        title={confirmState.mode === "deactivate" ? "Deactivate Employee" : "Delete Employee"}
        confirmLabel={confirmState.mode === "deactivate" ? "Deactivate" : "Delete Permanently"}
        message={
          confirmState.mode === "deactivate"
            ? `Are you sure you want to deactivate ${confirmState.employee?.full_name}? Their linked login account will be disabled.`
            : `Permanently delete ${confirmState.employee?.full_name}? Associated attendance, leaves, and salary history will also be removed.`
        }
      />
    </div>
  );
}
