import { tokenStore } from '@/api/client'

// The token goes in the Authorization header, never in the URL. An <img> or <a> cannot send a header, so media is
// fetched here and shown from a blob URL.
const cache = new Map<string, Promise<string>>() // url -> blob URL; a violation snapshot never changes

async function fetchBlob(url: string): Promise<Blob> {
  const token = tokenStore.get()
  const response = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!response.ok) throw new Error(String(response.status))
  return response.blob()
}

export function authBlobUrl(url: string): Promise<string> {
  let found = cache.get(url)
  if (!found) {
    found = fetchBlob(url).then((blob) => URL.createObjectURL(blob))
    found.catch(() => cache.delete(url))
    cache.set(url, found)
  }
  return found
}

export async function downloadWithAuth(url: string, filename: string): Promise<void> {
  const href = URL.createObjectURL(await fetchBlob(url))
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(href), 10_000)
}

export const snapshotUrl = (eventId: number) => `/api/snapshots/${eventId}`

export function downloadBlob(blob: Blob, filename: string): void {
  const href = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(href), 10_000)
}
