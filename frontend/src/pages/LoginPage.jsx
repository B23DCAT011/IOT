import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { USE_MOCK } from '../config'
import ui from '../styles/ui.module.css'
import s from './Login.module.css'

export default function LoginPage() {
  const { auth, expired, login } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // Đăng nhập xong quay về đúng trang đang xem trước khi bị đẩy ra (05-API.md §5.4 quy tắc 7).
  const from = location.state?.from
  const target = from ? `${from.pathname}${from.search ?? ''}` : '/'

  if (auth) return <Navigate to={target} replace />

  const onSubmit = async (event) => {
    event.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError(null)
    try {
      // Không cắt khoảng trắng của mật khẩu (05-API.md §4.8).
      await login(username.trim(), password)
      navigate(target, { replace: true })
    } catch (err) {
      // INVALID_CREDENTIALS: cùng một thông báo cho sai tên / sai mật khẩu / tài khoản khóa.
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <div className={s.page}>
      <div className={s.panel}>
        <div className={s.brand}>
          <div className={s.brandName}>Room01 Monitor</div>
          <div className={s.brandSub}>ESP8266 · PHÒNG 01</div>
        </div>

        <form className={s.form} onSubmit={onSubmit} noValidate>
          <div>
            <h1 className={s.title}>Đăng nhập</h1>
            <p className={s.lead}>Hệ thống giám sát và điều khiển môi trường phòng</p>
          </div>

          {expired && !error && (
            <div className={s.notice} role="status">
              Phiên đăng nhập đã hết. Vui lòng đăng nhập lại.
            </div>
          )}
          {error && (
            <div className={s.error} role="alert">
              {error}
            </div>
          )}

          <label className={s.field}>
            <span className={s.label}>Tên đăng nhập</span>
            <input
              className={ui.input}
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>

          <label className={s.field}>
            <span className={s.label}>Mật khẩu</span>
            <input
              className={ui.input}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          <button
            type="submit"
            className={`${ui.btn} ${ui.btnPrimary} ${s.submit}`}
            disabled={submitting || !username.trim() || !password}
          >
            {submitting ? 'Đang đăng nhập…' : 'Đăng nhập'}
          </button>
        </form>

        {USE_MOCK && (
          <div className={s.mockHint}>
            Đang dùng <b>dữ liệu giả (MSW)</b>. Tài khoản <code>admin</code> hoặc <code>operator</code>, mật khẩu{' '}
            <code>doi-mat-khau-nay</code>.
          </div>
        )}
      </div>
    </div>
  )
}
