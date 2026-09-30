import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  Eye, 
  EyeOff, 
  Lock, 
  Mail, 
  User, 
  Sparkles, 
  Cpu, 
  ArrowRight
} from 'lucide-react'
import { ApiError } from '@/shared/api/client'
import { authService } from '@/modules/auth/services/auth'

type Mode = 'login' | 'register'

function errorMessage(cause: unknown, mode: Mode): string {
  if (!(cause instanceof ApiError)) return 'Unable to reach the server. Please try again.'
  if (mode === 'login' && cause.status === 401) return 'Wrong email/username or password.'
  if (cause.status === 403) return 'Registration is closed. Ask an admin to create your account.'
  if (cause.status === 409) return 'That username or email is already registered.'
  if (cause.status === 422) return 'Check the fields: username 3+ characters (letters, digits, . _ -), a valid email, password 8+ characters.'
  return cause.message
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState<Mode>('login')
  const [login, setLogin] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      if (mode === 'login') {
        await authService.login({ login: login.trim(), password })
      } else {
        await authService.register({
          username: username.trim(),
          email: email.trim(),
          password,
          displayName: displayName.trim() || undefined,
        })
      }
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(destination && destination !== '/login' ? destination : '/', { replace: true })
    } catch (cause) {
      setError(errorMessage(cause, mode))
    } finally {
      setIsSubmitting(false)
    }
  }

  function switchMode(next: Mode) {
    setMode(next)
    setError('')
  }

  const isLogin = mode === 'login'

  return (
    <main className="min-h-screen w-full flex bg-background text-foreground overflow-hidden">
      {/* Left side: Visual & Branding Section */}
      <section className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-gradient-to-br from-slate-900 via-slate-950 to-zinc-950 text-white relative overflow-hidden border-r border-border/20">
        {/* Glowing background grid effects */}
        <div className="absolute inset-0 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:24px_24px] opacity-15" />
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="font-extrabold tracking-wider text-base bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              AI EDGE OPS
            </div>
            <div className="text-[10px] font-mono tracking-widest text-blue-400 font-semibold">
              Control Plane v2.4
            </div>
          </div>
        </div>

        {/* Main Hero Banner */}
        <div className="relative z-10 max-w-lg my-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Edge Intelligence</span>
          </div>

          <h1 className="text-4xl xl:text-5xl font-extrabold tracking-tight leading-tight text-slate-50">
            Real-time Telemetry & Edge Fleet Command.
          </h1>

          <p className="text-slate-400 text-base leading-relaxed">
            Monitor zero-latency computer vision pipelines, deploy ultra-light ML models, and orchestrate smart edge devices across global operational zones.
          </p>

          {/* Feature Highlights Grid */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <div className="text-xs font-bold text-slate-200">Sub-10ms Latency</div>
              <div className="text-[11px] text-slate-400">Live camera stream HUD</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <div className="text-xs font-bold text-slate-200">Enterprise Security</div>
              <div className="text-[11px] text-slate-400">Encrypted JWT & RBAC</div>
            </div>
          </div>
        </div>

        {/* Footer Status Bar */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-6">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono">All Systems Operational</span>
          </div>
          <span>&copy; {new Date().getFullYear()} AI Edge Ops</span>
        </div>
      </section>

      {/* Right side: Login / Register Form */}
      <section className="flex-1 flex flex-col justify-between p-6 sm:p-12 lg:p-16 bg-background relative overflow-y-auto">
        <div className="max-w-md w-full mx-auto my-auto space-y-8">
          {/* Mobile Header Logo */}
          <div className="flex lg:hidden items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold tracking-wider text-slate-900 dark:text-white">AI Edge Ops</span>
          </div>

          {/* Form Header */}
          <div className="space-y-2">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
              {isLogin ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="text-sm text-muted-foreground">
              {isLogin
                ? 'Sign in to access your dashboard & edge camera matrix.'
                : 'The first registered account will automatically gain Admin privileges.'}
            </p>
          </div>

          {/* Error Message Box */}
          {error && (
            <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-200" role="alert">
              <div className="w-2 h-2 rounded-full bg-destructive mt-1.5 shrink-0" />
              <div className="flex-1 font-medium">{error}</div>
            </div>
          )}

          {/* Authentication Form */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            {isLogin ? (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground tracking-wide flex items-center justify-between">
                  <span>Email or Username</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    autoComplete="username"
                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all placeholder:text-muted-foreground/60 text-foreground"
                    name="login"
                    onChange={(event) => setLogin(event.target.value)}
                    placeholder="name@company.com or username"
                    required
                    value={login}
                  />
                </div>
              </div>
            ) : (
              <>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground tracking-wide">
                    Username
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                      <User className="w-4 h-4" />
                    </div>
                    <input
                      autoComplete="username"
                      className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all placeholder:text-muted-foreground/60 text-foreground"
                      name="username"
                      minLength={3}
                      onChange={(event) => setUsername(event.target.value)}
                      pattern="[A-Za-z0-9_.\-]+"
                      placeholder="admin_dev"
                      required
                      value={username}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground tracking-wide">
                    Email address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      autoComplete="email"
                      className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all placeholder:text-muted-foreground/60 text-foreground"
                      name="email"
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="admin@edgeops.ai"
                      required
                      type="email"
                      value={email}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground tracking-wide">
                    Display Name <span className="text-muted-foreground font-normal">(Optional)</span>
                  </label>
                  <input
                    autoComplete="name"
                    className="w-full px-4 py-2.5 text-sm bg-card border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all placeholder:text-muted-foreground/60 text-foreground"
                    name="displayName"
                    onChange={(event) => setDisplayName(event.target.value)}
                    placeholder="Alex Morgan"
                    value={displayName}
                  />
                </div>
              </>
            )}

            {/* Password input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground tracking-wide flex items-center justify-between">
                <span>Password</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  className="w-full pl-10 pr-10 py-2.5 text-sm bg-card border border-input rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all placeholder:text-muted-foreground/60 text-foreground"
                  minLength={isLogin ? undefined : 8}
                  name="password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  required
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              className="w-full py-3 px-4 rounded-xl bg-brand text-brand-foreground font-bold text-sm hover:opacity-90 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none mt-2"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Switch Mode Footer */}
          <div className="pt-4 text-center border-t border-border/60">
            <p className="text-sm text-muted-foreground">
              {isLogin ? "Don't have an account?" : 'Already registered?'}
              {' '}
              <button
                type="button"
                className="font-semibold text-brand hover:underline focus:outline-none"
                onClick={() => switchMode(isLogin ? 'register' : 'login')}
              >
                {isLogin ? 'Create one now' : 'Sign in to account'}
              </button>
            </p>
          </div>
        </div>

        {/* Small footer text */}
        <div className="max-w-md w-full mx-auto text-center text-xs text-muted-foreground/60 pt-6">
          AI Edge Ops Platform • Protected by TLS Enterprise Encryption
        </div>
      </section>
    </main>
  )
}

