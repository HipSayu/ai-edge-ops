/**
 * Minimal WHEP (WebRTC-HTTP Egress Protocol) client for viewing a MediaMTX
 * stream in a plain <video> element.
 *
 * MediaMTX terminates ICE itself and returns a complete answer, so we gather
 * all local candidates before POSTing the offer (non-trickle) — the simplest
 * path that works against a public server behind NAT.
 */

function iceGatheringComplete(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise((resolve) => {
    const check = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', check)
        resolve()
      }
    }
    pc.addEventListener('icegatheringstatechange', check)
    setTimeout(resolve, 3000) // MediaMTX is fast; don't hang on a stuck candidate
  })
}

export interface WhepSession {
  readonly pc: RTCPeerConnection
  close(): void
}

export async function playWhep(
  video: HTMLVideoElement,
  url: string,
  token: string,
  signal?: AbortSignal,
): Promise<WhepSession> {
  const pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  })

  const close = () => {
    try {
      pc.getReceivers().forEach((r) => r.track?.stop())
    } catch {
      /* ignore */
    }
    pc.close()
    if (video.srcObject) video.srcObject = null
  }
  signal?.addEventListener('abort', close, { once: true })

  pc.addTransceiver('video', { direction: 'recvonly' })

  pc.ontrack = (event) => {
    const stream = event.streams[0] ?? new MediaStream([event.track])
    if (video.srcObject !== stream) {
      video.srcObject = stream
      void video.play().catch(() => {})
    }
  }
  pc.addEventListener('connectionstatechange', () => {
    if (pc.connectionState === 'connected') void video.play().catch(() => {})
  })

  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)
  await iceGatheringComplete(pc)
  if (signal?.aborted) {
    close()
    throw new DOMException('aborted', 'AbortError')
  }

  const sep = url.includes('?') ? '&' : '?'
  const res = await fetch(`${url}${sep}jwt=${encodeURIComponent(token)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/sdp' },
    body: pc.localDescription?.sdp ?? offer.sdp,
    signal,
  })
  if (!res.ok) {
    close()
    throw new Error(`WHEP handshake failed: ${res.status}`)
  }

  const answer = await res.text()
  await pc.setRemoteDescription({ type: 'answer', sdp: answer })

  return { pc, close }
}
