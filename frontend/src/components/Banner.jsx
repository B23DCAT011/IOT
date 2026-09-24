import ui from '../styles/ui.module.css'

// Dải thông báo lỗi dùng chung một khuôn (docs/wireframe/05-trang-thai.html, khung 5).
export default function Banner({ chip, children, action, onAction }) {
  return (
    <div className={ui.banner} role="status">
      <span className={ui.chip}>{chip}</span>
      <span className={ui.bannerText}>{children}</span>
      {action && (
        <button type="button" className={ui.bannerBtn} onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  )
}
