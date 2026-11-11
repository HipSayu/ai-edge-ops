/// <reference lib="webworker" />
// One worker for the whole wall: a single fetch to GET /api/cameras/live?cluster_id=&pin= carries the frames of every
// camera the page shows, each packet tagged with its camera id. Tiles register their own OffscreenCanvas here; the
// worker draws each incoming frame straight onto the canvas of its camera, or drops it if no tile wants it right now.
import { drawBoxes, type OverlayBox } from './drawBoxes'

interface Header {
  id: number
  age: number
  edge: { fps: number; ms: number; drop: number }
  w: number
  h: number
  boxes: { l: string; c: number; b: [number, number, number, number]; t: number | null }[]
}

interface Shown {
  bitmap: ImageBitmap
  frame: { w: number; h: number }
  boxes: OverlayBox[]
  age: number
  arrivedAt: number
  edge: Header['edge']
}

interface Tile {
  canvas: OffscreenCanvas
  ctx: OffscreenCanvasRenderingContext2D
  width: number
  height: number
  ratio: number
  shown: Shown | null
  drawing: number
  paused: boolean // frozen on the last frame it had; new ones still arrive and replace it, just are not painted
}

export type ToWorker =
  | { type: 'open'; clusterId: number | null; pin: number | null; token: string | null }
  | { type: 'register'; cameraId: number; canvas: OffscreenCanvas; width: number; height: number; ratio: number }
  | { type: 'unregister'; cameraId: number }
  | { type: 'size'; cameraId: number; width: number; height: number; ratio: number }
  | { type: 'pause'; cameraId: number; paused: boolean }
  | { type: 'snapshot'; cameraId: number; requestId: number }
  | { type: 'close' }
export type FromWorker =
  | { type: 'failed-all' } // the one shared connection gave up; every registered tile is affected
  | { type: 'snapshot-ready'; requestId: number; blob: Blob | null }

const RETRY_MS = 2000
const GIVE_UP_AFTER = 3 // failed connections in a row

const tiles = new Map<number, Tile>()
let generation = 0 // bumped on every open/close, so a stale read() loop from a previous connection stops touching state
const abort = { current: new AbortController() }

function paint(cameraId: number) {
  const tile = tiles.get(cameraId)
  if (!tile) return
  tile.drawing = 0
  const { width, height, ratio, shown, ctx, canvas } = tile
  if (!width || !height || !shown) return
  const pixelW = Math.round(width * ratio)
  const pixelH = Math.round(height * ratio)
  if (canvas.width !== pixelW || canvas.height !== pixelH) {
    canvas.width = pixelW
    canvas.height = pixelH
  }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
  ctx.clearRect(0, 0, width, height)
  // object-fit: cover
  const { bitmap } = shown
  const scale = Math.max(width / bitmap.width, height / bitmap.height)
  const w = bitmap.width * scale
  const h = bitmap.height * scale
  ctx.drawImage(bitmap, (width - w) / 2, (height - h) / 2, w, h)
  drawBoxes(ctx, width, height, shown.frame.w ? shown.frame : { w: bitmap.width, h: bitmap.height }, shown.boxes)
  // a small readout: the speed the edge reports, and the delay of what is on screen (time in the cloud + time since
  // the frame reached the page)
  const lag = Math.round(shown.age + performance.now() - shown.arrivedAt)
  const text = `EDGE ${shown.edge.fps} FPS · ${Math.round(shown.edge.ms)} MS · LAG ${lag} MS`
  ctx.font = '600 10px "IBM Plex Mono", ui-monospace, monospace'
  ctx.textBaseline = 'top'
  const textWidth = ctx.measureText(text).width
  ctx.fillStyle = 'rgba(0,0,0,0.55)'
  ctx.fillRect(width - textWidth - 14, height - 20, textWidth + 10, 16)
  ctx.fillStyle = '#9fb3c8'
  ctx.fillText(text, width - textWidth - 9, height - 18)
}

function schedule(cameraId: number) {
  const tile = tiles.get(cameraId)
  if (tile && !tile.drawing) tile.drawing = requestAnimationFrame(() => paint(cameraId))
}

async function applyPacket(head: Header, jpeg: Uint8Array, arrived: number) {
  const tile = tiles.get(head.id)
  if (!tile) return // no tile wants this camera right now
  try {
    const bitmap = await createImageBitmap(new Blob([jpeg as BlobPart], { type: 'image/jpeg' }))
    const current = tiles.get(head.id) // the tile may have gone (unregistered) while decoding
    if (!current) {
      bitmap.close()
      return
    }
    current.shown?.bitmap.close()
    current.shown = {
      bitmap,
      frame: { w: head.w, h: head.h },
      boxes: head.boxes.map((b) => ({ label: b.l, confidence: b.c, box: b.b, trackId: b.t })),
      age: head.age,
      arrivedAt: arrived,
      edge: head.edge,
    }
    if (!current.paused) schedule(head.id) // paused: still kept as `shown`, so unpausing shows the current moment at once
  } catch {
    // a damaged frame is skipped
  }
}

