import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'ghost' | 'danger' | 'outline' | 'secondary'
type Size = 'sm' | 'md' | 'lg'

const VARIANT: Record<Variant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-500 active:bg-blue-700 border border-blue-500',
  secondary: 'bg-panel2 text-ink border border-line-strong hover:bg-line active:bg-panel',
  outline: 'border border-line-strong bg-transparent text-ink hover:bg-panel2 active:bg-panel',
  ghost: 'text-dim hover:text-ink hover:bg-panel2 active:bg-panel',
  danger: 'bg-rose-600 text-white hover:bg-rose-500 active:bg-rose-700 border border-rose-500',
}

const SIZES: Record<Size, string> = {
  sm: 'px-2 py-1 text-[11px] gap-1.5 rounded-sm uppercase tracking-wider',
  md: 'px-3 py-1.5 text-xs gap-1.5 rounded-sm font-medium uppercase tracking-wider',
  lg: 'px-4 py-2 text-sm gap-2 rounded-sm font-semibold uppercase tracking-wider',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: ReactNode
}

export default function Button({
  variant = 'outline',
  size = 'md',
  icon,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center font-medium select-none cursor-pointer disabled:pointer-events-none disabled:opacity-50 ${SIZES[size]} ${VARIANT[variant]} ${className}`}
    >
      {icon}
      {children}
    </button>
  )
}
