import { useEffect, useState } from 'react'
import type { Zone } from '@/api/types'
import { cameraService } from '@/services/camera.service'

// The zones of every camera on the wall, kept in one place: a tile asks for its camera's zones, a wall of 9 tiles does 9
// requests once and then one per camera every REFRESH_MS, and a save in the camera window updates every tile at once.
const REFRESH_MS = 30_000
const cache = new Map<number, Zone[]>()
const listeners = new Map<number, Set<(zones: Zone[]) => void>>()

export function publishZones(cameraId: number, zones: Zone[]) {
  cache.set(cameraId, zones)
  listeners.get(cameraId)?.forEach((fn) => fn(zones))
}

export function useCameraZones(cameraId: number): Zone[] {
  const [zones, setZones] = useState<Zone[]>(() => cache.get(cameraId) ?? [])

  useEffect(() => {
    let alive = true
    const set = listeners.get(cameraId) ?? new Set()
    listeners.set(cameraId, set)
    set.add(setZones)
    const load = () =>
      cameraService
        .zones(cameraId)
        .then((z) => alive && publishZones(cameraId, z))
        .catch(() => {})
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => {
      alive = false
      clearInterval(timer)
      set.delete(setZones)
    }
  }, [cameraId])

  return zones
}

const asPoints = (polygon: Zone['polygon']) => polygon.map(([x, y]) => `${x},${y}`).join(' ')

// The switched-on zones of a camera over its picture. Never takes a click: the tile underneath stays clickable.
export default function ZoneOverlay({ cameraId, labels = false }: { cameraId: number; labels?: boolean }) {
  const zones = useCameraZones(cameraId).filter((z) => z.enabled)
  if (zones.length === 0) return null
  return (
    <div className="pointer-events-none absolute inset-0">
      <svg className="absolute inset-0 size-full" viewBox="0 0 1 1" preserveAspectRatio="none">
        {zones.map((z, i) => (
          <polygon
            key={z.id ?? i}
            points={asPoints(z.polygon)}
            fill="rgba(244,63,94,0.16)"
            stroke="#f43f5e"
            strokeWidth={0.006}
            strokeDasharray="0.015 0.01"
          />
        ))}
      </svg>
      {labels &&
        zones.map((z, i) => {
          const cx = z.polygon.reduce((s, p) => s + p[0], 0) / z.polygon.length
          const cy = z.polygon.reduce((s, p) => s + p[1], 0) / z.polygon.length
          return (
            <span
              key={`l-${z.id ?? i}`}
              className="absolute -translate-x-1/2 -translate-y-1/2 rounded bg-rose-600/80 px-1.5 py-0.5 text-[10px] font-bold text-white"
              style={{ left: `${cx * 100}%`, top: `${cy * 100}%` }}
            >
              {z.name}
            </span>
          )
        })}
    </div>
  )
}
