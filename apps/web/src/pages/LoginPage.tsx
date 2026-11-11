import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react'
import { Button, ErrorText, Input } from '@/components/ui'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username.trim(), password)
      navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign in failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative flex min-h-full items-center justify-center p-4 bg-bg overflow-hidden select-none">
      <div className="relative w-full max-w-sm">
        <form
          onSubmit={submit}
          className="relative space-y-4 rounded-xl border border-line bg-panel p-6 shadow-xl"
        >
          {/* Header Branding */}
          <div className="text-center">
            <div className="mx-auto mb-3 grid size-12 place-items-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <ShieldCheck size={26} className="stroke-[2.2]" />
            </div>
            <h1 className="brand text-lg font-bold tracking-tight text-ink uppercase">PPE Vision VMS</h1>
            <p className="mt-0.5 text-xs text-dim">
              AI-Powered Occupational Safety Monitoring System
            </p>
          </div>

          <div className="space-y-3 pt-1">
            <Input
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin"
              autoFocus
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <ErrorText message={error} />

          <Button
            type="submit"
            variant="primary"
            size="md"
            className="w-full gap-1.5 h-8.5 font-semibold"
            disabled={busy}
          >
            <span>{busy ? 'Authenticating...' : 'Sign In'}</span>
            {!busy && <ArrowRight size={14} />}
          </Button>

          <div className="flex items-center justify-center gap-1 text-[10px] text-dim pt-1">
            <CheckCircle2 size={11} className="text-emerald-500" />
            <span>Secure Enterprise Edge Encryption</span>
          </div>
        </form>
      </div>
    </div>
  )
}
