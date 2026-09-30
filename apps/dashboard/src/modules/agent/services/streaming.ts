import { apiClient } from '@/shared/api/client'

export interface StreamToken {
  url: string // WHEP endpoint to POST an SDP offer to
  path: string // MediaMTX path, e.g. "cam_12"
  token: string // bearer token — sent as ?jwt= on the WHEP request
  expires_at: string
}

export const streamingService = {
  /** Short-lived token + WHEP URL for viewing one camera's live stream. */
  viewToken: (cameraId: string | number) =>
    apiClient.get<StreamToken>(`/streaming/cameras/${cameraId}/view-token`),
}
