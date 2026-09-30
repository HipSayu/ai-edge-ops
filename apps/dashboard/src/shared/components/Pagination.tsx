import { ChevronLeft, ChevronRight } from 'lucide-react'

export interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems?: number
  pageSize?: number
  pageSizeOptions?: number[]
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  className?: string
}

export default function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize = 10,
  pageSizeOptions = [10, 20, 50, 100],
  onPageChange,
  onPageSizeChange,
  className = '',
}: PaginationProps) {
  if (totalPages <= 1 && (!totalItems || totalItems <= pageSize)) {
    return null
  }

  // Calculate start and end item index
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = totalItems ? Math.min(currentPage * pageSize, totalItems) : currentPage * pageSize

  // Generate page numbers with ellipsis
  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = []
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push('ellipsis')
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      for (let i = start; i <= end; i++) pages.push(i)
      if (currentPage < totalPages - 2) pages.push('ellipsis')
      pages.push(totalPages)
    }
    return pages
  }

  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-3 text-xs text-muted-foreground ${className}`}>
      {/* Left: Item range count */}
      <div className="flex items-center gap-2">
        {totalItems !== undefined && (
          <span>
            Showing <strong className="text-foreground">{startItem}-{endItem}</strong> of <strong className="text-foreground">{totalItems}</strong> items
          </span>
        )}
        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 ml-2 border-l border-border/60 pl-3">
            <span className="text-[11px]">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="h-6.5 rounded border border-border bg-card px-1.5 text-xs text-foreground outline-none font-mono"
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right: Page navigation buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="flex size-7 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-40 disabled:pointer-events-none"
          title="Previous page"
        >
          <ChevronLeft size={14} />
        </button>

        {getPageNumbers().map((p, idx) =>
          p === 'ellipsis' ? (
            <span key={`ellipsis-${idx}`} className="px-1.5 text-muted-foreground select-none">
              …
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`flex size-7 items-center justify-center rounded-md text-xs font-semibold transition-all ${
                currentPage === p
                  ? 'bg-brand text-white'
                  : 'border border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="flex size-7 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-40 disabled:pointer-events-none"
          title="Next page"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}
