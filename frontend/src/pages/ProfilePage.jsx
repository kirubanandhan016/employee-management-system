import { useCallback, useEffect, useState } from "react";
import { KeyRound, Shield, UserCheck } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { employeeService } from "../services/employeeService";
import { authService } from "../services/authService";
import { extractErrorMessage } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";
import StatusBadge from "../components/StatusBadge";

export default function ProfilePage() {
  const { user, isAdmin, refreshProfile } = useAuth();
  const [employee, setEmployee] = useState(null);
  const [usersList, setUsersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [contactForm, setContactForm] = useState({ phone: "", address: "", emergency_contact: "" });
  const [passwordForm, setPasswordForm] = useState({ current_password: "", new_password: "" });
  const [savingContact, setSavingContact] = useState(false);
  const [savingPwd, setSavingPwd] = useState(false);

  const loadProfileData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      if (user?.employee_id) {
        const emp = await employeeService.getMe();
        setEmployee(emp);
        setContactForm({
          phone: emp.phone || "",
          address: emp.address || "",
          emergency_contact: emp.emergency_contact || "",
        });
      }
      if (isAdmin) {
        const usersRes = await authService.listUsers({ page: 1, page_size: 50 });
        setUsersList(usersRes.items || []);
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to load profile details"));
    } finally {
      setLoading(false);
    }
  }, [user?.employee_id, isAdmin]);

  useEffect(() => {
    loadProfileData();
  }, [loadProfileData]);

  const handleSaveContact = async (e) => {
    e.preventDefault();
    setSavingContact(true);
    setError("");
    setNotice("");
    try {
      const updated = await employeeService.updateMe({
        phone: contactForm.phone.trim() || null,
        address: contactForm.address.trim() || null,
        emergency_contact: contactForm.emergency_contact.trim() || null,
      });
      setEmployee(updated);
      setNotice("Personal contact details updated.");
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to update contact details"));
    } finally {
      setSavingContact(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setSavingPwd(true);
    setError("");
    setNotice("");
    try {
      await authService.changePassword(passwordForm);
      setPasswordForm({ current_password: "", new_password: "" });
      setNotice("Password updated successfully.");
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to change password"));
    } finally {
      setSavingPwd(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    setError("");
    try {
      await authService.updateUser(userId, { role: newRole });
      await loadProfileData();
      await refreshProfile();
      setNotice("User role updated.");
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to update user role"));
    }
  };

  if (loading) return <LoadingSpinner label="Loading your profile..." />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">My Profile & Account Security</h2>
        <p className="text-sm text-slate-500">Manage your personal details, password, and access preferences</p>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />
      {notice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white">
                <UserCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">{user?.full_name}</h3>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
            </div>
            <StatusBadge value={user?.role} />
          </div>

          {employee ? (
            <form onSubmit={handleSaveContact} className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-3 text-xs">
                <div>
                  <span className="text-slate-500">Employee Code</span>
                  <p className="font-semibold text-slate-900">{employee.employee_code}</p>
                </div>
                <div>
                  <span className="text-slate-500">Department</span>
                  <p className="font-semibold text-slate-900">{employee.department_name || "Unassigned"}</p>
                </div>
                <div>
                  <span className="text-slate-500">Job Title</span>
                  <p className="font-semibold text-slate-900">{employee.job_title}</p>
                </div>
                <div>
                  <span className="text-slate-500">Hire Date</span>
                  <p className="font-semibold text-slate-900">{employee.hire_date}</p>
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Phone</label>
                <input
                  value={contactForm.phone}
                  onChange={(e) => setContactForm((p) => ({ ...p, phone: e.target.value }))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Address</label>
                <input
                  value={contactForm.address}
                  onChange={(e) => setContactForm((p) => ({ ...p, address: e.target.value }))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Emergency Contact</label>
                <input
                  value={contactForm.emergency_contact}
                  onChange={(e) => setContactForm((p) => ({ ...p, emergency_contact: e.target.value }))}
                  className="input-field"
                />
              </div>
              <button type="submit" disabled={savingContact} className="btn-primary">
                {savingContact ? "Saving..." : "Save Contact Info"}
              </button>
            </form>
          ) : (
            <p className="text-sm text-slate-500">
              No employee record is currently linked to this user account. Contact HR to link your employee profile.
            </p>
          )}
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4">
            <KeyRound className="h-5 w-5 text-brand-600" />
            <h3 className="text-base font-semibold text-slate-900">Change Password</h3>
          </div>
          <form onSubmit={handleChangePassword} className="mt-4 space-y-4">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Current Password</label>
              <input
                type="password"
                required
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, current_password: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">New Password (min 8 chars)</label>
              <input
                type="password"
                required
                minLength={8}
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, new_password: e.target.value }))}
                className="input-field"
              />
            </div>
            <button type="submit" disabled={savingPwd} className="btn-primary">
              {savingPwd ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>
      </div>

      {isAdmin && (
        <div className="card p-6">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4">
            <Shield className="h-5 w-5 text-brand-600" />
            <div>
              <h3 className="text-base font-semibold text-slate-900">User Role Administration</h3>
              <p className="text-xs text-slate-500">Assign Admin, HR Manager, or Employee permissions</p>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead>
                <tr className="text-xs font-semibold uppercase text-slate-500">
                  <th className="py-2.5 pr-4">User</th>
                  <th className="py-2.5 pr-4">Email</th>
                  <th className="py-2.5 pr-4">Status</th>
                  <th className="py-2.5">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usersList.map((u) => (
                  <tr key={u.id}>
                    <td className="py-3 pr-4 font-medium text-slate-900">{u.full_name}</td>
                    <td className="py-3 pr-4 text-slate-600">{u.email}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge value={u.is_active ? "active" : "inactive"} />
                    </td>
                    <td className="py-3">
                      <select
                        value={u.role}
                        disabled={u.id === user?.id}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        className="input-field max-w-[160px] py-1.5 text-xs"
                      >
                        <option value="admin">Admin</option>
                        <option value="hr_manager">HR Manager</option>
                        <option value="employee">Employee</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
