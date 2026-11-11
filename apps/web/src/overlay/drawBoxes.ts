export interface OverlayBox {
  label: string
  confidence: number
  box: [number, number, number, number] // x1, y1, x2, y2 in the pixels of the frame
  trackId: number | null
}

// Colours follow the meaning of the box, as on a control panel: a missing item is an alarm, worn gear is normal.
const ALARM = '#e5484d'
const NORMAL = '#3fb55f'
const PERSON = '#4a9fd8'

function colourOf(label: string): string {
  if (label.startsWith('no_')) return ALARM
  return label === 'person' ? PERSON : NORMAL
}

// Draws the boxes over a video drawn with object-fit: cover, so it is scaled to the larger ratio and cropped evenly.
// `frame` is the size of the frame the boxes are in.
export function drawBoxes(
  ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D,
  width: number,
  height: number,
  frame: { w: number; h: number },
  boxes: OverlayBox[],
) {
  if (!frame.w || !frame.h) return
  const scale = Math.max(width / frame.w, height / frame.h)
  const offsetX = (width - frame.w * scale) / 2
  const offsetY = (height - frame.h * scale) / 2
  ctx.font = '600 11px "IBM Plex Mono", ui-monospace, monospace'
  ctx.textBaseline = 'top'

  // People first, then worn gear, alarms last: a missing item is never hidden under the box of the person it belongs to
  const rank = (label: string) => (label === 'person' ? 0 : label.startsWith('no_') ? 2 : 1)
  const ordered = [...boxes].sort((a, b) => rank(a.label) - rank(b.label))
  for (const { label, confidence, box, trackId } of ordered) {
    const colour = colourOf(label)
    const x = box[0] * scale + offsetX
    const y = box[1] * scale + offsetY
    const w = (box[2] - box[0]) * scale
    const h = (box[3] - box[1]) * scale
    ctx.lineWidth = label.startsWith('no_') || label === 'person' ? 2 : 1
    ctx.strokeStyle = colour
    ctx.strokeRect(x, y, w, h)
    // A tracked person is named by the id the edge follows them by, like a tracker's output
    const text =
      label === 'person'
        ? trackId == null
          ? `PERSON ${Math.round(confidence * 100)}%`
          : `ID ${trackId}`
        : `${label.replace('no_', 'NO ').toUpperCase()} ${Math.round(confidence * 100)}%${trackId == null ? '' : ` #${trackId}`}`
    const pad = 3
    const textWidth = ctx.measureText(text).width
    const top = y - 15 < 0 ? y : y - 15
    ctx.fillStyle = colour
    ctx.fillRect(x, top, textWidth + pad * 2, 15)
    ctx.fillStyle = '#ffffff'
    ctx.fillText(text, x + pad, top + 2)
  }
}
