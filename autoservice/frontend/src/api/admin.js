import api from './client'

export const getDashboard = () => api.get('/admin/dashboard').then(r => r.data)

export const getAdminOrders = (filters = {}, page = 1) =>
  api.get('/admin/orders', { params: { ...filters, page } }).then(r => r.data)

export const getAdminOrderDetail = (orderNumber) =>
  api.get(`/admin/orders/${orderNumber}`).then(r => r.data)

export const forceCloseOrder = (orderNumber, partsCost) =>
  api.patch(`/admin/orders/${orderNumber}/force-close`, { parts_cost: partsCost }).then(r => r.data)

export const getAdminClients = (search, isActive, page = 1) =>
  api.get('/admin/clients', { params: { search, is_active: isActive, page } }).then(r => r.data)

export const getAdminClientProfile = (id) =>
  api.get(`/admin/clients/${id}`).then(r => r.data)

export const blockUser = (id, entity = 'clients') =>
  api.patch(`/admin/${entity}/${id}/block`).then(r => r.data)

export const unblockUser = (id, entity = 'clients') =>
  api.patch(`/admin/${entity}/${id}/unblock`).then(r => r.data)

export const getAdminMasters = (page = 1) =>
  api.get('/admin/masters', { params: { page } }).then(r => r.data)

export const getAdminMasterProfile = (id, dateFrom, dateTo) =>
  api.get(`/admin/masters/${id}`, { params: { date_from: dateFrom, date_to: dateTo } }).then(r => r.data)

export const setUserRole = (id, role) =>
  api.patch(`/admin/masters/${id}/${role === 'master' ? 'promote' : 'demote'}`).then(r => r.data)

export const getAdminFinancials = (filters = {}) =>
  api.get('/admin/financials', { params: filters }).then(r => r.data)

export const exportFinancials = (filters = {}, format = 'xlsx') => {
  const params = new URLSearchParams({ ...filters, export_format: format })
  return `/api/admin/financials/export?${params.toString()}`
}

export const sendBroadcast = (target, message) =>
  api.post('/admin/broadcast', { target, message }).then(r => r.data)

export const getBroadcasts = () =>
  api.get('/admin/broadcasts').then(r => r.data)

export const getAdminFeedbacks = (filters = {}, page = 1) =>
  api.get('/admin/feedbacks', { params: { ...filters, page } }).then(r => r.data)

export const getFeedbackStats = () =>
  api.get('/admin/feedbacks/stats').then(r => r.data)

export const getAdminCarHistory = (plate) =>
  api.get(`/admin/cars/${encodeURIComponent(plate)}`).then(r => r.data)
