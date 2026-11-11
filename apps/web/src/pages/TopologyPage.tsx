import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Maximize } from 'lucide-react'
import type { Camera, Cluster, GridItem, NodeItem } from '@/api/types'
import TopBar from '@/components/layout/TopBar'
import { useFilters } from '@/contexts/FilterContext'
import { useTheme } from '@/contexts/ThemeContext'
import { useGrid } from '@/hooks/useGrid'
import { useResource } from '@/hooks/useResource'
import { cameraService } from '@/services/camera.service'
import { clusterService } from '@/services/cluster.service'
import { nodeService } from '@/services/node.service'

const NO_CLUSTERS: Cluster[] = []
const NO_NODES: NodeItem[] = []
const NO_CAMERAS: Camera[] = []

// Module-level so useResource sees a stable loader; an inline arrow would refetch on every render.
const loadCameras = () => cameraService.list()

type Level = 'cloud' | 'cluster' | 'node' | 'camera'
type Tone = 'ok' | 'warn' | 'alarm' | 'off' | 'unavailable'

interface GNode {
  key: string
  level: Level
  label: string
  parent: string | null
  cams: number[] // camera ids at or below this vertex, for the state roll-up
  clusterId?: number
  nodeId?: number
  cameraId?: number
  enabled: boolean
  maxCameras?: number
  ip?: string | null
  x: number
  y: number
  vx: number
  vy: number
  fixed: boolean
}

interface Status {
  tone: Tone
  sub: string
}

const RADIUS: Record<Level, number> = { cloud: 40, cluster: 32, node: 26, camera: 19 }
const RING: Record<Level, number> = { cloud: 0, cluster: 240, node: 440, camera: 620 }
const LEVEL_TITLE: Record<Level, string> = { cloud: 'Cloud', cluster: 'Cluster', node: 'EdgeNode', camera: 'Camera' }
const REL: Record<Level, string> = { cloud: '', cluster: 'HAS_CLUSTER', node: 'HAS_NODE', camera: 'HAS_CAMERA' }
const TONE_LABEL: Record<Tone, string> = {
  ok: 'idle', warn: 'people', alarm: 'violation', off: 'disabled / empty', unavailable: 'unavailable (no signal)',
}

const toneOf = (violations: number, people: number, enabled: boolean, online: boolean): Tone =>
  !enabled ? 'off' : !online ? 'unavailable' : violations > 0 ? 'alarm' : people > 0 ? 'warn' : 'ok'

function buildStructure(clusters: Cluster[], nodes: NodeItem[], cameras: Camera[]): GNode[] {
  const base = { enabled: true, x: 0, y: 0, vx: 0, vy: 0, fixed: false }
  const out: GNode[] = [{ ...base, key: 'cloud', level: 'cloud', label: 'Cloud', parent: null, cams: cameras.map((c) => c.id), fixed: true }]
  for (const cl of clusters) {
    const clNodes = nodes.filter((n) => n.cluster_id === cl.id)
    const clCams = cameras.filter((c) => clNodes.some((n) => n.id === c.node_id))
    out.push({ ...base, key: `cluster-${cl.id}`, level: 'cluster', label: cl.name, parent: 'cloud', cams: clCams.map((c) => c.id), clusterId: cl.id })
    for (const n of clNodes) {
      const nCams = cameras.filter((c) => c.node_id === n.id)
      out.push({
        ...base, key: `node-${n.id}`, level: 'node', label: n.name, parent: `cluster-${cl.id}`,
        cams: nCams.map((c) => c.id), clusterId: cl.id, nodeId: n.id, maxCameras: n.max_cameras, ip: n.ip_address,
      })
      for (const c of nCams) {
        out.push({
          ...base, key: `cam-${c.id}`, level: 'camera', label: c.name, parent: `node-${n.id}`,
          cams: [c.id], clusterId: cl.id, nodeId: n.id, cameraId: c.id, enabled: c.enabled,
        })
      }
    }
  }
  return out
}

