import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Terminal, Server, Play, Pause, Download, Trash2, Search,
  Layers, Copy, Check, ArrowDown,
} from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import type { RuntimeId, LogLevel } from '@/modules/agent/types/logs'
import { useNodeLogStream } from '@/modules/agent/hooks/useNodeLogStream'

const LEVEL_COLORS: Record<LogLevel, { text: string; bg: string; border: string }> = {
  INFO:  { text: 'text-info',        bg: 'bg-info/10',        border: 'border-info/20' },
  WARN:  { text: 'text-warning',     bg: 'bg-warning/10',     border: 'border-warning/20' },
  ERROR: { text: 'text-destructive', bg: 'bg-destructive/10', border: 'border-destructive/20' },
  DEBUG: { text: 'text-muted-foreground', bg: 'bg-muted/40', border: 'border-border' },
  TRACE: { text: 'text-purple-400',  bg: 'bg-purple-500/10',  border: 'border-purple-500/20' },
}

export default function NodeLogsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { clusters } = useEdgeOps()

  const [selectedClusterId, setSelectedClusterId] = useState<string>('cluster-hn')
  const [selectedNodeId, setSelectedNodeId] = useState<string>('hn-node-1')
  const [selectedRuntime, setSelectedRuntime] = useState<RuntimeId | 'all'>('all')


  const [logLevel, setLogLevel] = useState<LogLevel | 'ALL'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [copied, setCopied] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)

  const terminalContainerRef = useRef<HTMLDivElement | null>(null)
  const isAutoScrollingRef = useRef(false)

  // Detect when user scrolls manually
  const handleScroll = () => {
    const el = terminalContainerRef.current
    if (!el || isAutoScrollingRef.current) return
    // Check if scrolled near bottom (within 40px threshold)
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    if (autoScroll !== isAtBottom) {
      setAutoScroll(isAtBottom)
    }
  }

  // Scroll to bottom helper
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    const el = terminalContainerRef.current
    if (!el) return
    isAutoScrollingRef.current = true
    el.scrollTo({ top: el.scrollHeight, behavior })
    setTimeout(() => {
      isAutoScrollingRef.current = false
    }, 150)
  }

  // ── 1. Init selection once clusters arrive (clusters update on every realtime tick) ──
  const hasClusters = clusters.length > 0
  useEffect(() => {
    if (!hasClusters) return
    const paramNodeId = searchParams.get('nodeId')
    if (paramNodeId) {
      const owningCluster = clusters.find((c) => c.nodes.some((n) => n.id === paramNodeId))
      if (owningCluster) {
        setSelectedClusterId(owningCluster.id)
        setSelectedNodeId(paramNodeId)
      }
    } else if (clusters[0]) {
      setSelectedClusterId(clusters[0].id)
      if (clusters[0].nodes[0]) setSelectedNodeId(clusters[0].nodes[0].id)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasClusters, searchParams])

  // Current cluster and node objects
  const activeCluster = clusters.find((c) => c.id === selectedClusterId) || clusters[0]
  const activeNode = activeCluster?.nodes.find((n) => n.id === selectedNodeId) || activeCluster?.nodes[0]

  // ── 2. Runtimes & logs come from context (initial API load + realtime) ──
  const { runtimes, logs, isLive: isLiveStreaming, toggleLive, clear: handleClearLogs } =
    useNodeLogStream(activeNode?.id, selectedRuntime, logLevel)

  // Auto-scroll on logs update if autoScroll is enabled
  useEffect(() => {
    if (autoScroll) {
      scrollToBottom('smooth')
    }
  }, [logs, autoScroll])

  // Actions

  const handleCopyLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.level}] [${l.runtime}] ${l.message}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const handleDownloadLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.level}] [${l.runtime}] ${l.message}`).join('\n')
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${activeNode?.name || 'node'}-${selectedRuntime}-logs.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filteredLogs = logs.filter((l) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return l.message.toLowerCase().includes(q) || l.runtime.toLowerCase().includes(q)
  })

  // Selected runtime details
  const activeRuntimeObj = runtimes.find((r) => r.id === selectedRuntime)

  return (
    <div className="flex flex-col gap-5">
      {/* ── 1. SELECTOR TOOLBAR: Cluster -> Node Agent -> Runtime ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3">
        {/* Cluster & Node Selection */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Cluster Dropdown */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-xs font-semibold text-muted-foreground">
              <Layers size={13} className="text-brand" />
              Cluster:
            </span>
            <select
              value={selectedClusterId}
              onChange={(e) => {
                setSelectedClusterId(e.target.value)
                const c = clusters.find((cls) => cls.id === e.target.value)
                if (c && c.nodes[0]) {
                  setSelectedNodeId(c.nodes[0].id)
                  setSearchParams({ nodeId: c.nodes[0].id })
                }
              }}
              className="rounded-lg border border-border bg-muted/40 px-2.5 py-1.5 text-xs font-bold text-foreground outline-none focus:border-brand"
            >
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.site})
                </option>
              ))}
            </select>
          </div>

          <div className="hidden h-4 w-px bg-border sm:block" />

          {/* Node Agent Dropdown */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-xs font-semibold text-muted-foreground">
              <Server size={13} className="text-info" />
              Node Agent:
            </span>
            <select
              value={selectedNodeId}
              onChange={(e) => {
                setSelectedNodeId(e.target.value)
                setSearchParams({ nodeId: e.target.value })
              }}
              className="rounded-lg border border-border bg-muted/40 px-2.5 py-1.5 text-xs font-bold text-foreground outline-none focus:border-brand"
            >
              {activeCluster?.nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name} — {n.ip} ({n.cameras.length} cams)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Node status badges */}
        {activeNode && (
          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
              {activeNode.hardware}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
              activeNode.status === 'online' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
            }`}>
              {activeNode.status}
            </span>
            <span className="text-muted-foreground font-mono text-[11px]">
              CPU: {activeNode.cpuUsage}% · GPU: {activeNode.gpuUsage}%
            </span>
          </div>
        )}
      </div>

      {/* ── 2. RUNTIME PROCESS TABS ── */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-border pb-3">
        <button
          onClick={() => setSelectedRuntime('all')}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
            selectedRuntime === 'all'
              ? 'bg-foreground text-background'
              : 'text-muted-foreground hover:bg-muted/60'
          }`}
        >
          <Terminal size={13} />
          <span>All Runtimes &amp; Logs</span>
        </button>

        {runtimes.map((r) => (
          <button
            key={r.id}
            onClick={() => setSelectedRuntime(r.id)}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              selectedRuntime === r.id
                ? 'bg-foreground text-background'
                : 'text-muted-foreground hover:bg-muted/60'
            }`}
          >
            <span className={`size-1.5 rounded-full ${r.status === 'running' ? 'bg-success' : 'bg-warning'}`} />
            <span>{r.name.split(' (')[0]}</span>
            {r.errorCount24h > 0 && (
              <span className="rounded-full bg-destructive/20 px-1 text-[9px] font-bold text-destructive">
                {r.errorCount24h}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── 3. RUNTIME PROCESS TELEMETRY STRIP (if specific runtime selected) ── */}
      {activeRuntimeObj && selectedRuntime !== 'all' && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">Status</span>
            <span className="text-xs font-bold text-success capitalize mt-0.5 inline-block">{activeRuntimeObj.status}</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">PID</span>
            <span className="text-xs font-mono font-bold text-foreground mt-0.5 inline-block">{activeRuntimeObj.pid}</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">CPU Usage</span>
            <span className="text-xs font-mono font-bold text-info mt-0.5 inline-block">{activeRuntimeObj.cpuPercent}%</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">Memory</span>
            <span className="text-xs font-mono font-bold text-foreground mt-0.5 inline-block">{activeRuntimeObj.memoryMb} MB</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">Uptime</span>
            <span className="text-xs font-mono font-medium text-muted-foreground mt-0.5 inline-block">{activeRuntimeObj.uptime}</span>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <span className="text-[10px] font-semibold text-muted-foreground block">24h Errors</span>
            <span className={`text-xs font-mono font-bold mt-0.5 inline-block ${
              activeRuntimeObj.errorCount24h > 0 ? 'text-destructive' : 'text-success'
            }`}>
              {activeRuntimeObj.errorCount24h} err
            </span>
          </div>
        </div>
      )}

      {/* ── 4. LOG TERMINAL VIEWER ── */}
      <div className="flex flex-col rounded-xl border border-border bg-card overflow-hidden transition-colors">
        {/* Terminal Header & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/20 px-4 py-2.5">
          {/* Left: Stream status & count */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className={`size-2 rounded-full ${isLiveStreaming ? 'animate-pulse bg-success' : 'bg-muted-foreground'}`} />
              <span className="text-xs font-bold text-foreground">
                {isLiveStreaming ? 'Live Log Stream' : 'Stream Paused'}
              </span>
            </div>
            <span className="text-xs font-mono text-muted-foreground">
              ({filteredLogs.length} events)
            </span>
          </div>

          {/* Right: Search, Filter by Level, Actions */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Search */}
            <div className="relative flex items-center">
              <Search size={12} className="absolute left-2.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search log stream..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-7 w-36 rounded-md border border-border bg-background pl-7 pr-2 text-xs text-foreground placeholder:text-muted-foreground focus:w-48 focus:border-brand transition-all outline-none"
              />
            </div>

            {/* Level filter */}
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value as LogLevel | 'ALL')}
              className="h-7 rounded-md border border-border bg-background px-2 text-[11px] font-semibold text-foreground outline-none"
            >
              <option value="ALL">All Levels</option>
              <option value="INFO">Info</option>
              <option value="WARN">Warn</option>
              <option value="ERROR">Error</option>
              <option value="DEBUG">Debug</option>
            </select>

            {/* Pause / Resume */}
            <button
              onClick={toggleLive}
              className={`flex h-7 items-center gap-1 rounded-md px-2.5 text-xs font-semibold transition-colors ${
                isLiveStreaming ? 'bg-muted text-foreground hover:bg-muted/80' : 'bg-success/20 text-success'
              }`}
            >
              {isLiveStreaming ? <Pause size={12} /> : <Play size={12} />}
              <span>{isLiveStreaming ? 'Pause' : 'Resume'}</span>
            </button>

            <div className="h-4 w-px bg-border/60 mx-0.5" />

            {/* Copy */}
            <button
              onClick={handleCopyLogs}
              title="Copy visible logs"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
            </button>

            {/* Download */}
            <button
              onClick={handleDownloadLogs}
              title="Download .log file"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              <Download size={13} />
            </button>

            {/* Clear */}
            <button
              onClick={handleClearLogs}
              title="Clear terminal"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-destructive transition-colors cursor-pointer"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>

        {/* Terminal Body */}
        <div className="relative">
          <div
            ref={terminalContainerRef}
            onScroll={handleScroll}
            className="h-[480px] overflow-y-auto p-4 font-mono text-[12px] leading-relaxed bg-background/50 text-foreground transition-colors"
          >
            {filteredLogs.map((log, index) => {
              const levelStyle = LEVEL_COLORS[log.level] || LEVEL_COLORS.INFO
              return (
                <div
                  key={log.id}
                  className="group flex items-start gap-2.5 py-1 transition-colors hover:bg-muted/30 rounded px-1.5"
                >
                  {/* Line number */}
                  <span className="w-8 shrink-0 text-right select-none text-[10px] text-muted-foreground/60">
                    {index + 1}
                  </span>

                  {/* Timestamp */}
                  <span className="shrink-0 text-[11px] text-muted-foreground">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}.{new Date(log.timestamp).getMilliseconds().toString().padStart(3, '0')}
                  </span>

                  {/* Level Badge */}
                  <span className={`shrink-0 rounded border px-1.5 py-px text-[9px] font-bold ${levelStyle.bg} ${levelStyle.text} ${levelStyle.border}`}>
                    {log.level}
                  </span>

                  {/* Runtime Badge */}
                  <span className="shrink-0 text-[11px] text-brand font-semibold">
                    [{log.runtime}]
                  </span>

                  {/* Log Message */}
                  <span className={`flex-1 break-all ${log.level === 'ERROR' ? 'text-destructive font-medium' : log.level === 'WARN' ? 'text-warning' : 'text-foreground'}`}>
                    {log.message}
                  </span>
                </div>
              )
            })}

            {filteredLogs.length === 0 && (
              <div className="flex h-48 flex-col items-center justify-center text-muted-foreground gap-2">
                <Terminal size={24} />
                <p className="text-xs">No logs found matching current filter.</p>
              </div>
            )}
          </div>

          {/* Floating Jump to Latest Button (shown when user scrolled up) */}
          {!autoScroll && (
            <button
              onClick={() => {
                setAutoScroll(true)
                scrollToBottom('smooth')
              }}
              className="absolute bottom-4 right-6 flex items-center gap-1.5 rounded-full border border-border bg-card/95 px-3 py-1.5 text-xs font-semibold text-foreground backdrop-blur-sm hover:bg-muted hover:border-brand/40 transition-all animate-bounce cursor-pointer"
            >
              <ArrowDown size={13} className="text-brand" />
              <span>Jump to Latest</span>
              <span className="size-2 rounded-full bg-success animate-pulse" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
