import { api } from './client'

const data = (response) => response.data

// Đường dẫn KHÔNG có dấu "/" cuối (05-API.md §2.5).
export const authApi = {
  login: (username, password) =>
    api
      .post('/auth/login', { username, password }, { noToken: true, noUnauthorizedRedirect: true })
      .then(data),

  // Gửi kèm token tường minh: AuthProvider đã xoá token khỏi bộ nhớ trước khi gọi (§4.9).
  logout: (token) =>
    api
      .post('/auth/logout', null, {
        headers: { Authorization: `Token ${token}` },
        noUnauthorizedRedirect: true,
      })
      .then(() => undefined),
}

export const sensorApi = {
  catalog: (config) => api.get('/sensors/devices', config).then(data),
  latest: (config) => api.get('/sensors/latest', config).then(data),
  chart: (limit, config) => api.get('/sensors/chart', { ...config, params: { limit } }).then(data),
  list: (params, config) => api.get('/sensors', { ...config, params }).then(data),
}

export const deviceApi = {
  list: (config) => api.get('/devices', config).then(data),
  // Không gửi user_id — người thao tác lấy từ token (05-API.md §4.5, bản 2.1).
  control: (id, action) => api.post(`/devices/${id}/control`, { action }).then(data),
}

export const actionApi = {
  list: (params, config) => api.get('/actions', { ...config, params }).then(data),
}

export const profileApi = {
  get: (config) => api.get('/profile', config).then(data),
}
