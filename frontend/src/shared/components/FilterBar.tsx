import React from 'react'
import { Search } from 'lucide-react'

interface FilterBarProps {
  searchQuery: string
  onSearchChange: (val: string) => void
  searchPlaceholder?: string
  children?: React.ReactNode
  actions?: React.ReactNode
}

export default function FilterBar({
  searchQuery,
  onSearchChange,
  searchPlaceholder = 'Search...',
  children,
  actions
}: FilterBarProps) {
  return (
    <section className="av-panel" style={{ marginBottom: 0 }}>
      <div className="av-filter-row" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300, alignItems: 'center' }}>
          <div className="av-search-box" style={{ flex: 1, height: '36px' }}>
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              style={{ width: '100%', height: '100%', background: 'transparent', border: 'none', color: 'var(--text)', outline: 'none', paddingLeft: 8 }}
            />
          </div>
          {children}
        </div>
        {actions && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {actions}
          </div>
        )}
      </div>
    </section>
  )
}

