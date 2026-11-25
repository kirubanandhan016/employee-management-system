import { useEffect, useState } from "react";
import Modal from "./Modal";
import ErrorAlert from "./ErrorAlert";
import { employeeService } from "../services/employeeService";
import { extractErrorMessage } from "../services/api";

const INITIAL_FORM = {
  employee_code: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  department_id: "",
  job_title: "",
  employment_type: "full_time",
  status: "active",
  hire_date: new Date().toISOString().slice(0, 10),
  base_salary: "",
  address: "",
  emergency_contact: "",
  create_user_account: false,
  account_password: "",
  account_role: "employee",
};

export default function EmployeeFormModal({ isOpen, onClose, employee, departments, onSaved }) {
  const isEditing = Boolean(employee);
  const [form, setForm] = useState(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (employee) {
      setForm({
        employee_code: employee.employee_code || "",
        first_name: employee.first_name || "",
        last_name: employee.last_name || "",
        email: employee.email || "",
        phone: employee.phone || "",
        department_id: employee.department_id ? String(employee.department_id) : "",
        job_title: employee.job_title || "",
        employment_type: employee.employment_type || "full_time",
        status: employee.status || "active",
        hire_date: employee.hire_date || new Date().toISOString().slice(0, 10),
        base_salary: String(employee.base_salary ?? ""),
        address: employee.address || "",
        emergency_contact: employee.emergency_contact || "",
        create_user_account: false,
        account_password: "",
        account_role: "employee",
      });
    } else {
      setForm(INITIAL_FORM);
    }
    setError("");
  }, [employee, isOpen]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const payload = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || null,
        department_id: form.department_id ? Number(form.department_id) : null,
        job_title: form.job_title.trim(),
        employment_type: form.employment_type,
        status: form.status,
        hire_date: form.hire_date,
        base_salary: Number(form.base_salary),
        address: form.address.trim() || null,
        emergency_contact: form.emergency_contact.trim() || null,
      };

      if (!isEditing) {
        if (form.employee_code.trim()) {
          payload.employee_code = form.employee_code.trim();
        }
        payload.create_user_account = form.create_user_account;
        if (form.create_user_account) {
          payload.account_password = form.account_password;
          payload.account_role = form.account_role;
        }
        await employeeService.create(payload);
      } else {
        await employeeService.update(employee.id, payload);
      }

      onSaved();
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to save employee"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? "Edit Employee" : "Add New Employee"}
      subtitle={isEditing ? `Updating ${employee.full_name} (${employee.employee_code})` : "Create an employee profile in the directory"}
      maxWidth="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <ErrorAlert message={error} onDismiss={() => setError("")} />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">First Name *</label>
            <input name="first_name" required value={form.first_name} onChange={handleChange} className="input-field" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Last Name *</label>
            <input name="last_name" required value={form.last_name} onChange={handleChange} className="input-field" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Work Email *</label>
            <input name="email" type="email" required value={form.email} onChange={handleChange} className="input-field" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Phone</label>
            <input name="phone" value={form.phone} onChange={handleChange} className="input-field" placeholder="+1-555-0100" />
          </div>
          {!isEditing && (
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Employee Code (optional)</label>
              <input name="employee_code" value={form.employee_code} onChange={handleChange} className="input-field" placeholder="Auto-generated if blank" />
            </div>
          )}
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Department</label>
            <select name="department_id" value={form.department_id} onChange={handleChange} className="input-field">
              <option value="">Unassigned</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name} ({dept.code})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Job Title *</label>
            <input name="job_title" required value={form.job_title} onChange={handleChange} className="input-field" placeholder="Software Engineer" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Base Salary (USD) *</label>
            <input name="base_salary" type="number" step="0.01" min="0" required value={form.base_salary} onChange={handleChange} className="input-field" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Employment Type</label>
            <select name="employment_type" value={form.employment_type} onChange={handleChange} className="input-field">
              <option value="full_time">Full Time</option>
              <option value="part_time">Part Time</option>
              <option value="contract">Contract</option>
              <option value="intern">Intern</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Status</label>
            <select name="status" value={form.status} onChange={handleChange} className="input-field">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="terminated">Terminated</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Hire Date *</label>
            <input name="hire_date" type="date" required value={form.hire_date} onChange={handleChange} className="input-field" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Emergency Contact</label>
            <input name="emergency_contact" value={form.emergency_contact} onChange={handleChange} className="input-field" />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold text-slate-700">Address</label>
          <input name="address" value={form.address} onChange={handleChange} className="input-field" />
        </div>

        {!isEditing && (
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
            <label className="flex items-center gap-2.5 text-sm font-medium text-slate-800">
              <input
                type="checkbox"
                name="create_user_account"
                checked={form.create_user_account}
                onChange={handleChange}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              Provision login account for this employee
            </label>
            {form.create_user_account && (
              <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">Initial Password *</label>
                  <input
                    name="account_password"
                    type="password"
                    minLength={8}
                    required
                    value={form.account_password}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="Minimum 8 characters"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">Account Role</label>
                  <select name="account_role" value={form.account_role} onChange={handleChange} className="input-field">
                    <option value="employee">Employee</option>
                    <option value="hr_manager">HR Manager</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Saving..." : isEditing ? "Save Changes" : "Create Employee"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
