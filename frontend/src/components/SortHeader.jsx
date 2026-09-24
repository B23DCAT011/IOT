import ui from '../styles/ui.module.css'
import { SortBothIcon, SortDownIcon, SortUpIcon } from './Icons'

// Bấm cột chưa sắp xếp → giảm dần; bấm lại → tăng dần (tham số `ordering` của DRF, 05-API.md §2.8).
export default function SortHeader({ label, field, ordering, onChange }) {
  const active = ordering === field || ordering === `-${field}`
  const desc = ordering === `-${field}`
  const next = active && desc ? field : `-${field}`

  return (
    <button
      type="button"
      className={active ? ui.sortcap : ui.sortable}
      onClick={() => onChange(next)}
      aria-sort={active ? (desc ? 'descending' : 'ascending') : 'none'}
    >
      {label}
      {active ? desc ? <SortDownIcon /> : <SortUpIcon /> : <SortBothIcon />}
    </button>
  )
}
