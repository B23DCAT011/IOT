import { useEffect, useMemo, useState } from 'react'
import { isAbort } from '../api/client'
import { sensorApi } from '../api/endpoints'
import Banner from '../components/Banner'
import { EmptyState, Field } from '../components/Filters'
import { InfoIcon, SearchIcon } from '../components/Icons'
import Layout from '../components/Layout'
import Pagination from '../components/Pagination'
import SortHeader from '../components/SortHeader'
import { PAGE_SIZE, PAGE_SIZE_OPTIONS } from '../config'
import ui from '../styles/ui.module.css'
import { errorChip } from '../utils/errors'
import { fmtCount, fmtDateTime, fmtValue, parseApproxVN } from '../utils/format'

const FIELD_ALL = ''
const FIELD_TIME = 'time'

function firstMessage(details, ...keys) {
  for (const key of keys) {
    const value = details?.[key]
    if (value) return Array.isArray(value) ? value[0] : String(value)
  }
  return null
}

/**
 * Dịch lựa chọn "Tìm theo" + chuỗi đã gõ thành tham số của GET /api/sensors.
 * Trả về { params } hoặc { error } — sai định dạng thì chặn ngay ở giao diện,
 * không gọi API (UC-04 E2).
 */
function buildQuery({ field, term }) {
  if (field === FIELD_TIME) {
    if (!term) return { params: {} }
    // Gõ tới đâu lọc trọn đơn vị tới đó: cả ngày / trọn giờ / trọn phút / đúng giây.
    const moment = parseApproxVN(term)
    if (!moment) {
      return {
        error:
          'Thời gian chưa đúng định dạng. Ví dụ: 17/08/2026 10:55:00 — gõ thiếu giây, phút hay cả giờ đều được.',
      }
    }
    return { params: { recorded_at__gte: moment.start, recorded_at__lte: moment.end } }
  }

  // "Tất cả": SearchFilter của DRF chỉ khớp cột chuỗi — mã và tên cảm biến.
  if (field === FIELD_ALL) return { params: term ? { search: term } : {} }

  // Còn lại là mã một cảm biến; ô giá trị để trống thì chỉ lọc theo cảm biến đó.
  if (!term) return { params: { sensor: field } }
  const value = Number(term.replace(',', '.'))
  if (!Number.isFinite(value)) return { error: 'Giá trị tìm kiếm phải là một số. Ví dụ: 29.4' }
  return { params: { sensor: field, value__gte: value, value__lte: value } }
}

