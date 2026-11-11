import { useCallback, useState } from 'react'
import { storage } from '@/helpers/storage'

export function useLocalStorageFlag(key: string, fallback: boolean): [boolean, (next: boolean) => void] {
  const [value, setValue] = useState(() => {
    const saved = storage.get(key)
    return saved === null ? fallback : saved === '1'
  })
  const set = useCallback(
    (next: boolean) => {
      setValue(next)
      storage.set(key, next ? '1' : '0')
    },
    [key],
  )
  return [value, set]
}
