import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export default function RequireAuth({ children, operatorOnly = false }: { children: ReactNode; operatorOnly?: boolean }) {
  const { user, loading, canOperate } = useAuth()
  if (loading) return <div className="grid h-full place-items-center text-sm text-dim">Đang tải…</div>
  if (!user) return <Navigate to="/login" replace />
  if (operatorOnly && !canOperate) return <Navigate to="/" replace />
  return <>{children}</>
}
