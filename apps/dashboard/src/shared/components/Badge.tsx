import React from 'react'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'healthy' | 'warning' | 'critical' | 'info' | 'neutral' | 'brand'
  size?: 'sm' | 'md'
  dot?: boolean
}

const VARIANT_MAP: Record<NonNullable<BadgeProps['variant']>, { container: string; dotColor: string }> = {
  healthy: {
    container: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    dotColor: 'bg-emerald-500',
  },
  warning: {
    container: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    dotColor: 'bg-amber-500',
  },
  critical: {
    container: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
    dotColor: 'bg-rose-500',
  },
  info: {
    container: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20',
    dotColor: 'bg-sky-500',
  },
  neutral: {
    container: 'bg-muted text-muted-foreground border-border',
    dotColor: 'bg-muted-foreground',
  },
  brand: {
    container: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
    dotColor: 'bg-blue-500',
  },
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className = '',
  variant = 'neutral',
  size = 'sm',
  dot = false,
  ...props
}) => {
  const styles = VARIANT_MAP[variant] || VARIANT_MAP.neutral
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full border ${styles.container} ${sizeClasses} ${className}`}
      {...props}
    >
      {dot && <span className={`size-1.5 rounded-full ${styles.dotColor} animate-pulse`} />}
      {children}
    </span>
  )
}

export default Badge
