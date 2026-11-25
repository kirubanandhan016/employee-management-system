const STYLE_MAP = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  present: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  paid: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",

  pending: "bg-amber-50 text-amber-700 ring-amber-600/20",
  late: "bg-amber-50 text-amber-700 ring-amber-600/20",
  half_day: "bg-sky-50 text-sky-700 ring-sky-600/20",
  on_leave: "bg-indigo-50 text-indigo-700 ring-indigo-600/20",

  inactive: "bg-slate-100 text-slate-600 ring-slate-500/20",
  cancelled: "bg-slate-100 text-slate-600 ring-slate-500/20",

  terminated: "bg-rose-50 text-rose-700 ring-rose-600/20",
  rejected: "bg-rose-50 text-rose-700 ring-rose-600/20",
  absent: "bg-rose-50 text-rose-700 ring-rose-600/20",

  admin: "bg-brand-50 text-brand-700 ring-brand-600/20",
  hr_manager: "bg-sky-50 text-sky-700 ring-sky-600/20",
  employee: "bg-slate-100 text-slate-700 ring-slate-500/20",
};

export default function StatusBadge({ value }) {
  const normalized = String(value || "").toLowerCase();
  const classes = STYLE_MAP[normalized] || "bg-slate-100 text-slate-700 ring-slate-500/20";
  const label = normalized.replace(/_/g, " ");

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ring-inset ${classes}`}
    >
      {label}
    </span>
  );
}