// The frames come as packets: two big-endian uint32 lengths, a JSON header (carrying the camera id), the JPEG.
async function read(url: string, token: string | null, myGeneration: number) {
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    signal: abort.current.signal,
  })
  if (!response.ok || !response.body) throw new Error(String(response.status))
  const reader = response.body.getReader()
  let chunks: Uint8Array[] = []
  let have = 0
  let need = 0
  let headLength = 0
  const take = (count: number): Uint8Array => {
    const out = new Uint8Array(count)
    let at = 0
    while (at < count) {
      const first = chunks[0]
      const n = Math.min(first.length, count - at)
      out.set(first.subarray(0, n), at)
      at += n
      if (n === first.length) chunks.shift()
      else chunks[0] = first.subarray(n)
    }
    have -= count
    return out
  }
  for (;;) {
    const { done, value } = await reader.read()
    if (myGeneration !== generation) return // a newer connection has taken over; this read loop is retired
    if (done) return
    chunks.push(value)
    have += value.length
    for (;;) {
      if (!need) {
        if (have < 8) break
        const lengths = take(8)
        const view = new DataView(lengths.buffer)
        need = view.getUint32(0) + view.getUint32(4)
        headLength = view.getUint32(0)
      }
      if (have < need) break
      const body = take(need)
      need = 0
      const head = JSON.parse(new TextDecoder().decode(body.subarray(0, headLength))) as Header
      void applyPacket(head, body.subarray(headLength), performance.now())
    }
  }
}

async function run(url: string, token: string | null, myGeneration: number) {
  let failures = 0
  while (myGeneration === generation) {
    try {
      await read(url, token, myGeneration)
      failures = 0 // a connection that ran and ended cleanly (e.g. server closed it) is not a failure streak
    } catch {
      // counted below
    }
    if (myGeneration !== generation) return
    if (++failures >= GIVE_UP_AFTER) {
      postMessage({ type: 'failed-all' } satisfies FromWorker)
      return
    }
    await new Promise((resolve) => setTimeout(resolve, RETRY_MS))
  }
}

self.onmessage = (event: MessageEvent<ToWorker>) => {
  const m = event.data
  if (m.type === 'open') {
    generation++
    abort.current.abort()
    abort.current = new AbortController()
    const params = new URLSearchParams()
    if (m.clusterId !== null) params.set('cluster_id', String(m.clusterId))
    if (m.pin !== null) params.set('pin', String(m.pin))
    const qs = params.toString()
    void run(`/api/cameras/live${qs ? `?${qs}` : ''}`, m.token, generation)
  } else if (m.type === 'register') {
    const ctx = m.canvas.getContext('2d')
    if (!ctx) return
    tiles.set(m.cameraId, { canvas: m.canvas, ctx, width: m.width, height: m.height, ratio: m.ratio, shown: null, drawing: 0, paused: false })
  } else if (m.type === 'unregister') {
    const tile = tiles.get(m.cameraId)
    if (tile) {
      cancelAnimationFrame(tile.drawing)
      tile.shown?.bitmap.close()
      tiles.delete(m.cameraId)
    }
  } else if (m.type === 'size') {
    const tile = tiles.get(m.cameraId)
    if (tile) {
      tile.width = m.width
      tile.height = m.height
      tile.ratio = m.ratio
      schedule(m.cameraId)
    }
  } else if (m.type === 'pause') {
    const tile = tiles.get(m.cameraId)
    if (tile) {
      tile.paused = m.paused
      if (!m.paused) schedule(m.cameraId) // resume: paint the newest frame received while paused, right away
    }
  } else if (m.type === 'snapshot') {
    const tile = tiles.get(m.cameraId)
    if (!tile) {
      postMessage({ type: 'snapshot-ready', requestId: m.requestId, blob: null } satisfies FromWorker)
    } else {
      tile.canvas.convertToBlob({ type: 'image/png' }).then(
        (blob) => postMessage({ type: 'snapshot-ready', requestId: m.requestId, blob } satisfies FromWorker),
        () => postMessage({ type: 'snapshot-ready', requestId: m.requestId, blob: null } satisfies FromWorker),
      )
    }
  } else {
    generation++
    abort.current.abort()
    for (const [, tile] of tiles) {
      cancelAnimationFrame(tile.drawing)
      tile.shown?.bitmap.close()
    }
    tiles.clear()
    self.close()
  }
}
