import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { WifiOff } from 'lucide-react'
import { streamingService } from '@/shared/api/services/streaming'
import { playWhep, type WhepSession } from './whep'

export interface WhepStats {
  width: number
  height: number
  fps: number
  bitrateKbps: number
  /** Jitter buffer delay, i.e. receive-side latency added by WebRTC's playout buffer. */
  latencyMs: number
}

interface Props {
  /** server-side Camera.id */
  cameraId: string | number
  className?: string
  muted?: boolean
  onStats?: (stats: WhepStats) => void
  onStatusChange?: (status: 'connecting' | 'live' | 'error') => void
}

/**
 * Live camera stream via WHEP. Fetches a short-lived view token, negotiates a
 * WebRTC session with MediaMTX, renders the track in a <video>, and (optionally)
 * reports inbound-video stats every 2s.
 */
const WhepVideo = forwardRef<HTMLVideoElement, Props>(function WhepVideo(
  { cameraId, className, muted = true, onStats, onStatusChange },
  ref,
) {
  const videoRef = useRef<HTMLVideoElement>(null)
  useImperativeHandle(ref, () => videoRef.current as HTMLVideoElement, [])
  const [status, setStatus] = useState<'connecting' | 'live' | 'error'>('connecting')

  // Keep callbacks in refs so a new function identity per parent render doesn't
  // tear down and re-establish the WebRTC session.
  const onStatsRef = useRef(onStats)
  const onStatusRef = useRef(onStatusChange)
  onStatsRef.current = onStats
  onStatusRef.current = onStatusChange

  useEffect(() => onStatusRef.current?.(status), [status])

  useEffect(() => {
    let session: WhepSession | null = null
    let disposed = false
    let statsTimer: ReturnType<typeof setInterval> | undefined
    const ac = new AbortController()

    async function connect() {
      setStatus('connecting')
      try {
        const tok = await streamingService.viewToken(cameraId)
        if (disposed || !videoRef.current) return
        session = await playWhep(videoRef.current, tok.url, tok.token, ac.signal)
        if (disposed) return session.close()

        session.pc.addEventListener('connectionstatechange', () => {
          const s = session?.pc.connectionState
          if (s === 'connected') setStatus('live')
          else if (s === 'failed' || s === 'disconnected') setStatus('error')
        })
        setStatus('live')

        {
          let lastBytes = 0
          let lastTs = 0
          // jitterBufferDelay/jitterBufferEmittedCount are cumulative since the
          // session started; diff them across the poll interval to get the
          // *current* average playout delay instead of an all-time average
          // that goes stale as the stream runs longer.
          let lastJitterDelay = 0
          let lastJitterCount = 0
          statsTimer = setInterval(async () => {
            const pc = session?.pc
            if (!pc || !onStatsRef.current) return
            const reports = await pc.getStats()
            reports.forEach((r) => {
              if (r.type === 'inbound-rtp' && r.kind === 'video') {
                const now = r.timestamp as number
                const bytes = (r.bytesReceived as number) ?? 0
                const dt = lastTs ? (now - lastTs) / 1000 : 0
                const bitrateKbps = dt > 0 ? Math.round(((bytes - lastBytes) * 8) / dt / 1000) : 0
                lastBytes = bytes
                lastTs = now

                const jitterDelay = (r.jitterBufferDelay as number) ?? 0
                const jitterCount = (r.jitterBufferEmittedCount as number) ?? 0
                const deltaCount = jitterCount - lastJitterCount
                const latencyMs =
                  deltaCount > 0
                    ? Math.round(((jitterDelay - lastJitterDelay) / deltaCount) * 1000)
                    : 0
                lastJitterDelay = jitterDelay
                lastJitterCount = jitterCount

                onStatsRef.current?.({
                  width: (r.frameWidth as number) ?? videoRef.current?.videoWidth ?? 0,
                  height: (r.frameHeight as number) ?? videoRef.current?.videoHeight ?? 0,
                  fps: Math.round((r.framesPerSecond as number) ?? 0),
                  bitrateKbps,
                  latencyMs,
                })
              }
            })
          }, 2000)
        }
      } catch (err) {
        if (!disposed) {
          console.warn('WHEP connect failed', err)
          setStatus('error')
        }
      }
    }

    connect()
    return () => {
      disposed = true
      if (statsTimer) clearInterval(statsTimer)
      ac.abort()
      session?.close()
    }
  }, [cameraId])

  return (
    <>
      <video
        ref={videoRef}
        className={className}
        autoPlay
        playsInline
        muted={muted}
        style={{ width: '100%', height: '100%', objectFit: 'cover', background: '#000' }}
      />
      {status !== 'live' && (
        <div className="av-video-offline" style={{ position: 'absolute', inset: 0 }}>
          <WifiOff size={28} />
          <span>{status === 'connecting' ? 'Connecting…' : 'Stream unavailable'}</span>
        </div>
      )}
    </>
  )
})

export default WhepVideo
