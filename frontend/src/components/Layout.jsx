import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { OFFLINE_AFTER_MS } from '../config'
import { ROLE_LABEL } from '../constants'
import { useRealtimeEvent } from '../realtime/RealtimeContext'
import { LogoutIcon, NavIcon } from './Icons'
import styles from './Layout.module.css'

const NAV = [
  { to: '/', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/data-sensor', label: 'Data Sensor', icon: 'sensor' },
  { to: '/action-history', label: 'Action History', icon: 'history' },
  { to: '/profile', label: 'Profile', icon: 'profile' },
]

// Số cảm biến đang vượt ngưỡng theo sự kiện sensor.data gần nhất — để trang nào cũng thấy
// chấm đỏ cạnh mục Dashboard. Quá 30 giây không có sự kiện (BR-07) thì thôi báo: số đo đã cũ.
function useAlertCount() {
  const [count, setCount] = useState(0)
  const staleTimer = useRef(null)

  useRealtimeEvent((event) => {
    if (event.type !== 'sensor.data' || !event.alerts) return
    setCount(Object.values(event.alerts).filter(Boolean).length)
    clearTimeout(staleTimer.current)
    staleTimer.current = setTimeout(() => setCount(0), OFFLINE_AFTER_MS)
  })
  useEffect(() => () => clearTimeout(staleTimer.current), [])
  return count
}

export default function Layout({ title, right, children }) {
  const { auth, logout } = useAuth()
  const user = auth?.user
  const alertCount = useAlertCount()

  return (
    <div className={styles.app}>
      <aside className={styles.side}>
        <div className={styles.brand}>
          <div className={styles.brandName}>Room01 Monitor</div>
          <div className={styles.brandSub}>ESP8266 · PHÒNG 01</div>
        </div>

        <nav className={styles.nav}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.on : ''}`}
            >
              <NavIcon name={item.icon} />
              {item.label}
              {item.to === '/' && alertCount > 0 && (
                <span className={styles.navAlert} title={`${alertCount} cảm biến đang vượt ngưỡng`}>
                  {alertCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className={styles.spacer} />

        {user && (
          <div className={styles.user}>
            <div className={styles.userMeta}>
              <div className={styles.userName}>{user.full_name || user.username}</div>
              <div className={styles.userRole}>
                {user.username} · {ROLE_LABEL[user.role] ?? user.role}
              </div>
            </div>
            <button
              type="button"
              className={styles.logout}
              onClick={logout}
              title="Đăng xuất"
              aria-label="Đăng xuất"
            >
              <LogoutIcon />
            </button>
          </div>
        )}

      </aside>

      <div className={styles.main}>
        <header className={styles.topbar}>
          <h1 className={styles.title}>{title}</h1>
          <div className={styles.topbarRight}>{right}</div>
        </header>
        <main className={styles.body}>{children}</main>
      </div>
    </div>
  )
}