// Radial tree: every vertex gets an angular sector sized by its camera count, a good start for the force relaxation.
function radialLayout(list: GNode[]) {
  const children = new Map<string, GNode[]>()
  for (const n of list) if (n.parent) children.set(n.parent, [...(children.get(n.parent) ?? []), n])
  const weight = (n: GNode): number => Math.max(1, (children.get(n.key) ?? []).reduce((s, c) => s + weight(c), 0))
  const place = (n: GNode, from: number, to: number) => {
    const a = (from + to) / 2
    n.x = Math.cos(a) * RING[n.level]
    n.y = Math.sin(a) * RING[n.level]
    const kids = children.get(n.key) ?? []
    const total = kids.reduce((s, c) => s + weight(c), 0)
    let cur = from
    for (const k of kids) {
      const span = ((to - from) * weight(k)) / total
      place(k, cur, cur + span)
      cur += span
    }
  }
  const root = list.find((n) => n.level === 'cloud')
  if (root) place(root, 0, Math.PI * 2)
}

function computeStatus(list: GNode[], live: Map<number, GridItem>): Map<string, Status> {
  const out = new Map<string, Status>()
  for (const n of list) {
    let v = 0
    let p = 0
    let online = 0
    for (const id of n.cams) {
      const g = live.get(id)
      v += g?.violation_count_recent ?? 0
      p += g?.person_count ?? 0
      if (g?.online) online += 1
    }
    if (n.level === 'camera') {
      out.set(n.key, {
        tone: toneOf(v, p, n.enabled, online > 0),
        sub: !n.enabled ? 'disabled' : online > 0 ? `${p} people / ${v} violations` : 'unavailable: no signal from the edge',
      })
      continue
    }
    const sub =
      n.level === 'node'
        ? `${n.cams.length}${n.maxCameras ? `/${n.maxCameras}` : ''} cameras${n.ip ? ` / ${n.ip}` : ''} / ${online} online`
        : `${n.cams.length} cameras / ${online} online / ${p} people / ${v} violations`
    out.set(n.key, { tone: n.cams.length === 0 ? 'off' : toneOf(v, p, true, online > 0), sub })
  }
  return out
}

interface Palette {
  bg: string
  panel: string
  line: string
  lineStrong: string
  ink: string
  dim: string
  accent: string
  level: Record<Level, string>
  tone: Record<Tone, string>
}

function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string) => css.getPropertyValue(name).trim()
  return {
    bg: v('--bg'), panel: v('--panel'), line: v('--line'), lineStrong: v('--line-strong'), ink: v('--ink'), dim: v('--dim'),
    accent: v('--accent'),
    level: { cloud: v('--graph-cloud'), cluster: v('--graph-cluster'), node: v('--graph-node'), camera: v('--graph-camera') },
    tone: { ok: v('--ok'), warn: v('--warning'), alarm: v('--danger'), off: v('--line-strong'), unavailable: v('--unavailable') },
  }
}

interface View {
  x: number
  y: number
  k: number
}

