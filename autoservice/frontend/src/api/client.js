import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authTelegram = (data) => api.post('/auth/telegram', data).then((r) => r.data)

export const createOrder = (data) => api.post('/orders', data).then((r) => r.data)
export const getOrders = (status) =>
  api.get('/orders', { params: status ? { status } : {} }).then((r) => r.data)
export const getOrderDetail = (orderNumber) =>
  api.get(`/orders/${orderNumber}`).then((r) => r.data)
export const updateOrderStatus = (orderNumber, data) =>
  api.patch(`/orders/${orderNumber}/status`, data).then((r) => r.data)
export const closeOrder = (orderNumber, data) =>
  api.post(`/orders/${orderNumber}/close`, data).then((r) => r.data)
export const uploadPhotos = (orderNumber, files) => {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return api.post(`/orders/${orderNumber}/photos`, form).then((r) => r.data)
}
export const getOrderPhotos = (orderNumber) =>
  api.get(`/orders/${orderNumber}/photos`).then((r) => r.data)
export const recordPayment = (orderNumber, description, amount, receiptFile) => {
  const form = new FormData()
  form.append('description', description)
  form.append('amount', amount)
  form.append('receipt', receiptFile)
  return api.post(`/orders/${orderNumber}/payment`, form).then((r) => r.data)
}

export const getCarHistory = (plate) =>
  api.get(`/cars/plate/${encodeURIComponent(plate)}`).then((r) => r.data)

export const getFinancialSummary = (params) =>
  api.get('/financials/summary', { params }).then((r) => r.data)
export const getFinancialOrders = (params) =>
  api.get('/financials/orders', { params }).then((r) => r.data)

export const getProfile = () => api.get('/profile').then((r) => r.data)
export const changePassword = (data) => api.patch('/profile/password', data).then((r) => r.data)

export default api
