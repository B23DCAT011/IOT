import { useEffect, useMemo, useState } from 'react'
import { isAbort } from '../api/client'
import { sensorApi } from '../api/endpoints'
import Banner from '../components/Banner'
import { DateTimeInput, EmptyState, Field, SearchInput } from '../components/Filters'
import { InfoIcon } from '../components/Icons'
import Layout from '../components/Layout'
import Pagination from '../components/Pagination'
import SortHeader from '../components/SortHeader'
import { PAGE_SIZE, PAGE_SIZE_OPTIONS } from '../config'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import ui from '../styles/ui.module.css'
import { errorChip } from '../utils/errors'
import { fmtCount, fmtDateTime, fmtValue, parseApproxVN } from '../utils/format'

const DEBOUNCE_MS = 400

function firstMessage(details, ...keys) {
  for (const key of keys) {
    const value = details?.[key]
    if (value) return Array.isArray(value) ? value[0] : String(value)
  }
  return null
}

export default function DataSensorPage() {
  const [catalog, setCatalog] = useState([])
  const [search, setSearch] = useState('')
  const [sensor, setSensor] = useState('')
  const [valueFrom, setValueFrom] = useState('')
  const [valueTo, setValueTo] = useState('')
  const [when, setWhen] = useState('') // thời điểm nhập gần đúng, xem parseApproxVN
  const [ordering, setOrdering] = useState('-recorded_at') // BR-09
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [serverErrors, setServerErrors] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const debouncedSearch = useDebouncedValue(search.trim(), DEBOUNCE_MS)
  const debouncedFrom = useDebouncedValue(valueFrom, DEBOUNCE_MS)
  const debouncedTo = useDebouncedValue(valueTo, DEBOUNCE_MS)
  // Gõ dần "29/10/2026 17:29:24" thì các bước giữa chừng cũng hợp lệ, phải chờ người dùng gõ xong.
  const debouncedWhen = useDebouncedValue(when.trim(), DEBOUNCE_MS)
  const moment = useMemo(() => parseApproxVN(debouncedWhen), [debouncedWhen])

  useEffect(() => {
    const controller = new AbortController()
    sensorApi
      .catalog({ signal: controller.signal })
      .then(setCatalog)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  const catalogById = useMemo(() => new Map(catalog.map((item) => [item.id, item])), [catalog])
  const selectedSensor = catalog.find((item) => item.code === sensor)

  // UC-04 E2 — chặn ngay ở giao diện, không cần đợi máy chủ trả INVALID_RANGE.
  const valueError =
    sensor && debouncedFrom !== '' && debouncedTo !== '' && Number(debouncedFrom) > Number(debouncedTo)
      ? 'Giá trị đầu khoảng phải nhỏ hơn hoặc bằng giá trị cuối khoảng.'
      : firstMessage(serverErrors, 'value__gte', 'value__lte')
  const whenError =
    debouncedWhen && !moment
      ? 'Thời điểm chưa đúng định dạng. Ví dụ: 29/10/2026 17:29:24 — gõ thiếu giây, phút hay cả giờ đều được.'
      : firstMessage(serverErrors, 'recorded_at__gte', 'recorded_at__lte')
  const blockedLocally =
    Boolean(sensor && debouncedFrom !== '' && debouncedTo !== '' && Number(debouncedFrom) > Number(debouncedTo)) ||
    Boolean(debouncedWhen && !moment)

  const hasFilter = Boolean(debouncedSearch || sensor || debouncedWhen)

  useEffect(() => {
    if (blockedLocally) return undefined

    const params = { page, page_size: pageSize, ordering }
    if (debouncedSearch) params.search = debouncedSearch
    if (sensor) {
      params.sensor = sensor
      // value__gte / value__lte chỉ hợp lệ khi đã chọn cảm biến (UC-04 E4)
      if (debouncedFrom !== '') params.value__gte = debouncedFrom
      if (debouncedTo !== '') params.value__lte = debouncedTo
    }
    // Gõ tới đâu lọc trọn đơn vị tới đó: cả ngày / trọn giờ / trọn phút / đúng giây.
    if (moment) {
      params.recorded_at__gte = moment.start
      params.recorded_at__lte = moment.end
    }

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
  }, [page, pageSize, ordering, debouncedSearch, sensor, debouncedFrom, debouncedTo, moment, blockedLocally, reloadKey])

  const withPageReset = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  const changeSensor = (code) => {
    setSensor(code)
    if (!code) {
      setValueFrom('')
      setValueTo('')
    }
    setPage(1)
  }

  const clearFilters = () => {
    setSearch('')
    setSensor('')
    setValueFrom('')
    setValueTo('')
    setWhen('')
    setServerErrors(null)
    setPage(1)
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
        <div className={ui.filters}>
          <Field label="Tìm kiếm">
            <SearchInput value={search} onChange={withPageReset(setSearch)} placeholder="Mã hoặc tên cảm biến…" />
          </Field>
          <Field label="Cảm biến">
            <select
              className={`${ui.input} ${ui.select}`}
              value={sensor}
              onChange={(e) => changeSensor(e.target.value)}
            >
              <option value="">Tất cả</option>
              {catalog.map((item) => (
                <option key={item.id} value={item.code}>
                  {item.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label={`Giá trị từ${selectedSensor ? ` (${selectedSensor.unit})` : ''}`}>
            <input
              type="number"
              step="any"
              className={`${ui.input} ${ui.inputNum} ${valueError ? ui.invalid : ''}`}
              disabled={!sensor}
              placeholder="—"
              value={valueFrom}
              onChange={(e) => withPageReset(setValueFrom)(e.target.value)}
            />
          </Field>
          <Field label="Đến">
            <input
              type="number"
              step="any"
              className={`${ui.input} ${ui.inputNum} ${valueError ? ui.invalid : ''}`}
              disabled={!sensor}
              placeholder="—"
              value={valueTo}
              onChange={(e) => withPageReset(setValueTo)(e.target.value)}
            />
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

        {(valueError || whenError) && (
          <div className={`${ui.fNote} ${ui.fNoteBad}`} role="alert">
            <InfoIcon />
            {valueError || whenError}
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
            <Pagination page={page} pageSize={pageSize} count={count} onChange={setPage} />
          </div>
        )}
      </section>
    </Layout>
  )
}
