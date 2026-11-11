import type { SelectHTMLAttributes } from 'react'
import { FIELD_CLASS } from '@/components/ui/fieldStyle'

export default function Select({ label, children, className = '', ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <label className="block text-sm">
      {label && <span className="mb-1 block text-xs font-medium text-dim">{label}</span>}
      <select {...props} className={`${FIELD_CLASS} ${className}`}>
        {children}
      </select>
    </label>
  )
}
