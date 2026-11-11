import { tokenStore } from '@/api/client'
import type { FromWorker, ToWorker } from './liveWallWorker'

// The wall's one shared connection: every camera tile registers its canvas here instead of opening its own fetch.
// setCluster() (called once from the page, whenever the cluster filter or the pinned/opened camera changes) tells the
// worker which GET /api/cameras/live?cluster_id=&pin= to open; the worker demultiplexes the frames by camera id and
// draws straight onto each tile's own OffscreenCanvas.

let worker: Worker | null = null
const failHandlers = new Set<() => void>()
const snapshotWaiters = new Map<number, (blob: Blob | null) => void>()
let openKey = '' // clusterId:pin, so an unchanged call does not reopen the connection
let nextRequestId = 1

function ensureWorker(): Worker {
  if (!worker) {
    worker = new Worker(new URL('./liveWallWorker.ts', import.meta.url), { type: 'module' })
    worker.onmessage = (event: MessageEvent<FromWorker>) => {
      if (event.data.type === 'failed-all') {
        failHandlers.forEach((fn) => fn())
      } else if (event.data.type === 'snapshot-ready') {
        snapshotWaiters.get(event.data.requestId)?.(event.data.blob)
        snapshotWaiters.delete(event.data.requestId)
      }
    }
  }
  return worker
}

function send(message: ToWorker, transfer: Transferable[] = []) {
  ensureWorker().postMessage(message, transfer)
}

export function setCluster(clusterId: number | null, pin: number | null = null) {
  const key = `${clusterId}:${pin}`
  if (key === openKey) return
  openKey = key
  send({ type: 'open', clusterId, pin, token: tokenStore.get() ?? null })
}

export function registerTile(cameraId: number, canvas: OffscreenCanvas, width: number, height: number, ratio: number) {
  send({ type: 'register', cameraId, canvas, width, height, ratio }, [canvas])
}

export function unregisterTile(cameraId: number) {
  send({ type: 'unregister', cameraId })
}

export function resizeTile(cameraId: number, width: number, height: number, ratio: number) {
  send({ type: 'size', cameraId, width, height, ratio })
}

export function onWallFailed(fn: () => void): () => void {
  failHandlers.add(fn)
  return () => failHandlers.delete(fn)
}

// Freezes a tile on its last frame (new ones keep arriving and replace it; resuming shows the current moment at once,
// not a backlog). There is no server-side pause: this is a live feed, not a seekable recording.
export function setPaused(cameraId: number, paused: boolean) {
  send({ type: 'pause', cameraId, paused })
}

// The tile's current picture as a PNG, or null if the tile is gone or has nothing drawn yet.
export function snapshotTile(cameraId: number): Promise<Blob | null> {
  const requestId = nextRequestId++
  return new Promise((resolve) => {
    snapshotWaiters.set(requestId, resolve)
    send({ type: 'snapshot', cameraId, requestId })
  })
}
