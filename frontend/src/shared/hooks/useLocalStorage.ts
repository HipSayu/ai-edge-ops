// src/shared/hooks/useLocalStorage.ts
import { useState } from 'react';

/**
 * Simple wrapper around localStorage that mirrors React state APIs.
 * Stores a JSON-serialisable value under the given key.
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const readValue = () => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`useLocalStorage: error reading key "${key}"`, error);
      return initialValue;
    }
  };

  const [storedValue, setStoredValue] = useState<T>(readValue);

  const setValue = (value: T) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.warn(`useLocalStorage: error setting key "${key}"`, error);
    }
  };

  return [storedValue, setValue];
}

