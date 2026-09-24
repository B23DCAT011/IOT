import axios from 'axios'
import { API_BASE_URL } from '../config'

export class ApiError extends Error {
  constructor({ status, code, message, details }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export const isAbort = (err) => axios.isCancel(err) || err?.code === 'ERR_CANCELED'

// Token giữ trong bộ nhớ, AuthProvider đồng bộ vào đây. Không đọc thẳng localStorage
// ở mỗi request vì localStorage có thể bị chặn.
let currentToken = null
export const setApiToken = (token) => {
  currentToken = token
}

let onUnauthorized = null
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  // `noToken`: request đăng nhập không gửi token cũ (05-API.md §4.8).
  if (currentToken && !config.noToken && !config.headers.Authorization) {
    config.headers.Authorization = `Token ${currentToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (isAbort(error)) return Promise.reject(error)

    const response = error.response
    if (!response) {
      // Mã NETWORK_ERROR chỉ tồn tại ở Frontend — máy chủ không trả được gì nên không có mã của máy chủ.
      return Promise.reject(
        new ApiError({
          status: 0,
          code: 'NETWORK_ERROR',
          message: 'Không kết nối được tới máy chủ.',
          details: null,
        }),
      )
    }

    // Mọi lỗi của API có đúng một hình dạng {error:{code,message,details}} (05-API.md §2.6).
    const body = response.data?.error
    const apiError = new ApiError({
      status: response.status,
      code: body?.code ?? 'INTERNAL_ERROR',
      message: body?.message ?? 'Không tải được dữ liệu.',
      details: body?.details ?? null,
    })

    // 401 chỉ có một nghĩa: chưa đăng nhập hoặc phiên đã hết (05-API.md §2.7, §5.4 quy tắc 7).
    if (response.status === 401 && !error.config?.noUnauthorizedRedirect) {
      onUnauthorized?.()
    }
    return Promise.reject(apiError)
  },
)
