import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ROLE_LABEL } from '../constants'
import { LogoutIcon, NavIcon } from './Icons'
import styles from './Layout.module.css'

const NAV = [
  { to: '/', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/data-sensor', label: 'Data Sensor', icon: 'sensor' },
  { to: '/action-history', label: 'Action History', icon: 'history' },
  { to: '/profile', label: 'Profile', icon: 'profile' },
]

export default function Layout({ title, right, children }) {
  const { auth, logout } = useAuth()
  const user = auth?.user

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
