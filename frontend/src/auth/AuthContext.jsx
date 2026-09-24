import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { setApiToken, setUnauthorizedHandler } from '../api/client'
import { authApi } from '../api/endpoints'
import { storage } from '../utils/storage'

const STORAGE_KEY = 'room01.auth'
const AuthContext = createContext(null)

function readStored() {
  const value = storage.get(STORAGE_KEY)
  return value?.token && value?.user ? value : null
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    const stored = readStored()
    setApiToken(stored?.token ?? null)
    return stored
  })
  const [expired, setExpired] = useState(false)

  const clear = useCallback(() => {
    setApiToken(null)
    storage.remove(STORAGE_KEY)
    setAuth(null)
  }, [])

  const login = useCallback(async (username, password) => {
    const result = await authApi.login(username, password)
    setApiToken(result.token)
    storage.set(STORAGE_KEY, result)
    setExpired(false)
    setAuth(result)
    return result
  }, [])

  // Về trang đăng nhập ngay, kể cả khi lời gọi đăng xuất thất bại (05-API.md §4.9).
  const logout = useCallback(() => {
    const token = auth?.token
    clear()
    setExpired(false)
    if (token) authApi.logout(token).catch(() => { })
  }, [auth, clear])

  // REST nhận 401 hoặc WebSocket đóng mã 4401 (05-API.md §5.4 quy tắc 6, 7).
  const expireSession = useCallback(() => {
    clear()
    setExpired(true)
  }, [clear])

  useEffect(() => {
    setUnauthorizedHandler(expireSession)
    return () => setUnauthorizedHandler(null)
  }, [expireSession])

  // Mỗi tài khoản chỉ có một token dùng chung (05-API.md §4.8):
  // tab khác đăng nhập / đăng xuất thì tab này theo luôn.
  useEffect(() => {
    const onStorage = (event) => {
      if (event.key !== STORAGE_KEY) return
      const stored = readStored()
      setApiToken(stored?.token ?? null)
      setAuth(stored)
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const value = useMemo(
    () => ({ auth, expired, login, logout, expireSession }),
    [auth, expired, login, logout, expireSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải được gọi bên trong AuthProvider')
  return ctx
}

// Chưa đăng nhập thì chỉ thấy trang Login; đăng nhập xong quay về đúng trang đang xem.
export function RequireAuth({ children }) {
  const { auth } = useAuth()
  const location = useLocation()
  if (!auth) return <Navigate to="/login" replace state={{ from: location }} />
  return children
}
