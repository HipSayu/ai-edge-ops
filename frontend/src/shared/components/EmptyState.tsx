import React from 'react'
import { AlertCircle } from 'lucide-react'

interface EmptyStateProps {
  message?: string
  icon?: React.ReactNode
}

export default function EmptyState({ message = 'No data available.', icon }: EmptyStateProps) {
  return (
    <div style={{ 
      gridColumn: '1 / -1', 
      textAlign: 'center', 
      padding: '48px 24px', 
      color: 'var(--text-faint)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 12,
      background: 'var(--panel-2)',
      borderRadius: 'var(--radius-lg)',
      border: '1px dashed var(--border-strong)'
    }}>
      {icon || <AlertCircle size={32} opacity={0.5} />}
      <span style={{ fontSize: 14, fontWeight: 500 }}>{message}</span>
    </div>
  )
}

