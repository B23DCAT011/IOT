import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { WS_CLOSE_UNAUTHORIZED, WS_RETRY_MS, WS_URL } from '../config'

const RealtimeContext = createContext(null)

/**
 * Một kết nối WebSocket cho cả ứng dụng (05-API.md §5).
 * - status: 'connecting' | 'open' | 'closed'
 * - generation: tăng mỗi lần kết nối thành công; trang nào cần bù khoảng trống
 *   sau khi mất kết nối thì tải lại khi giá trị này đổi (§5.4 quy tắc 2).
 */
export function RealtimeProvider({ children }) {
  const { auth, expireSession } = useAuth()
  const token = auth?.token
  const listeners = useRef(new Set())
  const reconnectRef = useRef(() => {})
  const [status, setStatus] = useState('connecting')
  const [generation, setGeneration] = useState(0)

  useEffect(() => {
    if (!token) return undefined

    let disposed = false
    let socket = null
    let retryTimer = null

    const open = () => {
      clearTimeout(retryTimer)
      setStatus('connecting')

      // Trình duyệt không đặt được header cho WebSocket nên token đi trên URL (§5.1).
      const url = new URL(WS_URL)
      url.searchParams.set('token', token)
      socket = new WebSocket(url)

      socket.onopen = () => {
        if (disposed) return
        setStatus('open')
        setGeneration((g) => g + 1)
      }

      socket.onmessage = (message) => {
        let event
        try {
          event = JSON.parse(message.data)
        } catch {
          return
        }
        listeners.current.forEach((listener) => listener(event))
      }

      socket.onclose = (closeEvent) => {
        if (disposed) return
        socket = null
        setStatus('closed')
        // Sai token: KHÔNG thử lại, về trang đăng nhập (§5.4 quy tắc 6).
        if (closeEvent.code === WS_CLOSE_UNAUTHORIZED) {
          expireSession()
          return
        }
        retryTimer = setTimeout(open, WS_RETRY_MS)
      }
    }

    reconnectRef.current = () => {
      if (!socket) open()
    }
    open()

    return () => {
      disposed = true
      clearTimeout(retryTimer)
      if (socket) {
        socket.onclose = null
        socket.close(1000)
      }
    }
  }, [token, expireSession])

  const subscribe = useCallback((listener) => {
    listeners.current.add(listener)
    return () => listeners.current.delete(listener)
  }, [])

  const reconnectNow = useCallback(() => reconnectRef.current(), [])

  const value = useMemo(
    () => ({ status, generation, subscribe, reconnectNow }),
    [status, generation, subscribe, reconnectNow],
  )

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext)
  if (!ctx) throw new Error('useRealtime phải được gọi bên trong RealtimeProvider')
  return ctx
}

// Đăng ký nhận sự kiện; handler luôn là bản mới nhất nên đọc được state hiện tại.
export function useRealtimeEvent(handler) {
  const { subscribe } = useRealtime()
  const handlerRef = useRef(handler)

  useEffect(() => {
    handlerRef.current = handler
  })

  useEffect(() => subscribe((event) => handlerRef.current(event)), [subscribe])
}
