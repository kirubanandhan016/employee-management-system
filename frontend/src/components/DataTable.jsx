import LoadingSpinner from "./LoadingSpinner";
import Pagination from "./Pagination";

export default function DataTable({
  columns,
  rows,
  loading = false,
  emptyTitle = "No records found",
  emptyDescription = "Try adjusting your search or filter criteria.",
  page = 1,
  totalPages = 1,
  total = 0,
  pageSize = 10,
  onPageChange,
}) {
  if (loading) {
    return (
      <div className="card">
        <LoadingSpinner label="Fetching records..." />
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50/80">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-slate-500 ${col.headerClassName || ""}`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-5 py-12 text-center">
                  <p className="text-sm font-semibold text-slate-700">{emptyTitle}</p>
                  <p className="mt-1 text-xs text-slate-500">{emptyDescription}</p>
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr key={row.id ?? idx} className="transition hover:bg-brand-50/30">
                  {columns.map((col) => (
                    <td key={col.key} className={`whitespace-nowrap px-5 py-3.5 text-slate-700 ${col.cellClassName || ""}`}>
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {onPageChange && (
        <Pagination
          page={page}
          totalPages={totalPages}
          total={total}
          pageSize={pageSize}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
