// Biểu tượng SVG lấy nguyên từ docs/wireframe/*.html.
const stroke = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'aria-hidden': 'true',
  focusable: 'false',
}

export function NavIcon({ name }) {
  switch (name) {
    case 'dashboard':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <rect x="3" y="3" width="7" height="9" />
          <rect x="14" y="3" width="7" height="5" />
          <rect x="14" y="12" width="7" height="9" />
          <rect x="3" y="16" width="7" height="5" />
        </svg>
      )
    case 'sensor':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <path d="M3 3v18h18" />
          <path d="M7 15l4-5 3 3 5-7" />
        </svg>
      )
    case 'history':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <path d="M12 8v4l3 2" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      )
    case 'profile':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
        </svg>
      )
    default:
      return null
  }
}

export function DeviceIcon({ type }) {
  if (type === 'FAN') {
    return (
      <svg {...stroke} strokeWidth="1.7">
        <circle cx="12" cy="12" r="2" />
        <path d="M12 10c0-4 1-7 3-7s2 4-1 6M14 12c4 0 7 1 7 3s-4 2-6-1M12 14c0 4-1 7-3 7s-2-4 1-6M10 12c-4 0-7-1-7-3s4-2 6 1" />
      </svg>
    )
  }
  if (type === 'LIGHT') {
    return (
      <svg {...stroke} strokeWidth="1.7">
        <path d="M9 18h6M10 21h4" />
        <path d="M12 3a6 6 0 0 0-3.5 10.9V15h7v-1.1A6 6 0 0 0 12 3z" />
      </svg>
    )
  }
  return (
    <svg {...stroke} strokeWidth="1.7">
      <path d="M12 3v8" />
      <path d="M7.5 6.5a7 7 0 1 0 9 0" />
    </svg>
  )
}

export function LinkIcon({ name }) {
  switch (name) {
    case 'github':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <path d="M9 19c-4 1.5-4-2.5-6-3m12 5v-3.9c0-1.1.1-1.5-.6-2.1 3-.3 5.6-1.5 5.6-6a4.7 4.7 0 0 0-1.3-3.2 4.3 4.3 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.4 5.4 2.7 5.4 2.7a4.3 4.3 0 0 0-.1 3.2A4.7 4.7 0 0 0 4 9.1c0 4.5 2.6 5.7 5.6 6-.7.6-.7 1.2-.6 2.1V21" />
        </svg>
      )
    case 'file':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <path d="M14 3v5h5" />
          <path d="M14 3H6v18h12V8z" />
          <path d="M9 13h6M9 17h4" />
        </svg>
      )
    case 'figma':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <circle cx="12" cy="12" r="3" />
          <path d="M9 3h3v6H9a3 3 0 0 1 0-6zM12 3h3a3 3 0 0 1 0 6h-3M9 9h3v6H9a3 3 0 0 1 0-6zM9 15h3v3a3 3 0 1 1-3-3z" />
        </svg>
      )
    case 'code':
      return (
        <svg {...stroke} strokeWidth="1.8">
          <path d="M8 6l-5 6 5 6M16 6l5 6-5 6" />
        </svg>
      )
    default:
      return null
  }
}

export const SearchIcon = () => (
  <svg {...stroke} strokeWidth="2">
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.5-3.5" />
  </svg>
)

export const InfoIcon = () => (
  <svg {...stroke} strokeWidth="2">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8h.01M11 12h1v5h1" />
  </svg>
)

export const LogoutIcon = () => (
  <svg {...stroke} strokeWidth="1.8">
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    <path d="M10 17l-5-5 5-5" />
    <path d="M5 12h11" />
  </svg>
)

export const SortBothIcon = () => (
  <svg {...stroke} strokeWidth="2.6">
    <path d="M7 10l5-5 5 5M7 14l5 5 5-5" />
  </svg>
)

export const SortDownIcon = () => (
  <svg {...stroke} strokeWidth="2.4">
    <path d="M6 15l6 6 6-6" />
  </svg>
)

export const SortUpIcon = () => (
  <svg {...stroke} strokeWidth="2.4">
    <path d="M6 9l6-6 6 6" />
  </svg>
)

export const CalendarIcon = () => (
  <svg {...stroke} strokeWidth="1.8">
    <rect x="3" y="5" width="18" height="16" rx="1.5" />
    <path d="M3 10h18M8 3v4M16 3v4" />
  </svg>
)
