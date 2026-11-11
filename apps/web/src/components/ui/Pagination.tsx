import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

interface PaginationProps {
  page: number
  totalItems: number
  pageSize: number
  onPageChange: (newPage: number) => void
  onPageSizeChange?: (newPageSize: number) => void
}

export default function Pagination({
  page,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const start = totalItems === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(totalItems, page * pageSize)

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line/80 px-4 py-2 text-xs text-dim">
      <div className="flex items-center gap-2">
        <span>
          Showing <strong className="text-ink font-mono">{start}-{end}</strong> of <strong className="text-ink font-mono">{totalItems}</strong> items
        </span>
        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 ml-2">
            <span>/ page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="rounded border border-line bg-panel2/60 px-2 py-0.5 text-xs text-ink outline-none focus:border-brand cursor-pointer"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(1)}
          disabled={page <= 1}
          title="First Page"
          className="rounded p-1 text-dim transition-colors hover:bg-panel2 hover:text-ink disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
        >
          <ChevronsLeft size={14} />
        </button>
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          title="Previous Page"
          className="rounded p-1 text-dim transition-colors hover:bg-panel2 hover:text-ink disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
        >
          <ChevronLeft size={14} />
        </button>

        <span className="px-2 font-mono font-medium text-ink">
          {page} / {totalPages}
        </span>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          title="Next Page"
          className="rounded p-1 text-dim transition-colors hover:bg-panel2 hover:text-ink disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
        >
          <ChevronRight size={14} />
        </button>
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={page >= totalPages}
          title="Last Page"
          className="rounded p-1 text-dim transition-colors hover:bg-panel2 hover:text-ink disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
        >
          <ChevronsRight size={14} />
        </button>
      </div>
    </div>
  )
}
