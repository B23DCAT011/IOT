import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { isAbort } from '../api/client'
import { deviceApi, sensorApi } from '../api/endpoints'
import Banner from '../components/Banner'
import DevicePanel from '../components/dashboard/DevicePanel'
import s from '../components/dashboard/Dashboard.module.css'
import SensorChart from '../components/dashboard/SensorChart'
import StatCard from '../components/dashboard/StatCard'
import Layout from '../components/Layout'
import { CHART_POINTS, OFFLINE_AFTER_MS } from '../config'
import { METRIC_COLOR, METRIC_KEYS, metricKey } from '../constants'
import { useRealtime, useRealtimeEvent } from '../realtime/RealtimeContext'
import ui from '../styles/ui.module.css'
import { errorChip } from '../utils/errors'
import { fmtTime } from '../utils/format'

// Biến thiên = giá trị hiện tại − giá trị của 10 chu kỳ trước (20 giây) — CLAUDE.md §0.2f.
const DELTA_CYCLES = 10

export default function DashboardPage() {
  const { status: wsStatus, generation, reconnectNow } = useRealtime()

  const [catalog, setCatalog] = useState([])
  const [current, setCurrent] = useState({})
  const [chart, setChart] = useState([])
  const [devices, setDevices] = useState([])
  const [lastUpdate, setLastUpdate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [offline, setOffline] = useState(false)
  const [notice, setNotice] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const offlineTimer = useRef(null)

  // BR-07: quá 30 giây không có sensor.data thì báo ngoại tuyến. Đếm ở giao diện, không ở máy chủ.
  const armOfflineTimer = useCallback(() => {
    clearTimeout(offlineTimer.current)
    setOffline(false)
    offlineTimer.current = setTimeout(() => setOffline(true), OFFLINE_AFTER_MS)
  }, [])

  useEffect(() => {
    armOfflineTimer()
    return () => clearTimeout(offlineTimer.current)
  }, [armOfflineTimer])

  // Kết nối lại WebSocket sau khi mất (generation > 1) → tải lại để bù khoảng trống (§5.4 quy tắc 2).
  const reconnectKey = generation > 1 ? generation : 0

  useEffect(() => {
    const controller = new AbortController()
    const config = { signal: controller.signal }

    Promise.all([
      sensorApi.catalog(config),
      sensorApi.latest(config),
      sensorApi.chart(CHART_POINTS, config),
      deviceApi.list(config),
    ])
      .then(([sensors, latest, chartData, deviceList]) => {
        // Thẻ dựng từ DANH MỤC, giá trị điền từ số đo mới nhất (05-API.md §4.1, UC-01 A3).
        const byId = new Map(sensors.map((sensor) => [sensor.id, sensor]))
        const values = {}
        let newest = null
        latest.forEach((reading) => {
          const sensor = byId.get(reading.sensor.id)
          if (!sensor) return
          values[metricKey(sensor.metric_type)] = reading.value
          if (!newest || reading.recorded_at > newest) newest = reading.recorded_at
        })
        setCatalog(sensors)
        setCurrent(values)
        setChart(chartData)
        setDevices(deviceList)
        setLastUpdate(newest)
        setLoadError(null)
      })
      .catch((err) => {
        if (!isAbort(err)) setLoadError(err)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [reconnectKey, reloadKey])

  useRealtimeEvent((event) => {
    if (event.type !== 'sensor.data') return
    armOfflineTimer()

    // Cảm biến không đọc được ở chu kỳ này thì trường là null: thẻ giữ giá trị cũ, biểu đồ đứt nét.
    setCurrent((prev) => {
      const next = { ...prev }
      METRIC_KEYS.forEach((key) => {
        if (event[key] != null) next[key] = event[key]
      })
      return next
    })
    setChart((prev) => {
      if (prev.length && prev[prev.length - 1].recorded_at === event.recorded_at) return prev
      const point = {
        recorded_at: event.recorded_at,
        temperature: event.temperature,
        humidity: event.humidity,
        light: event.light,
      }
      return [...prev, point].slice(-CHART_POINTS) // BR-10
    })
    setLastUpdate(event.recorded_at)
  })

  const series = useMemo(
    () =>
      catalog.map((sensor) => {
        const key = metricKey(sensor.metric_type)
        return {
          key,
          name: sensor.name,
          unit: sensor.unit,
          metricType: sensor.metric_type,
          color: METRIC_COLOR[key] ?? '#5B6D7C',
          axis: sensor.metric_type === 'LIGHT' ? 'right' : 'left',
        }
      }),
    [catalog],
  )

  const lastPoint = chart[chart.length - 1]
  const refPoint = chart.length > DELTA_CYCLES ? chart[chart.length - 1 - DELTA_CYCLES] : null

  const chartSub = chart.length
    ? [
        `${fmtTime(chart[0].recorded_at)} → ${fmtTime(lastPoint.recorded_at)}`,
        'chu kỳ 2 giây',
        ...series.map((item) => {
          const missing = chart.filter((point) => point[item.key] == null).length
          return missing ? `${missing} mẫu thiếu ${item.name.toLowerCase()}` : null
        }),
      ]
        .filter(Boolean)
        .join(' · ')
    : 'chưa nhận được mẫu nào'

  const reloadDevices = () => {
    deviceApi
      .list()
      .then(setDevices)
      .catch(() => {})
  }

  let connText = 'Đang nhận dữ liệu'
  if (wsStatus === 'closed') connText = 'Mất kết nối máy chủ'
  else if (wsStatus === 'connecting' && generation === 0) connText = 'Đang kết nối…'
  else if (offline) connText = 'Thiết bị ngoại tuyến'
  const connOk = wsStatus === 'open' && !offline

  const topRight = (
    <>
      <div className={ui.conn}>
        <span className={`${ui.dot} ${connOk ? '' : ui.dotWarn}`} />
        {connText}
      </div>
      {lastUpdate && <div className={ui.stamp}>Cập nhật {fmtTime(lastUpdate)}</div>}
    </>
  )

  return (
    <Layout title="Dashboard" right={topRight}>
      {wsStatus === 'closed' && (
        <Banner chip="WebSocket" action="Thử lại ngay" onAction={reconnectNow}>
          Mất kết nối tới máy chủ — đang thử lại sau 5 giây…
        </Banner>
      )}
      {loadError && (
        <Banner chip={errorChip(loadError)} action="Thử lại" onAction={() => setReloadKey((k) => k + 1)}>
          Không tải được dữ liệu. {loadError.message}
        </Banner>
      )}
      {notice && (
        <Banner chip={notice.chip} action="Đóng" onAction={() => setNotice(null)}>
          {notice.text}
        </Banner>
      )}

      <div className={`${s.stats} ${offline ? ui.dim : ''}`}>
        {catalog.map((sensor) => {
          const key = metricKey(sensor.metric_type)
          const delta =
            lastPoint?.[key] != null && refPoint?.[key] != null ? lastPoint[key] - refPoint[key] : null
          return (
            <StatCard
              key={sensor.id}
              sensor={sensor}
              color={METRIC_COLOR[key]}
              value={current[key]}
              delta={delta}
              spark={chart.slice(-(DELTA_CYCLES + 1)).map((point) => point[key])}
              offline={offline}
            />
          )
        })}
      </div>

      <div className={s.chartRow}>
        <div className={s.chartCol}>
          <section className={ui.card}>
            <div className={ui.cardHead}>
              <div>
                <div className={ui.cardTitle}>Diễn biến {CHART_POINTS} mẫu gần nhất</div>
                <div className={ui.cardSub}>{chartSub}</div>
              </div>
              <div className={s.legend}>
                {series.map((item) => (
                  <span key={item.key} className={s.legendItem}>
                    <span className={s.legendKey} style={{ background: item.color }} />
                    {item.name}
                  </span>
                ))}
              </div>
            </div>

            {chart.length === 0 ? (
              <div className={s.chartEmpty}>{loading ? 'Đang tải…' : 'Chưa có dữ liệu'}</div>
            ) : (
              <div className={s.chartBox}>
                <div className={s.plot}>
                  <div className={s.plotInner}>
                    <SensorChart data={chart} series={series} />
                  </div>
                </div>
                <div className={s.units}>
                  <span>°C / %</span>
                  <span>lux</span>
                </div>
              </div>
            )}
          </section>
        </div>

        <div className={s.devCol}>
          <DevicePanel
            devices={devices}
            setDevices={setDevices}
            loading={loading}
            onNotice={setNotice}
            onFallback={reloadDevices}
          />
        </div>
      </div>
    </Layout>
  )
}
