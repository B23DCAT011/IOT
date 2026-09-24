import { useEffect, useMemo, useState } from 'react'
import { isAbort } from '../api/client'
import { actionApi, deviceApi } from '../api/endpoints'
import { useAuth } from '../auth/AuthContext'
import Banner from '../components/Banner'
import { DateTimeInput, EmptyState, Field, SearchInput } from '../components/Filters'
import { InfoIcon } from '../components/Icons'
import Layout from '../components/Layout'
import Pagination from '../components/Pagination'
import SortHeader from '../components/SortHeader'
import { PAGE_SIZE, PAGE_SIZE_OPTIONS } from '../config'
import { ACTION_OPTIONS, STATUS_OPTIONS } from '../constants'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { useRealtimeEvent } from '../realtime/RealtimeContext'
import ui from '../styles/ui.module.css'
import { errorChip } from '../utils/errors'
import { fmtCount, fmtDateTime, parseApproxVN } from '../utils/format'

export default function ActionHistoryPage() {
  const { auth } = useAuth()
  const [devices, setDevices] = useState([])
  const [search, setSearch] = useState('')
  const [device, setDevice] = useState('')
  const [status, setStatus] = useState('')
  const [action, setAction] = useState('')
  const [user, setUser] = useState('') // '' | 'me' | 'none'
  const [when, setWhen] = useState('') // thời điểm nhập gần đúng, xem parseApproxVN
  const [ordering, setOrdering] = useState('-created_at') // BR-09
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const debouncedSearch = useDebouncedValue(search.trim(), 400)
  // Gõ dần "29/10/2026 17:29:24" thì các bước giữa chừng cũng hợp lệ, phải chờ người dùng gõ xong.
  const debouncedWhen = useDebouncedValue(when.trim(), 400)
  const moment = useMemo(() => parseApproxVN(debouncedWhen), [debouncedWhen])
  const whenError =
    debouncedWhen && !moment
      ? 'Thời điểm chưa đúng định dạng. Ví dụ: 29/10/2026 17:29:24 — gõ thiếu giây, phút hay cả giờ đều được.'
      : null
  const hasFilter = Boolean(debouncedSearch || device || status || action || user || debouncedWhen)
  const userId = auth?.user?.id

  useEffect(() => {
    const controller = new AbortController()
    deviceApi
      .list({ signal: controller.signal })
      .then(setDevices)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (whenError) return undefined

    const params = { page, page_size: pageSize, ordering }
    if (debouncedSearch) params.search = debouncedSearch
    if (device) params.device = device
    if (status) params.status = status
    if (action) params.action = action
    // API chưa có danh sách người dùng, nên bộ lọc chỉ gồm "của tôi" và "không rõ" (05-API.md §4.6)
    if (user === 'me' && userId) params.user = userId
    if (user === 'none') params.user = 'none'
    // Gõ tới đâu lọc trọn đơn vị tới đó: cả ngày / trọn giờ / trọn phút / đúng giây.
    if (moment) {
      params.created_at__gte = moment.start
      params.created_at__lte = moment.end
    }

    const controller = new AbortController()
    setLoading(true)

    actionApi
      .list(params, { signal: controller.signal })
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err) => {
        if (isAbort(err)) return
        if (err.code === 'PAGE_NOT_FOUND') {
          setPage(1)
          return
        }
        setError(err)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [page, pageSize, ordering, debouncedSearch, device, status, action, user, userId, moment, whenError, reloadKey])

  // Bảng lịch sử không tự chèn dòng mới; chỉ cập nhật khi một dòng PENDING đang hiện kết thúc (UC-05 A2).
  useRealtimeEvent((event) => {
    if (event.type !== 'device.state') return
    const shown = data?.results?.some((row) => row.status === 'PENDING' && row.request_id === event.request_id)
    if (shown) setReloadKey((k) => k + 1)
  })

  const withPageReset = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  const clearFilters = () => {
    setSearch('')
    setDevice('')
    setStatus('')
    setAction('')
    setUser('')
    setWhen('')
    setPage(1)
  }

  const rows = data?.results ?? []
  const count = data?.count ?? 0
  const firstRow = (page - 1) * pageSize + 1
  const lastRow = firstRow + rows.length - 1

  const select = (value, setter, options, allLabel = 'Tất cả') => (
    <select className={`${ui.input} ${ui.select}`} value={value} onChange={(e) => withPageReset(setter)(e.target.value)}>
      <option value="">{allLabel}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )

  return (
    <Layout
      title="Action History"
      right={data && <div className={ui.stamp}>{fmtCount(count)} thao tác{hasFilter ? ' khớp bộ lọc' : ''}</div>}
    >
      {error && (
        <Banner chip={errorChip(error)} action="Thử lại" onAction={() => setReloadKey((k) => k + 1)}>
          Không tải được dữ liệu. {error.message}
        </Banner>
      )}

      <section className={`${ui.card} ${ui.cardGrow}`}>
        <div className={ui.filters}>
          <Field label="Tìm kiếm">
            <SearchInput value={search} onChange={withPageReset(setSearch)} placeholder="Tên hoặc mã thiết bị…" />
          </Field>
          <Field label="Thiết bị">
            {select(
              device,
              setDevice,
              devices.map((d) => ({ value: String(d.id), label: d.name })),
            )}
          </Field>
          <Field label="Trạng thái">
            {select(
              status,
              setStatus,
              STATUS_OPTIONS.map((s) => ({ value: s, label: s })),
            )}
          </Field>
          <Field label="Hành động">
            {select(
              action,
              setAction,
              ACTION_OPTIONS.map((a) => ({ value: a, label: a })),
            )}
          </Field>
          <Field label="Người thao tác">
            {select(user, setUser, [
              { value: 'me', label: 'Của tôi' },
              { value: 'none', label: 'Không rõ (—)' },
            ])}
          </Field>
          <Field label="Thời điểm">
            <DateTimeInput
              value={when}
              onChange={withPageReset(setWhen)}
              invalid={Boolean(whenError)}
              placeholder="dd/mm/yyyy hh/mm/ss"
            />
          </Field>
          <Field label="Dòng/trang">
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
          </Field>
          <button type="button" className={ui.btn} onClick={clearFilters} disabled={!hasFilter && !search}>
            Xóa bộ lọc
          </button>
        </div>

        {whenError && (
          <div className={`${ui.fNote} ${ui.fNoteBad}`} role="alert">
            <InfoIcon />
            {whenError}
          </div>
        )}


        <div className={`${ui.tbl} ${loading ? ui.loading : ''}`}>
          <table className={ui.table}>
            <colgroup>
              <col style={{ width: '6%' }} />
              <col style={{ width: '17%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '15%' }} />
              <col style={{ width: '25%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '18%' }} />
            </colgroup>
            <thead>
              <tr>
                <th className={ui.num}>
                  <SortHeader label="ID" field="id" ordering={ordering} onChange={withPageReset(setOrdering)} />
                </th>
                <th>Thiết bị</th>
                <th>
                  <SortHeader label="Hành động" field="action" ordering={ordering} onChange={withPageReset(setOrdering)} />
                </th>
                <th>Người thao tác</th>
                <th>
                  <SortHeader label="Trạng thái" field="status" ordering={ordering} onChange={withPageReset(setOrdering)} />
                </th>
                <th className={ui.num}>Độ trễ</th>
                <th>
                  <SortHeader
                    label="Thời gian"
                    field="created_at"
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
                    <td>
                      <span className={ui.code}>{row.device.code}</span>
                      <div className={ui.sub}>{row.device.name}</div>
                    </td>
                    <td className={ui.act}>{row.action}</td>
                    {/* user = null thì hiện "—", KHÔNG ghi "Hệ thống"/"Ẩn danh" (BR-12) */}
                    <td className={row.user ? undefined : ui.nil}>{row.user ? row.user.full_name : '—'}</td>
                    <td>
                      <span className={`${ui.pill} ${ui[`pill${row.status}`] ?? ''}`}>{row.status}</span>
                      {row.error_message && <div className={ui.errline}>{row.error_message}</div>}
                    </td>
                    <td className={`${ui.num} ${row.latency_ms == null ? ui.nil : ''}`}>
                      {row.latency_ms == null ? '—' : `${fmtCount(row.latency_ms)} ms`}
                    </td>
                    <td className={ui.mono}>{fmtDateTime(row.created_at)}</td>
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
              {hasFilter ? ' khớp bộ lọc' : ''}
            </span>
            <Pagination page={page} pageSize={pageSize} count={count} onChange={setPage} />
          </div>
        )}
      </section>
    </Layout>
  )
}
