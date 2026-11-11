import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react'

// Drives one resize handle. `onMove` gets every pointer move while the handle is held (mouse and touch alike)
// and turns the pointer position into a size; the latest `onMove` is always used, so it can read fresh state.
export function useDragResize(cursor: 'col-resize' | 'row-resize', onMove: (event: PointerEvent) => void) {
  const [dragging, setDragging] = useState(false)
  const move = useRef(onMove)
  move.current = onMove

  useEffect(() => {
    if (!dragging) return
    document.body.style.cursor = cursor
    document.body.style.userSelect = 'none'

    const handleMove = (event: PointerEvent) => move.current(event)
    const stop = () => setDragging(false)
    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', stop)
    window.addEventListener('pointercancel', stop)
    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', stop)
      window.removeEventListener('pointercancel', stop)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [dragging, cursor])

  const start = useCallback((event: ReactPointerEvent) => {
    event.preventDefault()
    setDragging(true)
  }, [])

  return { dragging, start }
}
