import { useEffect, useRef } from 'react'
import { onWallFailed, registerTile, resizeTile, unregisterTile } from '@/overlay/liveWall'

// A wall can show a dozen tiles at once; a Retina/4K devicePixelRatio (2-3x) would make the worker paint 4-9x the
// pixels for no visible gain at tile size. Capped, not dropped: still sharp, just not wastefully so.
const MAX_RATIO = 1.5
const ratioOf = () => Math.min(window.devicePixelRatio || 1, MAX_RATIO)

// One tile's picture: registers its own canvas with the shared wall connection (see liveWall.ts) instead of opening a
// fetch of its own. The page calls liveWall.setCluster() once; every tile just shows whatever arrives for its camera.
export default function LiveCanvas({ cameraId, onFail }: { cameraId: number; onFail: () => void }) {
  const host = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = host.current
    if (!el) return
    const canvas = document.createElement('canvas')
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%'
    canvas.setAttribute('aria-label', 'Camera')
    el.appendChild(canvas)

    const offscreen = canvas.transferControlToOffscreen()
    registerTile(cameraId, offscreen, el.clientWidth, el.clientHeight, ratioOf())

    const observer = new ResizeObserver(() => resizeTile(cameraId, el.clientWidth, el.clientHeight, ratioOf()))
    observer.observe(el)
    const stopWatching = onWallFailed(onFail)

    return () => {
      observer.disconnect()
      stopWatching()
      unregisterTile(cameraId)
      canvas.remove()
    }
  }, [cameraId, onFail])

  return <div ref={host} className="absolute inset-0" />
}
