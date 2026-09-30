import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean
}

export const Card: React.FC<CardProps> = ({ children, className = '', glass = true, ...props }) => {
  return (
    <div
      className={`rounded-xl border border-border/80 bg-card p-4 transition-all duration-200 ${
        glass ? 'backdrop-blur-sm bg-card/90 shadow-sm hover:border-border hover:shadow-md' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => {
  return (
    <div className={`flex items-center justify-between pb-3 border-b border-border/60 ${className}`} {...props}>
      {children}
    </div>
  )
}

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ children, className = '', ...props }) => {
  return (
    <h3 className={`text-sm font-bold tracking-tight text-foreground flex items-center gap-2 ${className}`} {...props}>
      {children}
    </h3>
  )
}

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => {
  return (
    <div className={`pt-3 ${className}`} {...props}>
      {children}
    </div>
  )
}
