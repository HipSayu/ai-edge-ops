import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { authService } from '@/modules/auth/services/auth'

/** Sends signed-out users to /login, remembering where they were going. */
export default function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation()
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return children
}
