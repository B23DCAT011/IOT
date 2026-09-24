import { useEffect, useState } from 'react'
import { isAbort } from '../api/client'
import { profileApi } from '../api/endpoints'
import Banner from '../components/Banner'
import { LinkIcon } from '../components/Icons'
import Layout from '../components/Layout'
import { API_BASE_URL } from '../config'
import ui from '../styles/ui.module.css'
import { errorChip } from '../utils/errors'
import { shortUrl } from '../utils/format'
import s from './Profile.module.css'

const LINKS = [
  { key: 'github', title: 'Mã nguồn', icon: 'github' },
  { key: 'report_pdf', title: 'Báo cáo PDF', icon: 'file' },
  { key: 'figma', title: 'Thiết kế Figma', icon: 'figma' },
  { key: 'api_docs', title: 'Tài liệu API', icon: 'code' },
]

function Avatar({ url, name }) {
  const [broken, setBroken] = useState(false)
  if (!url || broken) {
    return (
      <div className={s.avatar}>
        Ảnh đại diện
        <br />
        200 × 200
      </div>
    )
  }
  // avatar_url là đường dẫn tương đối trên backend (/static/…) — 05-API.md §4.7, §12 điểm 6
  return (
    <img className={s.avatarImg} src={new URL(url, API_BASE_URL).href} alt={name} onError={() => setBroken(true)} />
  )
}

export default function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    profileApi
      .get({ signal: controller.signal })
      .then((result) => {
        setProfile(result)
        setError(null)
      })
      .catch((err) => {
        if (!isAbort(err)) setError(err)
      })
    return () => controller.abort()
  }, [reloadKey])

  const student = profile?.student
  const project = profile?.project

  return (
    <Layout title="Profile">
      {error && (
        <Banner chip={errorChip(error)} action="Thử lại" onAction={() => setReloadKey((k) => k + 1)}>
          Không tải được dữ liệu. {error.message}
        </Banner>
      )}

      {profile && (
        <div className={s.cols}>
          <div className={`${s.col} ${s.colA}`}>
            <section className={ui.card}>
              <div className={ui.cardHead}>
                <div className={ui.cardTitle}>Sinh viên thực hiện</div>
              </div>
              <div className={s.who}>
                <Avatar url={student.avatar_url} name={student.full_name} />
                <div className={s.kv}>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Họ và tên</div>
                    <div className={s.kvV}>{student.full_name}</div>
                  </div>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Mã sinh viên</div>
                    <div className={`${s.kvV} ${s.mono}`}>{student.student_id}</div>
                  </div>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Lớp</div>
                    <div className={`${s.kvV} ${s.mono}`}>{student.class_name}</div>
                  </div>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Email</div>
                    <div className={`${s.kvV} ${s.mono}`}>{student.email}</div>
                  </div>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Học phần</div>
                    <div className={s.kvV}>{project.subject}</div>
                  </div>
                  <div className={s.kvRow}>
                    <div className={s.kvK}>Giảng viên</div>
                    {/* Học vị nằm sẵn trong chuỗi supervisor, không tự ghép tiền tố (05-API.md §4.7) */}
                    <div className={s.kvV}>{project.supervisor}</div>
                  </div>
                </div>
              </div>
              <div className={s.topic}>
                <div className={s.topicK}>Đề tài</div>
                <div className={s.topicV}>{project.title}</div>
              </div>
            </section>
          </div>

          <div className={`${s.col} ${s.colB}`}>
            <section className={ui.card}>
              <div className={ui.cardHead}>
                <div className={ui.cardTitle}>Sản phẩm bàn giao</div>
                <div className={ui.cardSub}>{LINKS.length} liên kết</div>
              </div>
              <div className={s.links}>
                {LINKS.map((link) => {
                  const href = profile.links?.[link.key]
                  // Liên kết null → nút vô hiệu kèm "Đang cập nhật" (UC-06 E1)
                  if (!href) {
                    return (
                      <div key={link.key} className={`${s.link} ${s.linkOff}`} aria-disabled="true">
                        <LinkIcon name={link.icon} />
                        <div className={s.linkTxt}>
                          <div className={s.linkT}>{link.title}</div>
                          <div className={s.linkS}>Đang cập nhật</div>
                        </div>
                      </div>
                    )
                  }
                  return (
                    <a key={link.key} className={s.link} href={href} target="_blank" rel="noreferrer">
                      <LinkIcon name={link.icon} />
                      <div className={s.linkTxt}>
                        <div className={s.linkT}>{link.title}</div>
                        <div className={s.linkS}>{shortUrl(href)}</div>
                      </div>
                    </a>
                  )
                })}
              </div>
            </section>
          </div>
        </div>
      )}
    </Layout>
  )
}
