import React, { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'brand'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const VARIANT_MAP: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-foreground text-background hover:opacity-90 active:scale-[0.98]',
  brand: 'bg-brand text-brand-foreground shadow-sm shadow-brand/20 hover:opacity-90 active:scale-[0.98]',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 active:scale-[0.98]',
  outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground active:scale-[0.98]',
  ghost: 'hover:bg-accent hover:text-accent-foreground active:scale-[0.98]',
  destructive: 'bg-destructive text-destructive-foreground hover:opacity-90 active:scale-[0.98]',
}

const SIZE_MAP: Record<NonNullable<ButtonProps['size']>, string> = {
  xs: 'px-2 py-1 text-xs gap-1 rounded-md',
  sm: 'px-3 py-1.5 text-xs gap-1.5 rounded-lg',
  md: 'px-4 py-2 text-sm gap-2 rounded-xl',
  lg: 'px-5 py-2.5 text-base gap-2.5 rounded-xl',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = '',
      variant = 'secondary',
      size = 'sm',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:pointer-events-none disabled:transform-none cursor-pointer select-none ${
          VARIANT_MAP[variant]
        } ${SIZE_MAP[size]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children && <span>{children}</span>}
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
