import { Loader2 } from 'lucide-react'

interface LoadingProps {
  label?: string
  size?: 'sm' | 'md' | 'lg'
  fullScreen?: boolean
  className?: string
}

export default function Loading({
  label = 'Loading...',
  size = 'md',
  fullScreen = false,
  className = '',
}: LoadingProps) {
  const sizeMap = {
    sm: 'size-4',
    md: 'size-6',
    lg: 'size-8',
  }

  const content = (
    <div className={`flex flex-col items-center justify-center gap-2 text-dim ${className}`}>
      <Loader2 className={`animate-spin text-blue-500 ${sizeMap[size]}`} />
      {label && <span className="font-mono text-xs">{label}</span>}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs">
        {content}
      </div>
    )
  }

  return content
}

