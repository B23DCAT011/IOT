import ui from '../styles/ui.module.css'

// Trang 1 trong 3614 → ‹ 1 2 3 … 3614 › — đúng như bản vẽ.
function pageItems(page, last) {
  const set = new Set([1, last, page - 1, page, page + 1])
  if (page <= 2) {
    set.add(2)
    set.add(3)
  }
  if (page >= last - 1) {
    set.add(last - 1)
    set.add(last - 2)
  }
  const numbers = [...set].filter((n) => n >= 1 && n <= last).sort((a, b) => a - b)
  const items = []
  numbers.forEach((n, i) => {
    if (i > 0 && n - numbers[i - 1] > 1) items.push(`gap-${n}`)
    items.push(n)
  })
  return items
}

export default function Pagination({ page, pageSize, count, onChange }) {
  const last = Math.max(1, Math.ceil(count / pageSize))

  return (
    <nav className={ui.pager} aria-label="Phân trang">
      <button
        type="button"
        className={ui.pg}
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        aria-label="Trang trước"
      >
        ‹
      </button>
      {pageItems(page, last).map((item) =>
        typeof item === 'string' ? (
          <span key={item} className={`${ui.pg} ${ui.pgMute}`}>
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            className={`${ui.pg} ${item === page ? ui.pgOn : ''}`}
            onClick={() => item !== page && onChange(item)}
            aria-current={item === page ? 'page' : undefined}
          >
            {item}
          </button>
        ),
      )}
      <button
        type="button"
        className={ui.pg}
        disabled={page >= last}
        onClick={() => onChange(page + 1)}
        aria-label="Trang sau"
      >
        ›
      </button>
    </nav>
  )
}
