import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { storage } from '@/helpers/storage'

interface ThemeState {
  dark: boolean
  toggle: () => void
}

const ThemeContext = createContext<ThemeState | null>(null)

export function applyTheme(dark: boolean) {
  const root = document.documentElement
  root.classList.toggle('dark', dark)
  root.dataset.theme = dark ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(() => storage.get('ppe_theme') !== 'light')
  applyTheme(dark)

  const toggle = useCallback(() => {
    setDark((prev) => {
      storage.set('ppe_theme', prev ? 'light' : 'dark')
      return !prev
    })
  }, [])

  const value = useMemo(() => ({ dark, toggle }), [dark, toggle])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
