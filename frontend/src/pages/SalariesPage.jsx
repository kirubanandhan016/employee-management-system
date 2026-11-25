import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, DollarSign, Edit3, Plus, Trash2, Wallet } from "lucide-react";
import { salaryService } from "../services/salaryService";
import { employeeService } from "../services/employeeService";
import { extractErrorMessage } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import DataTable from "../components/DataTable";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import ErrorAlert from "../components/ErrorAlert";
import Modal from "../components/Modal";
import ConfirmDialog from "../components/ConfirmDialog";

const INITIAL_SALARY_FORM = {
  employee_id: "",
  pay_month: new Date().getMonth() + 1,
  pay_year: new Date().getFullYear(),
  basic_salary: "",
  allowances: "0",
  deductions: "0",
  payment_status: "pending",
  notes: "",
};

export default function SalariesPage() {
  const { isAdmin, isPrivileged } = useAuth();
  const [salaries, setSalaries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [monthFilter, setMonthFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, totalPages: 1, pageSize: 15 });

  const [modalOpen, setModalOpen] = useState(false);
  const [editingSalary, setEditingSalary] = useState(null);
  const [form, setForm] = useState(INITIAL_SALARY_FORM);
  const [saving, setSaving] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, salary: null });

  const loadSalaries = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = {
        pay_month: monthFilter ? Number(monthFilter) : undefined,
        pay_year: yearFilter ? Number(yearFilter) : undefined,
        payment_status: statusFilter || undefined,
      };
      const [listRes, summaryRes] = await Promise.all([
        salaryService.list({ ...params, page, page_size: meta.pageSize }),
        salaryService.getSummary(params),
      ]);
      setSalaries(listRes.items || []);
      setMeta({ total: listRes.total, totalPages: listRes.total_pages, pageSize: listRes.page_size });
      setSummary(summaryRes);
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to fetch salary records"));
    } finally {
      setLoading(false);
    }
  }, [monthFilter, yearFilter, statusFilter, page, meta.pageSize]);

  useEffect(() => {
    loadSalaries();
  }, [loadSalaries]);

  useEffect(() => {
    if (isPrivileged) {
      employeeService
        .list({ page: 1, page_size: 100 })
        .then((res) => setEmployees(res.items || []))
        .catch(() => {});
    }
  }, [isPrivileged]);

  const openCreateModal = () => {
    setEditingSalary(null);
    setForm(INITIAL_SALARY_FORM);
    setModalOpen(true);
  };

  const openEditModal = (sal) => {
    setEditingSalary(sal);
    setForm({
      employee_id: String(sal.employee_id),
      pay_month: sal.pay_month,
      pay_year: sal.pay_year,
      basic_salary: String(sal.basic_salary),
      allowances: String(sal.allowances),
      deductions: String(sal.deductions),
      payment_status: sal.payment_status,
      notes: sal.notes || "",
    });
    setModalOpen(true);
  };

  const handleEmployeeSelect = (empId) => {
    const selected = employees.find((e) => String(e.id) === empId);
    setForm((prev) => ({
      ...prev,
      employee_id: empId,
      basic_salary: selected ? String(selected.base_salary) : prev.basic_salary,
    }));
  };

  const computedPreview =
    (Number(form.basic_salary || 0) || 0) +
    (Number(form.allowances || 0) || 0) -
    (Number(form.deductions || 0) || 0);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (editingSalary) {
        await salaryService.update(editingSalary.id, {
          basic_salary: Number(form.basic_salary),
          allowances: Number(form.allowances || 0),
          deductions: Number(form.deductions || 0),
          payment_status: form.payment_status,
          notes: form.notes || null,
        });
      } else {
        await salaryService.create({
          employee_id: Number(form.employee_id),
          pay_month: Number(form.pay_month),
          pay_year: Number(form.pay_year),
          basic_salary: Number(form.basic_salary),
          allowances: Number(form.allowances || 0),
          deductions: Number(form.deductions || 0),
          payment_status: form.payment_status,
          notes: form.notes || null,
        });
      }
      setModalOpen(false);
      await loadSalaries();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to save salary record"));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.salary) return;
    setSaving(true);
    setError("");
    try {
      await salaryService.remove(deleteDialog.salary.id);
      setDeleteDialog({ open: false, salary: null });
      await loadSalaries();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to delete salary record"));
      setDeleteDialog({ open: false, salary: null });
    } finally {
      setSaving(false);
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
    {
      key: "period",
      label: "Pay Period",
      render: (row) => `${String(row.pay_month).padStart(2, "0")}/${row.pay_year}`,
    },
    {
      key: "basic_salary",
      label: "Basic",
      render: (row) => `$${Number(row.basic_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
    {
      key: "allowances",
      label: "Allowances",
      render: (row) => `+$${Number(row.allowances).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
    {
      key: "deductions",
      label: "Deductions",
      render: (row) => `-$${Number(row.deductions).toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
    {
      key: "net_salary",
      label: "Net Salary",
      render: (row) => (
        <span className="font-bold text-slate-900">
          ${Number(row.net_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "payment_status",
      label: "Status",
      render: (row) => <StatusBadge value={row.payment_status} />,
    },
    ...(isPrivileged
      ? [
          {
            key: "actions",
            label: "Actions",
            headerClassName: "text-right",
            cellClassName: "text-right",
            render: (row) => (
              <div className="inline-flex items-center justify-end gap-1">
                <button
                  type="button"
                  onClick={() => openEditModal(row)}
                  className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-brand-600"
                  title="Edit salary record"
                >
                  <Edit3 className="h-4 w-4" />
                </button>
                {isAdmin && (
                  <button
                    type="button"
                    onClick={() => setDeleteDialog({ open: true, salary: row })}
                    className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                    title="Delete salary record"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ),
          },
        ]
      : []),
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Salary & Payroll Records</h2>
          <p className="text-sm text-slate-500">
            {isPrivileged ? "Generate payroll runs, allowances, deductions, and payment status" : "Your monthly compensation and payslip history"}
          </p>
        </div>
        {isPrivileged && (
          <button type="button" onClick={openCreateModal} className="btn-primary">
            <Plus className="h-4 w-4" />
            Create Salary Record
          </button>
        )}
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />

      {summary && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            title="Total Net Payroll"
            value={`$${Number(summary.total_net_payroll).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
            subtitle={`${summary.total_records} record(s)`}
            icon={DollarSign}
            accent="blue"
          />
          <StatCard
            title="Allowances / Deductions"
            value={`+$${Number(summary.total_allowances).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            subtitle={`Deductions: -$${Number(summary.total_deductions).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            icon={Wallet}
            accent="indigo"
          />
          <StatCard
            title="Disbursement Status"
            value={`${summary.paid_count} Paid`}
            subtitle={`${summary.pending_count} pending`}
            icon={CheckCircle2}
            accent="emerald"
          />
        </div>
      )}

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
        <select value={monthFilter} onChange={(e) => { setMonthFilter(e.target.value); setPage(1); }} className="input-field">
          <option value="">All Months</option>
          {Array.from({ length: 12 }, (_, idx) => idx + 1).map((m) => (
            <option key={m} value={m}>
              Month {String(m).padStart(2, "0")}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="2000"
          max="2100"
          placeholder="Filter by Year (e.g. 2026)"
          value={yearFilter}
          onChange={(e) => { setYearFilter(e.target.value); setPage(1); }}
          className="input-field"
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="input-field">
          <option value="">All Payment Statuses</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={salaries}
        loading={loading}
        page={page}
        totalPages={meta.totalPages}
        total={meta.total}
        pageSize={meta.pageSize}
        onPageChange={setPage}
      />

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingSalary ? "Update Salary Record" : "Create Salary Record"}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {!editingSalary && (
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Employee *</label>
              <select
                required
                value={form.employee_id}
                onChange={(e) => handleEmployeeSelect(e.target.value)}
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
          )}

          {!editingSalary && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Month *</label>
                <input
                  type="number"
                  min={1}
                  max={12}
                  required
                  value={form.pay_month}
                  onChange={(e) => setForm((p) => ({ ...p, pay_month: e.target.value }))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Year *</label>
                <input
                  type="number"
                  min={2000}
                  max={2100}
                  required
                  value={form.pay_year}
                  onChange={(e) => setForm((p) => ({ ...p, pay_year: e.target.value }))}
                  className="input-field"
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Basic Salary *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={form.basic_salary}
                onChange={(e) => setForm((p) => ({ ...p, basic_salary: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Allowances</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.allowances}
                onChange={(e) => setForm((p) => ({ ...p, allowances: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Deductions</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.deductions}
                onChange={(e) => setForm((p) => ({ ...p, deductions: e.target.value }))}
                className="input-field"
              />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl bg-brand-50 px-4 py-3">
            <span className="text-xs font-semibold text-brand-700">Calculated Net Salary</span>
            <span className="text-lg font-bold text-brand-900">
              ${Math.max(0, computedPreview).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Payment Status</label>
            <select
              value={form.payment_status}
              onChange={(e) => setForm((p) => ({ ...p, payment_status: e.target.value }))}
              className="input-field"
            >
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Notes</label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
              className="input-field"
            />
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving || computedPreview < 0} className="btn-primary">
              {saving ? "Saving..." : editingSalary ? "Save Changes" : "Create Record"}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, salary: null })}
        onConfirm={handleDelete}
        loading={saving}
        title="Delete Salary Record"
        confirmLabel="Delete Record"
        message={`Delete salary record for ${deleteDialog.salary?.employee_name} (${deleteDialog.salary?.pay_month}/${deleteDialog.salary?.pay_year})?`}
      />
    </div>
  );
}
