import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '@/shared/api/client'
import { authService } from '@/shared/api/services/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await authService.login({ email, password })
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(destination && destination !== '/login' ? destination : '/', { replace: true })
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Unable to sign in. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="av-login-page">
      <section className="av-login-panel" aria-labelledby="login-title">
        <div className="av-login-mark">AI EDGE OPS</div>
        <p className="av-eyebrow">CONTROL PLANE</p>
        <h1 id="login-title">Sign in</h1>
        <p className="av-login-subtitle">Access your edge fleet and live telemetry.</p>

        <form className="av-login-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              autoComplete="email"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label>
            Password
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {error && <p className="av-login-error" role="alert">{error}</p>}
          <button className="av-login-submit" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
