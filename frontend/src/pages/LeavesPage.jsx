import { useCallback, useEffect, useState } from "react";
import { Check, Plus, X, Ban } from "lucide-react";
import { leaveService } from "../services/leaveService";
import { extractErrorMessage } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import DataTable from "../components/DataTable";
import StatusBadge from "../components/StatusBadge";
import ErrorAlert from "../components/ErrorAlert";
import Modal from "../components/Modal";

export default function LeavesPage() {
  const { isPrivileged, user } = useAuth();
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, totalPages: 1, pageSize: 15 });

  const [applyOpen, setApplyOpen] = useState(false);
  const [applyForm, setApplyForm] = useState({
    leave_type: "annual",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: new Date().toISOString().slice(0, 10),
    reason: "",
  });

  const [reviewModal, setReviewModal] = useState({ open: false, leave: null, decision: "approved", comment: "" });
  const [saving, setSaving] = useState(false);

  const loadLeaves = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await leaveService.list({
        status: statusFilter || undefined,
        leave_type: typeFilter || undefined,
        page,
        page_size: meta.pageSize,
      });
      setLeaves(res.items || []);
      setMeta({ total: res.total, totalPages: res.total_pages, pageSize: res.page_size });
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to fetch leave requests"));
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, page, meta.pageSize]);

  useEffect(() => {
    loadLeaves();
  }, [loadLeaves]);

  const handleApplySubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await leaveService.apply(applyForm);
      setApplyOpen(false);
      setApplyForm({
        leave_type: "annual",
        start_date: new Date().toISOString().slice(0, 10),
        end_date: new Date().toISOString().slice(0, 10),
        reason: "",
      });
      await loadLeaves();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to submit leave request"));
    } finally {
      setSaving(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewModal.leave) return;
    setSaving(true);
    setError("");
    try {
      await leaveService.review(reviewModal.leave.id, {
        status: reviewModal.decision,
        review_comment: reviewModal.comment || null,
      });
      setReviewModal({ open: false, leave: null, decision: "approved", comment: "" });
      await loadLeaves();
    } catch (err) {
      setError(extractErrorMessage(err, "Review action failed"));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (leaveId) => {
    setError("");
    try {
      await leaveService.cancel(leaveId);
      await loadLeaves();
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to cancel leave request"));
    }
  };

  const columns = [
    {
      key: "employee",
      label: "Employee",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.employee_name || "—"}</p>
          <p className="text-xs text-slate-500">{row.department_name || row.employee_code}</p>
        </div>
      ),
    },
    {
      key: "leave_type",
      label: "Type",
      render: (row) => <span className="capitalize font-medium text-slate-800">{row.leave_type}</span>,
    },
    {
      key: "dates",
      label: "Period",
      render: (row) => (
        <div>
          <p className="text-slate-800">
            {row.start_date} → {row.end_date}
          </p>
          <p className="text-xs text-slate-500">
            {row.days_count} {row.days_count === 1 ? "day" : "days"}
          </p>
        </div>
      ),
    },
    {
      key: "reason",
      label: "Reason",
      cellClassName: "max-w-xs truncate",
      render: (row) => <span title={row.reason}>{row.reason}</span>,
    },
    {
      key: "status",
      label: "Status",
      render: (row) => (
        <div>
          <StatusBadge value={row.status} />
          {row.reviewer_name && (
            <p className="mt-1 text-[11px] text-slate-400">by {row.reviewer_name}</p>
          )}
        </div>
      ),
    },
    {
      key: "actions",
      label: "Actions",
      headerClassName: "text-right",
      cellClassName: "text-right",
      render: (row) => {
        if (row.status !== "pending") return <span className="text-xs text-slate-400">Closed</span>;
        return (
          <div className="inline-flex items-center justify-end gap-1.5">
            {isPrivileged && (
              <>
                <button
                  type="button"
                  onClick={() => setReviewModal({ open: true, leave: row, decision: "approved", comment: "" })}
                  className="rounded-lg bg-emerald-50 p-1.5 text-emerald-700 hover:bg-emerald-100"
                  title="Approve"
                >
                  <Check className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setReviewModal({ open: true, leave: row, decision: "rejected", comment: "" })}
                  className="rounded-lg bg-rose-50 p-1.5 text-rose-700 hover:bg-rose-100"
                  title="Reject"
                >
                  <X className="h-4 w-4" />
                </button>
              </>
            )}
            {(isPrivileged || row.employee_id === user?.employee_id) && (
              <button
                type="button"
                onClick={() => handleCancel(row.id)}
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                title="Cancel request"
              >
                <Ban className="h-4 w-4" />
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Leave Management</h2>
          <p className="text-sm text-slate-500">Submit time-off applications and track approval status</p>
        </div>
        {user?.employee_id && (
          <button type="button" onClick={() => setApplyOpen(true)} className="btn-primary">
            <Plus className="h-4 w-4" />
            Apply for Leave
          </button>
        )}
      </div>

      <ErrorAlert message={error} onDismiss={() => setError("")} />

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="input-field">
          <option value="">All Leave Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }} className="input-field">
          <option value="">All Leave Types</option>
          <option value="annual">Annual</option>
          <option value="sick">Sick</option>
          <option value="casual">Casual</option>
          <option value="unpaid">Unpaid</option>
          <option value="maternity">Maternity</option>
          <option value="paternity">Paternity</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={leaves}
        loading={loading}
        page={page}
        totalPages={meta.totalPages}
        total={meta.total}
        pageSize={meta.pageSize}
        onPageChange={setPage}
      />

      <Modal isOpen={applyOpen} onClose={() => setApplyOpen(false)} title="Apply for Leave">
        <form onSubmit={handleApplySubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Leave Type *</label>
            <select
              value={applyForm.leave_type}
              onChange={(e) => setApplyForm((p) => ({ ...p, leave_type: e.target.value }))}
              className="input-field"
            >
              <option value="annual">Annual Leave</option>
              <option value="sick">Sick Leave</option>
              <option value="casual">Casual Leave</option>
              <option value="unpaid">Unpaid Leave</option>
              <option value="maternity">Maternity Leave</option>
              <option value="paternity">Paternity Leave</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Start Date *</label>
              <input
                type="date"
                required
                value={applyForm.start_date}
                onChange={(e) => setApplyForm((p) => ({ ...p, start_date: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">End Date *</label>
              <input
                type="date"
                required
                value={applyForm.end_date}
                onChange={(e) => setApplyForm((p) => ({ ...p, end_date: e.target.value }))}
                className="input-field"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Reason *</label>
            <textarea
              required
              minLength={5}
              rows={3}
              value={applyForm.reason}
              onChange={(e) => setApplyForm((p) => ({ ...p, reason: e.target.value }))}
              className="input-field"
              placeholder="Briefly describe the reason for your leave..."
            />
          </div>
          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => setApplyOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Submitting..." : "Submit Request"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={reviewModal.open}
        onClose={() => setReviewModal({ open: false, leave: null, decision: "approved", comment: "" })}
        title={`${reviewModal.decision === "approved" ? "Approve" : "Reject"} Leave Request`}
      >
        <form onSubmit={handleReviewSubmit} className="space-y-4">
          <p className="text-sm text-slate-600">
            Reviewing <span className="font-semibold text-slate-900">{reviewModal.leave?.employee_name}</span>&apos;s{" "}
            <span className="capitalize">{reviewModal.leave?.leave_type}</span> leave from{" "}
            {reviewModal.leave?.start_date} to {reviewModal.leave?.end_date}.
          </p>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">Reviewer Comment (optional)</label>
            <textarea
              rows={3}
              value={reviewModal.comment}
              onChange={(e) => setReviewModal((p) => ({ ...p, comment: e.target.value }))}
              className="input-field"
              placeholder="Add an optional note for the employee..."
            />
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setReviewModal({ open: false, leave: null, decision: "approved", comment: "" })}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className={reviewModal.decision === "approved" ? "btn-primary" : "btn-danger"}
            >
              {saving ? "Submitting..." : reviewModal.decision === "approved" ? "Confirm Approval" : "Confirm Rejection"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