export default function TopologyPage() {
  const navigate = useNavigate()
  const { dark } = useTheme()
  const { setClusterId, setNodeId, setCameraId } = useFilters()
  const { data: clusters } = useResource(clusterService.list, NO_CLUSTERS)
  const { data: nodes } = useResource(nodeService.list, NO_NODES)
  const { data: cameras } = useResource(loadCameras, NO_CAMERAS)
  const { items } = useGrid(null, null) // live counters, polled

  const structure = useMemo(() => buildStructure(clusters, nodes, cameras), [clusters, nodes, cameras])
  const live = useMemo(() => new Map(items.map((i) => [i.camera_id, i])), [items])

  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const graph = useRef<GNode[]>([])
  const status = useRef<Map<string, Status>>(new Map())
  const palette = useRef<Palette | null>(null)
  const view = useRef<View>({ x: 0, y: 0, k: 1 })
  const alpha = useRef(0)
  const needFit = useRef(true)
  const hoverKey = useRef<string | null>(null)
  const selectedKey = useRef<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const size = useRef({ w: 0, h: 0 })
  const [tip, setTip] = useState<{ key: string; x: number; y: number } | null>(null)

  const fit = () => {
    const list = graph.current
    const { w, h } = size.current
    if (list.length === 0 || w === 0) return
    const xs = list.map((n) => n.x)
    const ys = list.map((n) => n.y)
    const minX = Math.min(...xs) - 60
    const maxX = Math.max(...xs) + 60
    const minY = Math.min(...ys) - 60
    const maxY = Math.max(...ys) + 60
    const k = Math.min(w / (maxX - minX), h / (maxY - minY), 1.5)
    view.current = { k, x: w / 2 - ((minX + maxX) / 2) * k, y: h / 2 - ((minY + maxY) / 2) * k }
  }

  // Structure changed: keep the positions of vertices that already exist, lay out only the new ones.
  useEffect(() => {
    const old = new Map(graph.current.map((n) => [n.key, n]))
    const fresh = structure.map((n) => ({ ...n }))
    radialLayout(fresh)
    for (const n of fresh) {
      const prev = old.get(n.key)
      if (prev) Object.assign(n, { x: prev.x, y: prev.y, fixed: prev.fixed || n.level === 'cloud' })
    }
    graph.current = fresh
    alpha.current = old.size === 0 ? 1 : 0.5
    needFit.current = old.size === 0
  }, [structure])

  useEffect(() => {
    status.current = computeStatus(graph.current, live)
  }, [live, structure])

  useEffect(() => {
    palette.current = readPalette()
  }, [dark])

  useEffect(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return
    const ctx = canvas.getContext('2d')!
    let raf = 0

    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      const w = wrap.clientWidth
      const h = wrap.clientHeight
      size.current = { w, h }
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
    }
    const ro = new ResizeObserver(resize)
    ro.observe(wrap)
    resize()

    const restLength = (n: GNode, siblings: number) =>
      n.level === 'cluster' ? 240 : n.level === 'node' ? 190 : Math.min(260, 90 + siblings * 3)

    const step = () => {
      const list = graph.current
      const a = alpha.current
      if (a < 0.02) return
      const byKey = new Map(list.map((n) => [n.key, n]))
      const siblings = new Map<string, number>()
      for (const n of list) if (n.parent) siblings.set(n.parent, (siblings.get(n.parent) ?? 0) + 1)
      for (let i = 0; i < list.length; i++) {
        for (let j = i + 1; j < list.length; j++) {
          const p = list[i]
          const q = list[j]
          const dx = q.x - p.x
          const dy = q.y - p.y
          const d2 = Math.max(dx * dx + dy * dy, 25)
          if (d2 > 250000) continue
          const d = Math.sqrt(d2)
          const f = (14000 * a) / d2
          p.vx -= (dx / d) * f
          p.vy -= (dy / d) * f
          q.vx += (dx / d) * f
          q.vy += (dy / d) * f
        }
      }
      for (const n of list) {
        const parent = n.parent ? byKey.get(n.parent) : null
        if (!parent) continue
        const dx = n.x - parent.x
        const dy = n.y - parent.y
        const d = Math.max(Math.hypot(dx, dy), 1)
        const f = (d - restLength(n, siblings.get(n.parent!) ?? 1)) * 0.06 * a
        n.vx -= (dx / d) * f
        n.vy -= (dy / d) * f
        parent.vx += (dx / d) * f * 0.5
        parent.vy += (dy / d) * f * 0.5
      }
      for (const n of list) {
        if (n.fixed) {
          n.vx = 0
          n.vy = 0
          continue
        }
        n.vx *= 0.6
        n.vy *= 0.6
        n.x += n.vx
        n.y += n.vy
      }
      alpha.current = a * 0.985
      if (needFit.current) fit()
      if (alpha.current < 0.1) needFit.current = false
    }

    const draw = (t: number) => {
      const pal = palette.current ?? (palette.current = readPalette())
      const dpr = window.devicePixelRatio || 1
      const { w, h } = size.current
      const { x, y, k } = view.current
      const list = graph.current
      const byKey = new Map(list.map((n) => [n.key, n]))
      const hover = hoverKey.current
      const near = new Set<string>()
      if (hover) {
        near.add(hover)
        for (const n of list) {
          if (n.key === hover && n.parent) near.add(n.parent)
          if (n.parent === hover) near.add(n.key)
        }
      }

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.fillStyle = pal.bg
      ctx.fillRect(0, 0, w, h)
      ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * x, dpr * y)

      // Relationships: grey line, arrowhead on the child, relationship type written along the line.
      for (const n of list) {
        const p = n.parent ? byKey.get(n.parent) : null
        if (!p) continue
        const lit = hover === null || (near.has(n.key) && near.has(p.key))
        const st = status.current.get(n.key)
        const ang = Math.atan2(n.y - p.y, n.x - p.x)
        const len = Math.hypot(n.x - p.x, n.y - p.y)
        const x1 = p.x + Math.cos(ang) * RADIUS[p.level]
        const y1 = p.y + Math.sin(ang) * RADIUS[p.level]
        const tipX = n.x - Math.cos(ang) * (RADIUS[n.level] + 6)
        const tipY = n.y - Math.sin(ang) * (RADIUS[n.level] + 6)
        ctx.globalAlpha = lit ? 1 : 0.15
        ctx.strokeStyle = st?.tone === 'alarm' ? pal.tone.alarm : pal.lineStrong
        ctx.fillStyle = ctx.strokeStyle
        ctx.lineWidth = 1.5 / k
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(tipX, tipY)
        ctx.stroke()
        const ah = 9
        ctx.beginPath()
        ctx.moveTo(tipX, tipY)
        ctx.lineTo(tipX - Math.cos(ang - 0.4) * ah, tipY - Math.sin(ang - 0.4) * ah)
        ctx.lineTo(tipX - Math.cos(ang + 0.4) * ah, tipY - Math.sin(ang + 0.4) * ah)
        ctx.closePath()
        ctx.fill()
        if (k >= 0.55 && len > RADIUS[p.level] + RADIUS[n.level] + 70) {
          const flip = Math.abs(ang) > Math.PI / 2
          ctx.save()
          ctx.translate((x1 + tipX) / 2, (y1 + tipY) / 2)
          ctx.rotate(flip ? ang + Math.PI : ang)
          ctx.font = `${9 / k}px 'IBM Plex Mono', monospace`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'bottom'
          ctx.fillStyle = pal.dim
          ctx.fillText(REL[n.level], 0, -2 / k)
          ctx.restore()
        }
      }

      // Vertices: filled with the colour of their label (type); the state is the outer ring.
      const pulse = (Math.sin(t / 250) + 1) / 2
      for (const n of list) {
        const tone = status.current.get(n.key)?.tone ?? 'off'
        const r = RADIUS[n.level]
        const faded = hover !== null && !near.has(n.key)
        ctx.globalAlpha = faded ? 0.25 : 1
        if (tone === 'alarm') {
          ctx.strokeStyle = pal.tone.alarm
          ctx.globalAlpha = (faded ? 0.25 : 1) * 0.5 * (1 - pulse)
          ctx.lineWidth = 3 / k
          ctx.beginPath()
          ctx.arc(n.x, n.y, r + 6 + pulse * 10, 0, Math.PI * 2)
          ctx.stroke()
          ctx.globalAlpha = faded ? 0.25 : 1
        }
        if (n.key === selectedKey.current) {
          ctx.strokeStyle = pal.ink
          ctx.lineWidth = 2 / k
          ctx.beginPath()
          ctx.arc(n.x, n.y, r + 9, 0, Math.PI * 2)
          ctx.stroke()
        }
        ctx.fillStyle = pal.level[n.level]
        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = pal.tone[tone]
        ctx.lineWidth = 4 / k
        ctx.beginPath()
        ctx.arc(n.x, n.y, r + 2, 0, Math.PI * 2)
        ctx.stroke()
        if (n.fixed && n.level !== 'cloud') {
          ctx.fillStyle = pal.ink
          ctx.beginPath()
          ctx.arc(n.x + r * 0.72, n.y - r * 0.72, 3 / k + 1.5, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // Names sit inside the circle, like Neo4j Browser; when it does not fit, the name goes below.
      ctx.textAlign = 'center'
      for (const n of list) {
        const r = RADIUS[n.level]
        const faded = hover !== null && !near.has(n.key)
        ctx.globalAlpha = faded ? 0.25 : 1
        ctx.font = `${10 / k}px 'IBM Plex Sans', 'Segoe UI', sans-serif`
        const inside = ctx.measureText(n.label).width <= r * 1.7
        if (inside) {
          ctx.fillStyle = '#ffffff'
          ctx.textBaseline = 'middle'
          ctx.fillText(n.label, n.x, n.y)
        } else if (n.level !== 'camera' || k >= 0.6 || near.has(n.key)) {
          ctx.fillStyle = pal.ink
          ctx.textBaseline = 'top'
          ctx.fillText(n.label.length > 24 ? `${n.label.slice(0, 23)}…` : n.label, n.x, n.y + r + 8)
        }
      }
      ctx.globalAlpha = 1

      step()
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [])

  // Pointer handling: wheel zoom at the cursor, drag the background to pan, drag a vertex to move it and pin it.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const pos = (e: MouseEvent | WheelEvent) => {
      const r = canvas.getBoundingClientRect()
      return { sx: e.clientX - r.left, sy: e.clientY - r.top }
    }
    const toWorld = (sx: number, sy: number) => ({ wx: (sx - view.current.x) / view.current.k, wy: (sy - view.current.y) / view.current.k })
    const pick = (sx: number, sy: number) => {
      const { wx, wy } = toWorld(sx, sy)
      const list = graph.current
      for (let i = list.length - 1; i >= 0; i--) {
        const n = list[i]
        const r = RADIUS[n.level] + 6 / view.current.k
        if ((n.x - wx) ** 2 + (n.y - wy) ** 2 <= r * r) return n
      }
      return null
    }

    let drag: { node: GNode | null; sx: number; sy: number; moved: boolean } | null = null

    const onDown = (e: MouseEvent) => {
      const { sx, sy } = pos(e)
      drag = { node: pick(sx, sy), sx, sy, moved: false }
    }
    const onMove = (e: MouseEvent) => {
      const { sx, sy } = pos(e)
      if (drag) {
        const dx = sx - drag.sx
        const dy = sy - drag.sy
        if (Math.hypot(dx, dy) > 3) drag.moved = true
        if (drag.moved) {
          if (drag.node) {
            const { wx, wy } = toWorld(sx, sy)
            drag.node.x = wx
            drag.node.y = wy
            drag.node.fixed = true
            alpha.current = Math.max(alpha.current, 0.3)
          } else {
            view.current.x += dx
            view.current.y += dy
          }
          drag.sx = sx
          drag.sy = sy
        }
        return
      }
      const n = pick(sx, sy)
      const key = n?.key ?? null
      canvas.style.cursor = n ? 'pointer' : 'default'
      if (key !== hoverKey.current) hoverKey.current = key
      setTip(n ? { key: n.key, x: sx, y: sy } : null)
    }
    const onUp = () => {
      if (drag && !drag.moved) select(drag.node?.key ?? null)
      drag = null
    }
    const onLeave = () => {
      drag = null
      hoverKey.current = null
      setTip(null)
    }
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const { sx, sy } = pos(e)
      const v = view.current
      const k = Math.min(4, Math.max(0.15, v.k * Math.exp(-e.deltaY * 0.0015)))
      v.x = sx - ((sx - v.x) / v.k) * k
      v.y = sy - ((sy - v.y) / v.k) * k
      v.k = k
    }
    const onDouble = (e: MouseEvent) => {
      const { sx, sy } = pos(e)
      const n = pick(sx, sy)
      if (n && n.level !== 'cloud') {
        n.fixed = false // release a pinned vertex
        alpha.current = Math.max(alpha.current, 0.3)
      }
    }

    canvas.addEventListener('mousedown', onDown)
    window.addEventListener('mouseup', onUp)
    canvas.addEventListener('mousemove', onMove)
    canvas.addEventListener('mouseleave', onLeave)
    canvas.addEventListener('wheel', onWheel, { passive: false })
    canvas.addEventListener('dblclick', onDouble)
    return () => {
      canvas.removeEventListener('mousedown', onDown)
      window.removeEventListener('mouseup', onUp)
      canvas.removeEventListener('mousemove', onMove)
      canvas.removeEventListener('mouseleave', onLeave)
      canvas.removeEventListener('wheel', onWheel)
      canvas.removeEventListener('dblclick', onDouble)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function select(key: string | null) {
    selectedKey.current = key
    setSelected(key)
  }

  // Sets the shared filters and jumps to the Camera Viewer.
  function open(n: GNode) {
    setClusterId(n.clusterId ?? null)
    if (n.nodeId !== undefined) setNodeId(n.nodeId)
    if (n.cameraId !== undefined) setCameraId(n.cameraId)
    navigate('/')
  }

  const tipNode = tip ? graph.current.find((n) => n.key === tip.key) : null
  const tipStatus = tip ? status.current.get(tip.key) : null
  const selNode = selected ? graph.current.find((n) => n.key === selected) : null
  const selStatus = selected ? status.current.get(selected) : null
  const props: [string, string][] = []
  if (selNode && selStatus) {
    props.push(['name', selNode.label], ['state', TONE_LABEL[selStatus.tone]], ['summary', selStatus.sub])
    if (selNode.clusterId !== undefined) props.push(['cluster_id', String(selNode.clusterId)])
    if (selNode.nodeId !== undefined) props.push(['node_id', String(selNode.nodeId)])
    if (selNode.cameraId !== undefined) props.push(['camera_id', String(selNode.cameraId)])
    if (selNode.ip) props.push(['ip_address', selNode.ip])
    if (selNode.maxCameras) props.push(['max_cameras', String(selNode.maxCameras)])
    props.push(['cameras', String(selNode.cams.length)], ['pinned', selNode.fixed ? 'yes' : 'no'])
  }

  return (
    <div className="flex h-dvh w-screen flex-col overflow-hidden bg-bg text-ink">
      <TopBar />
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-line bg-panel px-3 py-1.5 text-[11px]">
        <span className="text-dim">
          Scroll to zoom, drag the background to pan, drag a node to pin it (double-click releases), click a node for its properties.
        </span>
        <span className="flex flex-wrap items-center gap-3 font-mono text-[10px] text-dim">
          {(['cloud', 'cluster', 'node', 'camera'] as Level[]).map((l) => (
            <span key={l} className="flex items-center gap-1">
              <span className="inline-block size-2.5 rounded-full" style={{ background: `var(--graph-${l})` }} />
              {LEVEL_TITLE[l]}
            </span>
          ))}
          <span className="text-line-strong">|</span>
          {(Object.keys(TONE_LABEL) as Tone[]).map((t) => (
            <span key={t} className="flex items-center gap-1">
              <span
                className="inline-block size-2.5 rounded-full border-2"
                style={{
                  borderColor:
                    t === 'ok' ? 'var(--ok)'
                    : t === 'warn' ? 'var(--warning)'
                    : t === 'alarm' ? 'var(--danger)'
                    : t === 'unavailable' ? 'var(--unavailable)'
                    : 'var(--line-strong)',
                }}
              />
              {TONE_LABEL[t]}
            </span>
          ))}
        </span>
      </div>
      <div ref={wrapRef} className="relative min-h-0 flex-1 overflow-hidden">
        <canvas ref={canvasRef} className="block touch-none" />
        <button
          onClick={() => {
            fit()
            alpha.current = Math.max(alpha.current, 0.05)
          }}
          title="Fit to screen"
          className="absolute right-3 top-3 cursor-pointer rounded border border-line bg-panel p-1.5 text-dim transition-colors hover:border-line-strong hover:text-ink"
        >
          <Maximize size={14} />
        </button>
        {tip && tipNode && tipStatus && tip.key !== selected && (
          <div
            className="pointer-events-none absolute z-10 max-w-64 border border-line-strong bg-panel px-2 py-1 text-[11px]"
            style={{ left: Math.min(tip.x + 14, size.current.w - 260), top: tip.y + 14 }}
          >
            <div className="text-ink">{tipNode.label}</div>
            <div className="font-mono text-[10px] text-dim">{tipStatus.sub}</div>
          </div>
        )}
        {selNode && selStatus && (
          <aside className="absolute bottom-3 right-3 top-12 flex w-64 flex-col border border-line-strong bg-panel text-[11px]">
            <div className="flex items-center gap-2 border-b border-line px-3 py-2">
              <span className="rounded-full px-2 py-0.5 font-mono text-[10px] text-white" style={{ background: `var(--graph-${selNode.level})` }}>
                {LEVEL_TITLE[selNode.level]}
              </span>
              <button onClick={() => select(null)} className="ml-auto cursor-pointer text-dim hover:text-ink">close</button>
            </div>
            <div className="scroll-thin min-h-0 flex-1 overflow-y-auto px-3 py-2">
              <dl className="grid grid-cols-[88px_1fr] gap-x-2 gap-y-1.5 font-mono text-[10px]">
                {props.map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="text-dim">{k}</dt>
                    <dd className="break-words text-ink">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="flex gap-2 border-t border-line p-2">
              {selNode.level !== 'cloud' && (
                <button onClick={() => open(selNode)} className="flex-1 cursor-pointer bg-blue-600 px-2 py-1.5 text-white hover:bg-blue-700">
                  Open in Camera Viewer
                </button>
              )}
              {selNode.fixed && selNode.level !== 'cloud' && (
                <button
                  onClick={() => {
                    selNode.fixed = false
                    alpha.current = Math.max(alpha.current, 0.3)
                    setSelected(selNode.key)
                  }}
                  className="cursor-pointer border border-line px-2 py-1.5 text-dim hover:border-line-strong hover:text-ink"
                >
                  Unpin
                </button>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
