import type { InputHTMLAttributes } from 'react'
import { FIELD_CLASS } from '@/components/ui/fieldStyle'

export default function Input({ label, className = '', ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <label className="block text-sm">
      {label && <span className="mb-1 block text-xs font-medium text-dim">{label}</span>}
      <input {...props} className={`${FIELD_CLASS} ${className}`} />
    </label>
  )
}