export default function DataSensorPage() {
  const [catalog, setCatalog] = useState([])
  const [field, setField] = useState(FIELD_ALL) // cột đang chọn ở ô "Tìm theo"
  const [term, setTerm] = useState('') // chuỗi đang gõ, CHƯA áp dụng
  const [query, setQuery] = useState({ field: FIELD_ALL, term: '' }) // bộ lọc ĐÃ áp dụng
  const [formError, setFormError] = useState(null)
  const [ordering, setOrdering] = useState('-recorded_at') // BR-09
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [serverErrors, setServerErrors] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    sensorApi
      .catalog({ signal: controller.signal })
      .then(setCatalog)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  const catalogById = useMemo(() => new Map(catalog.map((item) => [item.id, item])), [catalog])
  const selected = catalog.find((item) => item.code === field)
  const built = useMemo(() => buildQuery(query), [query])

  const searchError =
    formError ??
    firstMessage(serverErrors, 'search', 'sensor', 'value__gte', 'value__lte', 'recorded_at__gte', 'recorded_at__lte')
  // Đang lọc hay không là theo tham số THẬT SỰ gửi lên, không theo ô đang chọn:
  // "Thời gian" mà chưa gõ mốc nào thì vẫn là toàn bộ bảng.
  const hasFilter = Object.keys(built.params ?? {}).length > 0

  // Gợi ý trong ô giá trị đổi theo cột đang chọn — khỏi phải đoán gõ gì.
  let placeholder = 'Nhập mã hoặc tên cảm biến'
  if (field === FIELD_TIME) placeholder = 'dd/mm/yyyy hh:mm:ss'
  else if (field !== FIELD_ALL) placeholder = `Nhập giá trị${selected ? ` (${selected.unit})` : ''}`

  useEffect(() => {
    if (built.error) return undefined

    const params = { page, page_size: pageSize, ordering, ...built.params }

    const controller = new AbortController()
    setLoading(true)

    sensorApi
      .list(params, { signal: controller.signal })
      .then((result) => {
        setData(result)
        setError(null)
        setServerErrors(null)
      })
      .catch((err) => {
        if (isAbort(err)) return
        // Vượt số trang: coi là rỗng, quay về trang 1 (05-API.md §2.8, UC-03 A2).
        if (err.code === 'PAGE_NOT_FOUND') {
          setPage(1)
          return
        }
        if (err.code === 'INVALID_RANGE' || err.code === 'VALIDATION_ERROR') {
          setServerErrors(err.details ?? {})
          setError(null)
          return
        }
        setError(err)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [page, pageSize, ordering, built, reloadKey])

  const withPageReset = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  /**
   * Đổi cột CHƯA lọc — bảng giữ nguyên kết quả cũ cho tới khi bấm Tìm.
   * Chuỗi cũ bị xoá: "29.4" của Nhiệt độ vô nghĩa ở cột khác.
   */
  const changeField = (value) => {
    setField(value)
    setTerm('')
    setFormError(null)
    setServerErrors(null)
  }

  // Chỉ bấm Tìm (hoặc Enter) mới gọi API — gõ không làm bảng đổi.
  const submitSearch = (event) => {
    event.preventDefault()
    const next = { field, term: term.trim() }
    const check = buildQuery(next)
    if (check.error) {
      setFormError(check.error)
      return
    }
    setFormError(null)
    setServerErrors(null)
    setPage(1)
    setQuery(next)
  }

  const clearFilters = () => {
    setField(FIELD_ALL)
    setTerm('')
    setFormError(null)
    setServerErrors(null)
    setPage(1)
    setQuery({ field: FIELD_ALL, term: '' })
  }

  const rows = data?.results ?? []
  const count = data?.count ?? 0
  const firstRow = (page - 1) * pageSize + 1
  const lastRow = firstRow + rows.length - 1

  return (
    <Layout
      title="Data Sensor"
      right={data && <div className={ui.stamp}>{fmtCount(count)} bản ghi{hasFilter ? ' khớp bộ lọc' : ''}</div>}
    >
      {error && (
        <Banner chip={errorChip(error)} action="Thử lại" onAction={() => setReloadKey((k) => k + 1)}>
          Không tải được dữ liệu. {error.message}
        </Banner>
      )}

      <section className={`${ui.card} ${ui.cardGrow}`}>
        <form className={ui.filters} onSubmit={submitSearch}>
          <Field label="Tìm theo">
            <select
              className={`${ui.input} ${ui.select}`}
              value={field}
              onChange={(e) => changeField(e.target.value)}
            >
              <option value={FIELD_ALL}>Tất cả</option>
              {catalog.map((item) => (
                <option key={item.id} value={item.code}>
                  {item.name}
                </option>
              ))}
              <option value={FIELD_TIME}>Thời gian</option>
            </select>
          </Field>
          <Field label="Giá trị tìm kiếm" grow>
            <input
              type="text"
              autoComplete="off"
              className={`${ui.input} ${searchError ? ui.invalid : ''}`}
              value={term}
              placeholder={placeholder}
              onChange={(e) => setTerm(e.target.value)}
            />
          </Field>
          <button type="submit" className={`${ui.btn} ${ui.btnPrimary}`}>
            <SearchIcon />
            Tìm
          </button>
          <button type="button" className={ui.btn} onClick={clearFilters} disabled={!hasFilter && !term && field === FIELD_ALL}>
            Xóa bộ lọc
          </button>
        </form>

        {searchError && (
          <div className={`${ui.fNote} ${ui.fNoteBad}`} role="alert">
            <InfoIcon />
            {searchError}
          </div>
        )}


        <div className={`${ui.tbl} ${loading ? ui.loading : ''}`}>
          <table className={ui.table}>
            <colgroup>
              <col style={{ width: '8%' }} />
              <col style={{ width: '20%' }} />
              <col style={{ width: '20%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '29%' }} />
            </colgroup>
            <thead>
              <tr>
                <th className={ui.num}>
                  <SortHeader label="ID" field="id" ordering={ordering} onChange={withPageReset(setOrdering)} />
                </th>
                <th>Mã cảm biến</th>
                <th>Cảm biến</th>
                <th className={ui.num}>
                  <SortHeader label="Giá trị" field="value" ordering={ordering} onChange={withPageReset(setOrdering)} />
                </th>
                <th>Đơn vị</th>
                <th>
                  <SortHeader
                    label="Thời gian"
                    field="recorded_at"
                    ordering={ordering}
                    onChange={withPageReset(setOrdering)}
                  />
                </th>
              </tr>
            </thead>
            {rows.length > 0 && (
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td className={ui.num}>{row.id}</td>
                    <td className={ui.mono}>{row.sensor.code}</td>
                    <td>{row.sensor.name}</td>
                    <td className={ui.num}>{fmtValue(row.value, catalogById.get(row.sensor.id)?.metric_type)}</td>
                    <td>{row.sensor.unit}</td>
                    <td className={ui.mono}>{fmtDateTime(row.recorded_at)}</td>
                  </tr>
                ))}
              </tbody>
            )}
          </table>
          {data && rows.length === 0 && <EmptyState filtered={hasFilter} onClear={clearFilters} />}
        </div>

        {rows.length > 0 && (
          <div className={ui.tfoot}>
            <span>
              Hiển thị {fmtCount(firstRow)}–{fmtCount(lastRow)} trong {fmtCount(count)} bản ghi
              {hasFilter ? ' khớp bộ lọc' : catalog.length ? ` · ${catalog.length} dòng mỗi chu kỳ` : ''}
            </span>
            <div className={ui.tfootRight}>
              <label className={ui.pageSize}>
                Dòng/trang
                <select
                  className={`${ui.input} ${ui.select} ${ui.selectNarrow}`}
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value))
                    setPage(1) // đổi cỡ trang thì số trang cũ có thể vượt quá số trang mới
                  }}
                >
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
              <Pagination page={page} pageSize={pageSize} count={count} onChange={setPage} />
            </div>
          </div>
        )}
      </section>
    </Layout>
  )
}
