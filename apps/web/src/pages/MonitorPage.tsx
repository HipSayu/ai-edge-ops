import { useEffect, useState } from 'react'
import {
  Activity,
  Camera as CameraIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Loader2,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  ShieldAlert,
} from 'lucide-react'
import type { GridItem, Stats, ViolationEvent } from '@/api/types'
import ChatPanel from '@/components/chat/ChatPanel'
import TopBar from '@/components/layout/TopBar'
import { useFilters } from '@/contexts/FilterContext'
import CameraModal from '@/components/monitor/CameraModal'
import EmptySlot from '@/components/monitor/EmptySlot'
import VmsCameraTile from '@/components/monitor/VmsCameraTile'
import { Badge, Loading, PanelFrame, ResizeHandle } from '@/components/ui'
import { VIOLATION_LABEL } from '@/constants/labels'
import AuthImage from '@/components/ui/AuthImage'
import { downloadBlob, snapshotUrl } from '@/helpers/media'
import { useDragResize } from '@/hooks/useDragResize'
import { useGrid } from '@/hooks/useGrid'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { setCluster, setPaused, snapshotTile } from '@/overlay/liveWall'
import { cameraService } from '@/services/camera.service'
import { gridService } from '@/services/grid.service'
import { formatPercent, formatTime } from '@/utils/format'

type LayoutMode = '1+5' | '2x2' | '3x3' | 'grid'

const LAYOUTS: { mode: LayoutMode; label: string; title: string }[] = [
  { mode: '1+5', label: '1+5 View', title: '1 Primary + 5 Secondary (Perspective VMS)' },
  { mode: '2x2', label: '2x2', title: '2x2 Grid' },
  { mode: '3x3', label: '3x3', title: '3x3 Grid' },
  { mode: 'grid', label: 'Auto Grid', title: 'Auto Adaptive Grid' },
]

const HEADER_PX = 32 // height of a collapsed block: its title bar
const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

// A camera cell: a 16:9 box on narrow screens, a grid-filling cell on wide ones
// Positions of a fixed layout that have no camera: [0, 1, ...] for however many are missing
const emptySlots = (total: number, shown: number) => Array.from({ length: Math.max(0, total - Math.min(shown, total)) }, (_, i) => i)

const CELL = 'aspect-video min-w-0 lg:aspect-auto lg:h-full lg:min-h-0 lg:w-full'

