export default function LoadingSpinner({ label = "Loading...", fullScreen = false }) {
  const wrapperClass = fullScreen
    ? "flex min-h-screen flex-col items-center justify-center bg-slate-50 gap-3"
    : "flex flex-col items-center justify-center py-12 gap-3";

  return (
    <div className={wrapperClass} role="status" aria-live="polite">
      <div className="h-9 w-9 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      <p className="text-sm font-medium text-slate-500">{label}</p>
    </div>
  );
}
