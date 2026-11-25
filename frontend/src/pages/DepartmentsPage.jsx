import { useCallback, useEffect, useState } from "react";
import { Building2, Edit3, Plus, Trash2, Users } from "lucide-react";
import { departmentService } from "../services/departmentService";
import { employeeService } from "../services/employeeService";
import { extractErrorMessage } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";
import Modal from "../components/Modal";
import ConfirmDialog from "../components/ConfirmDialog";

export default function DepartmentsPage() {
  const { isPrivileged } = useAuth();
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [form, setForm] = useState({ name: "", code: "", description: "", manager_id: "" });
  const [saving, setSaving] = useState(false);

  const [assignModal, setAssignModal] = useState({ open: false, dept: null, selectedIds: [] });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, dept: null });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const deptRes = await departmentService.list({ page: 1, page_size: 100 });
      setDepartments(deptRes.items || []);
      if (isPrivileged) {
        const empRes = await employeeService.list({ page: 1, page_size: 100 });
        setEmployees(empRes.items || []);
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to load departments"));
    } finally {
      setLoading(false);
    }
  }, [isPrivileged]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openCreateModal = () => {
    setEditingDept(null);
    setForm({ name: "", code: "", description: "", manager_id: "" });
    setModalOpen(true);
  };

  const openEditModal = (dept) => {
    setEditingDept(dept);
    setForm({
      name: dept.name,
      code: dept.code,
      description: dept.description || "",
      manager_id: dept.manager_id ? String(dept.manager_id) : "",
    });
    setModalOpen(true);
  };

  const handleSaveDepartment = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        name: form.name.trim(),
        code: form.code.trim().toUpperCase(),
        description: form.description.trim() || null,
        manager_id: form.manager_id ? Number(form.manager_id) : null,
      };
      if (editingDept) {
        await departmentService.update(editingDept.id, payload);
      } else {
        await departmentService.create(payload);
      }
      setModalOpen(false);
      await loadData();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to save department"));
    } finally {
      setSaving(false);
    }
  };

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!assignModal.dept || assignModal.selectedIds.length === 0) return;
    setSaving(true);
    setError("");
    try {
      await departmentService.assignEmployees(assignModal.dept.id, assignModal.selectedIds);
      setAssignModal({ open: false, dept: null, selectedIds: [] });
      await loadData();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to assign employees"));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.dept) return;
    setSaving(true);
    setError("");
    try {
      await departmentService.remove(deleteDialog.dept.id);
      setDeleteDialog({ open: false, dept: null });
      await loadData();
    } catch (err) {
      setError(extractErrorMessage(err, "Cannot delete department"));
      setDeleteDialog({ open: false, dept: null });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading departments..." />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Departments</h2>
          <p className="text-sm text-slate-500">Organizational units, department leads, and headcount</p>
        </div>
        {isPrivileged && (
          <button type="button" onClick={openCreateModal} className="btn-primary">
            <Plus className="h-4 w-4" />
            New Department
          </button>
        )}
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {departments.map((dept) => (
          <div key={dept.id} className="card flex flex-col justify-between p-5">
            <div>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                    <Building2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">{dept.name}</h3>
                    <span className="text-xs font-semibold uppercase tracking-wider text-brand-600">{dept.code}</span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                  <Users className="h-3.5 w-3.5" />
                  {dept.employee_count}
                </span>
              </div>

              <p className="mt-3 text-sm text-slate-600">{dept.description || "No description provided."}</p>
              <p className="mt-3 text-xs text-slate-500">
                Manager: <span className="font-semibold text-slate-700">{dept.manager_name || "Unassigned"}</span>
              </p>
            </div>

            {isPrivileged && (
              <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-3.5">
                <button
                  type="button"
                  onClick={() => setAssignModal({ open: true, dept, selectedIds: [] })}
                  className="text-xs font-semibold text-brand-600 hover:text-brand-700"
                >
                  Assign Employees
                </button>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => openEditModal(dept)}
                    className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-brand-600"
                    title="Edit department"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteDialog({ open: true, dept })}
                    className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                    title="Delete department"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingDept ? "Edit Department" : "Create Department"}
      >
        <form onSubmit={handleSaveDepartment} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Department Name *</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                className="input-field"
                placeholder="Engineering"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Code *</label>
              <input
                required
                value={form.code}
                onChange={(e) => setForm((p) => ({ ...p, code: e.target.value }))}
                className="input-field"
                placeholder="ENG"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Department Manager</label>
            <select
              value={form.manager_id}
              onChange={(e) => setForm((p) => ({ ...p, manager_id: e.target.value }))}
              className="input-field"
            >
              <option value="">No Manager</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name} ({emp.employee_code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Description</label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              className="input-field"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Saving..." : editingDept ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={assignModal.open}
        onClose={() => setAssignModal({ open: false, dept: null, selectedIds: [] })}
        title={`Assign Employees to ${assignModal.dept?.name || ""}`}
      >
        <form onSubmit={handleAssignSubmit} className="space-y-4">
          <div className="max-h-64 space-y-2 overflow-y-auto rounded-xl border border-slate-200 p-3">
            {employees.map((emp) => {
              const checked = assignModal.selectedIds.includes(emp.id);
              return (
                <label key={emp.id} className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-slate-50">
                  <span className="flex items-center gap-2.5 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {
                        setAssignModal((prev) => ({
                          ...prev,
                          selectedIds: checked
                            ? prev.selectedIds.filter((id) => id !== emp.id)
                            : [...prev.selectedIds, emp.id],
                        }));
                      }}
                      className="h-4 w-4 rounded border-slate-300 text-brand-600"
                    />
                    {emp.full_name}
                  </span>
                  <span className="text-xs text-slate-400">{emp.department_name || "Unassigned"}</span>
                </label>
              );
            })}
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setAssignModal({ open: false, dept: null, selectedIds: [] })}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button type="submit" disabled={saving || assignModal.selectedIds.length === 0} className="btn-primary">
              {saving ? "Assigning..." : "Assign Selected"}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, dept: null })}
        onConfirm={handleDelete}
        loading={saving}
        title="Delete Department"
        confirmLabel="Delete Department"
        message={`Are you sure you want to delete "${deleteDialog.dept?.name}"? Deletion is blocked if employees are still assigned to it.`}
      />
    </div>
  );
}