export default function MonitorPage() {
  const { clusterId, nodeId, cameraId: cameraIdFilter } = useFilters()

  const [openId, setOpenId] = useState<number | null>(null)
  const [selectedCamId, setSelectedCamId] = useState<number | null>(null)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('1+5')
  const [, setStats] = useState<Stats | null>(null)
  const [events, setEvents] = useState<ViolationEvent[]>([])
  const { items, loading } = useGrid(clusterId, openId)
  const [nowStr, setNowStr] = useState('')
  const [dockPaused, setDockPaused] = useState(false)
  const [dockSnapshotting, setDockSnapshotting] = useState(false)

  // One shared connection carries the live video+boxes of every camera this page shows; it must match what useGrid
  // is asking for (same cluster, same pinned/opened camera), so the two never disagree about which cameras are live.
  useEffect(() => {
    setCluster(clusterId, openId)
  }, [clusterId, openId])

  // Infinite Scroll Event pagination limit
  const [eventScrollLimit, setEventScrollLimit] = useState(25)

  // Panel layout: what is collapsed, and the sizes the user dragged
  const isMobile = useMediaQuery('(max-width: 1023px)')
  const [isCameraCollapsed, setIsCameraCollapsed] = useState(false)
  const [isLogsCollapsed, setIsLogsCollapsed] = useState(false)
  const [isChatCollapsed, setIsChatCollapsed] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(384) // wide screens: width of the right column, px
  const [chatHeight, setChatHeight] = useState(380) // height of the chat block, px
  const [logsHeight, setLogsHeight] = useState(220) // narrow screens: height of the violation logs, px

  // Wide screens: drag the bar between the camera viewer and the right column
  const sideDrag = useDragResize('col-resize', (e) => {
    const width = window.innerWidth - e.clientX
    if (width >= 240 && width <= Math.min(850, window.innerWidth - 250)) {
      setSidebarWidth(width)
      setIsSidebarCollapsed(false)
    }
  })

  // Wide screens: drag the bar between the violation logs and the chat
  const chatDrag = useDragResize('row-resize', (e) => {
    const height = window.innerHeight - e.clientY
    if (height >= 100 && height <= window.innerHeight - 150) {
      setChatHeight(height)
      setIsChatCollapsed(false)
    }
  })

  // Narrow screens: drag the top edge of the bottom panel; the chat keeps its height, the logs take the rest
  const logsDrag = useDragResize('row-resize', (e) => {
    const chatPx = isChatCollapsed ? HEADER_PX : chatHeight
    const next = window.innerHeight - e.clientY - chatPx
    setLogsHeight(clamp(next, HEADER_PX, window.innerHeight - chatPx - 120)) // keep 120px for the cameras
    setIsLogsCollapsed(false)
  })

  // Live Clock
  useEffect(() => {
    const updateTime = () => {
      const d = new Date()
      setNowStr(d.toLocaleDateString() + ' ' + d.toLocaleTimeString())
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  // Auto-select first camera or sync with selected filters
  useEffect(() => {
    if (cameraIdFilter) {
      setSelectedCamId(cameraIdFilter)
    } else if (nodeId) {
      const matchCam = items.find((c) => c.node_id === nodeId)
      if (matchCam) setSelectedCamId(matchCam.camera_id)
    } else if (items.length > 0 && selectedCamId === null) {
      setSelectedCamId(items[0].camera_id)
    }
  }, [items, selectedCamId, nodeId, cameraIdFilter])

  // Periodic stats reload
  useEffect(() => {
    let alive = true
    const load = () =>
      gridService
        .stats(clusterId)
        .then((s) => alive && setStats(s))
        .catch(() => {})
    load()
    const timer = setInterval(load, 15000)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [clusterId])

  // Fetch Full events across all cameras in current scope
  useEffect(() => {
    let alive = true
    const loadEvents = async () => {
      try {
        if (items.length === 0) return
        const promises = items.slice(0, 10).map((c) => cameraService.events(c.camera_id, 30).catch(() => []))
        const results = await Promise.all(promises)
        const allEvs = results.flat().sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        if (alive) setEvents(allEvs)
      } catch {}
    }
    loadEvents()
    const timer = setInterval(loadEvents, 5000)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [items])

  const opened: GridItem | undefined = items.find((i) => i.camera_id === openId)
  const selectedItem: GridItem | undefined =
    items.find((i) => i.camera_id === selectedCamId) || items[0]

  useEffect(() => setDockPaused(false), [selectedItem?.camera_id]) // a freshly selected camera starts unpaused

  const secondaryItems = items.filter((i) => i.camera_id !== selectedItem?.camera_id)
  const totalPeople = items.reduce((acc, curr) => acc + (curr.person_count || 0), 0)

  // Filter items strictly by Cluster -> Node -> Camera hierarchy
  const displayedItems = items.filter((i) => {
    const matchCluster = clusterId === null || i.cluster_id === clusterId
    const matchNode = nodeId === null || i.node_id === nodeId
    const matchCam = cameraIdFilter === null || i.camera_id === cameraIdFilter
    return matchCluster && matchNode && matchCam
  })

  // Infinite scroll trigger
  const handleScrollEvents = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
    if (scrollHeight - scrollTop <= clientHeight + 30) {
      if (eventScrollLimit < events.length) {
        setEventScrollLimit((prev) => prev + 15)
      }
    }
  }

  const scrollVisibleEvents = events.slice(0, eventScrollLimit)

  const tile = (item: GridItem) => (
    <VmsCameraTile
      item={item}
      isSelected={selectedCamId === item.camera_id}
      isMaximized={openId === item.camera_id}
      onSelect={() => setSelectedCamId(item.camera_id)}
      onMaximize={() => setOpenId((curr) => (curr === item.camera_id ? null : item.camera_id))}
      nowStr={nowStr}
    />
  )

  const detailsOpen = Boolean(openId && selectedItem && openId === selectedItem.camera_id)

  // Sizes of the three blocks. The parent sets how much room each gets; PanelFrame sets what it looks like.
  const cameraClass = isCameraCollapsed ? (isMobile ? 'flex-none' : 'w-7 flex-none') : 'flex-1 bg-black'
  const asideClass = isMobile
    ? `w-full ${isCameraCollapsed ? 'min-h-0 flex-1' : 'flex-none'}`
    : isCameraCollapsed
      ? 'flex-1'
      : `${isSidebarCollapsed ? 'w-0 border-none pointer-events-none' : ''} ${
          sideDrag.dragging ? '' : 'transition-[width] duration-150'
        }`
  const asideStyle = !isMobile && !isCameraCollapsed ? { width: isSidebarCollapsed ? 0 : sidebarWidth } : undefined
  const chatHandleShown = !isMobile && !isChatCollapsed && !isLogsCollapsed
  const logsFixed = isMobile && !isLogsCollapsed && !isCameraCollapsed
  const logsClass = isLogsCollapsed ? 'flex-none' : logsFixed ? 'flex-none' : isMobile ? 'min-h-0 flex-1' : 'min-h-[140px] flex-1'

  return (
    <div className="flex h-dvh w-screen flex-col overflow-hidden bg-bg text-ink">
      {/* 1. Header with Strict Hierarchy Filters: Cluster -> Node -> Cameras */}
      <TopBar
        totalCameras={items.length}
        totalPeople={totalPeople}
        cameras={items}
      />

      {/* 2. Main 1-Screen Body: camera viewer | right column (violation logs, AI assistant) */}
      <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
        <PanelFrame
          title="Camera Viewer"
          icon={<CameraIcon size={13} className="text-cyan-400" />}
          badge={
            <span className="hidden font-mono text-[10px] font-normal normal-case tracking-normal text-dim sm:inline">
              [ {displayedItems.length} CHANNELS LIVE ]
            </span>
          }
          actions={
            <div className="flex items-center gap-1">
              {LAYOUTS.map(({ mode, label, title }) => (
                <button
                  key={mode}
                  onClick={() => setLayoutMode(mode)}
                  title={title}
                  className={`rounded px-2 py-0.5 text-[11px] font-semibold transition-colors cursor-pointer ${
                    layoutMode === mode ? 'bg-blue-600 text-white' : 'text-dim hover:text-ink hover:bg-panel2'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          }
          collapsed={isCameraCollapsed}
          onToggleCollapse={() => setIsCameraCollapsed(!isCameraCollapsed)}
          collapseAxis={isMobile ? 'vertical' : 'horizontal'}
          className={cameraClass}
        >
          {/* Camera Grid Area - full height with zero overflow gap */}
          <div className="min-h-0 flex-1 overflow-y-auto bg-black p-1 lg:overflow-hidden">
            {loading && items.length === 0 && (
              <div className="grid h-full place-items-center">
                <Loading label="Connecting camera video streams..." size="md" />
              </div>
            )}

            {!loading && items.length === 0 && (
              <div className="grid h-full place-items-center p-6 text-center text-xs text-dim">
                <div>
                  <CameraIcon size={32} className="mx-auto mb-2 text-dim/50" />
                  <p className="font-semibold text-ink">No cameras available</p>
                  <p className="mt-1">
                    To connect a camera, create a <strong>Cluster</strong>, deploy an <strong>Edge Node</strong>, and add a Camera in Administration.
                  </p>
                </div>
              </div>
            )}

            {/* Layout 1: 1 Primary Large + 5 Secondary (Perspective VMS) */}
            {layoutMode === '1+5' && displayedItems.length > 0 && selectedItem && (
              <div className="grid w-full gap-1 grid-cols-2 lg:h-full lg:grid-cols-3 lg:grid-rows-3 lg:overflow-hidden">
                <div className="col-span-2 aspect-video min-w-0 lg:col-span-2 lg:row-span-2 lg:aspect-auto lg:min-h-0">
                  {tile(selectedItem)}
                </div>
                {secondaryItems.slice(0, 5).map((item) => (
                  <div key={item.camera_id} className="aspect-video min-w-0 lg:aspect-auto lg:min-h-0">
                    {tile(item)}
                  </div>
                ))}
                {emptySlots(5, secondaryItems.length).map((n) => (
                  <div key={`empty-${n}`} className="aspect-video min-w-0 lg:aspect-auto lg:min-h-0">
                    <EmptySlot />
                  </div>
                ))}
              </div>
            )}

            {/* Layout 2: 2x2 Matrix */}
            {layoutMode === '2x2' && (
              <div className="grid w-full gap-1 grid-cols-2 lg:h-full lg:grid-rows-2 lg:overflow-hidden">
                {displayedItems.slice(0, 4).map((item) => (
                  <div key={item.camera_id} className={CELL}>
                    {tile(item)}
                  </div>
                ))}
                {emptySlots(4, displayedItems.length).map((n) => (
                  <div key={`empty-${n}`} className={CELL}>
                    <EmptySlot />
                  </div>
                ))}
              </div>
            )}

            {/* Layout 3: 3x3 Matrix */}
            {layoutMode === '3x3' && (
              <div className="grid w-full gap-1 grid-cols-2 sm:grid-cols-3 lg:h-full lg:grid-rows-3 lg:overflow-hidden">
                {displayedItems.slice(0, 9).map((item) => (
                  <div key={item.camera_id} className={CELL}>
                    {tile(item)}
                  </div>
                ))}
                {emptySlots(9, displayedItems.length).map((n) => (
                  <div key={`empty-${n}`} className={CELL}>
                    <EmptySlot />
                  </div>
                ))}
              </div>
            )}

            {/* Layout 4: Auto Responsive Grid */}
            {layoutMode === 'grid' && (
              <div className="grid w-full gap-1 grid-cols-2 md:grid-cols-3 lg:h-full lg:grid-cols-4 lg:auto-rows-fr lg:overflow-hidden">
                {displayedItems.map((item) => (
                  <div key={item.camera_id} className={CELL}>
                    {tile(item)}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* VMS Bottom Dock Bar - aligned with AI Assistant composer */}
          <div className="flex h-11 shrink-0 select-none items-center justify-between border-t border-line bg-panel/95 backdrop-blur-md px-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-extrabold uppercase text-[10px] tracking-wider text-dim">
                Camera Control:
              </span>
              <span className="font-mono text-cyan-400 font-bold text-[11px] bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                {selectedItem ? selectedItem.name : 'NO CAMERA SELECTED'}
              </span>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center gap-1 text-dim">
              <button
                onClick={() => {
                  if (selectedItem) {
                    setOpenId((curr) => (curr === selectedItem.camera_id ? null : selectedItem.camera_id))
                  }
                }}
                title={detailsOpen ? 'Minimize / Close Details' : 'Maximize / View Camera Details'}
                className="flex items-center gap-1 rounded bg-panel2/80 px-2 py-1 text-[11px] font-semibold text-ink hover:bg-panel2 hover:text-white border border-line cursor-pointer transition-colors"
              >
                {detailsOpen ? (
                  <>
                    <Minimize2 size={12} className="text-cyan-400" />
                    <span className="text-cyan-400">Minimize</span>
                  </>
                ) : (
                  <>
                    <Maximize2 size={12} />
                    <span>Details</span>
                  </>
                )}
              </button>
              <button
                onClick={async () => {
                  if (!selectedItem) return
                  setDockSnapshotting(true)
                  const blob = await snapshotTile(selectedItem.camera_id)
                  setDockSnapshotting(false)
                  if (blob) downloadBlob(blob, `${selectedItem.name}-${new Date().toISOString().replace(/[:.]/g, '-')}.png`)
                }}
                disabled={!selectedItem || dockSnapshotting}
                title="Snapshot"
                className="rounded p-1 hover:bg-panel2 hover:text-ink cursor-pointer transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {dockSnapshotting ? <Loader2 size={13} className="animate-spin" /> : <CameraIcon size={13} />}
              </button>
              <button
                onClick={() => {
                  if (!selectedItem) return
                  const next = !dockPaused
                  setDockPaused(next)
                  setPaused(selectedItem.camera_id, next)
                }}
                disabled={!selectedItem}
                title={dockPaused ? 'Resume' : 'Pause'}
                className="rounded p-1 hover:bg-panel2 hover:text-ink cursor-pointer transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {dockPaused ? <Play size={13} className="text-cyan-400" /> : <Pause size={13} />}
              </button>
            </div>
          </div>
        </PanelFrame>

        {/* Wide screens: bar between the camera viewer and the right column, with its collapse button */}
        {!isMobile && !isCameraCollapsed && (
          <ResizeHandle
            axis="col"
            dragging={sideDrag.dragging}
            onPointerDown={sideDrag.start}
            title="Drag to resize panels horizontally"
          >
            <button
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              title={isSidebarCollapsed ? 'Expand Side Panel' : 'Collapse Side Panel (Maximize Camera Viewer)'}
              className="absolute top-1/2 -left-2 z-30 flex size-4 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-panel2 text-dim hover:bg-blue-600 hover:text-white transition-all shadow cursor-pointer opacity-70 group-hover:opacity-100"
            >
              {isSidebarCollapsed ? <ChevronLeft size={10} /> : <ChevronRight size={10} />}
            </button>
          </ResizeHandle>
        )}

        {/* Right column: violation logs on top, AI assistant below. On wide screens it is positioned, so a block of it that is
            maximized fills the column (its full height, its own width) and not the whole work area */}
        <aside
          style={asideStyle}
          className={`${isMobile ? '' : 'relative'} flex shrink-0 flex-col overflow-hidden border-t border-line bg-panel text-xs select-none lg:border-t-0 ${asideClass}`}
        >
          {/* Narrow screens: drag the top edge to make the violation logs taller or shorter */}
          {isMobile && !isCameraCollapsed && (
            <ResizeHandle
              axis="row"
              dragging={logsDrag.dragging}
              onPointerDown={logsDrag.start}
              title="Drag to resize Violation Event Logs"
              grip
              className="!h-4"
            />
          )}

          <PanelFrame
            title="Violation Event Logs"
            icon={<ShieldAlert size={13} className="text-rose-500" />}
            badge={
              <span className="ml-1 rounded bg-rose-600/90 px-1.5 py-0.2 font-mono text-[10px] font-bold tracking-normal text-white">
                {events.length} logs
              </span>
            }
            collapsed={isLogsCollapsed}
            onToggleCollapse={() => setIsLogsCollapsed(!isLogsCollapsed)}
            className={logsClass}
            style={logsFixed ? { height: logsHeight } : undefined}
          >
            {/* Scrollable Event List with no-scrollbar */}
            <div
              onScroll={handleScrollEvents}
              className="no-scrollbar min-h-0 flex-1 overflow-y-auto divide-y divide-line/60 p-1"
            >
              {events.length === 0 && (
                <div className="flex h-full flex-col items-center justify-center p-3 text-center text-dim">
                  <Activity size={18} className="mb-1 text-dim/60" />
                  <p className="font-semibold text-[11px]">No violations recorded</p>
                  <p className="text-[10px] text-dim/80">Compliance standards currently met</p>
                </div>
              )}
              {scrollVisibleEvents.map((e) => {
                const cam = items.find((c) => c.camera_id === e.camera_id)
                return (
                  <div
                    key={e.id}
                    onClick={() => setOpenId(e.camera_id)}
                    className="flex items-center gap-2 p-1.5 hover:bg-panel2/60 transition-colors cursor-pointer rounded"
                  >
                    <AuthImage
                      src={snapshotUrl(e.id)}
                      alt=""
                      className="size-8 shrink-0 rounded bg-black object-cover border border-line"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="font-mono text-[10px] text-blue-400 font-bold">
                          [{cam?.name ?? `Cam ${e.camera_id}`}]
                        </span>
                        <p className="truncate font-semibold text-ink text-[11px]">
                          {VIOLATION_LABEL[e.violation_type]}
                        </p>
                      </div>
                      <p className="flex items-center gap-1 text-[10px] text-dim font-mono">
                        <Clock size={10} />
                        {formatTime(e.created_at)}
                      </p>
                    </div>
                    <Badge tone="danger" dot>
                      {formatPercent(e.confidence)}
                    </Badge>
                  </div>
                )
              })}

              {eventScrollLimit < events.length && (
                <div className="py-2 text-center text-[10px] text-dim font-mono">
                  Scroll for more events ({scrollVisibleEvents.length}/{events.length})
                </div>
              )}
            </div>
          </PanelFrame>

          {/* Wide screens: bar between the violation logs and the AI assistant */}
          {chatHandleShown && (
            <ResizeHandle
              axis="row"
              dragging={chatDrag.dragging}
              onPointerDown={chatDrag.start}
              title="Drag to resize AI Assistant height vertically"
            />
          )}

          <ChatPanel
            collapsed={isChatCollapsed}
            onToggleCollapse={() => setIsChatCollapsed(!isChatCollapsed)}
            className={`${chatHandleShown ? '' : 'border-t border-line'} ${
              isLogsCollapsed && !isChatCollapsed && !isMobile ? 'flex-1' : 'shrink-0'
            }`}
            style={isChatCollapsed || (isLogsCollapsed && !isMobile) ? undefined : { height: chatHeight }}
          />
        </aside>
      </div>

      {opened && <CameraModal item={opened} onClose={() => setOpenId(null)} />}
    </div>
  )
}
