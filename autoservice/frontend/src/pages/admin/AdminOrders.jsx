import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import Pagination from '../../components/Pagination'
import ExportButton from '../../components/ExportButton'
import { getAdminOrders, getAdminMasters } from '../../api/admin'
import { Search } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const STATUSES = ['', 'new', 'preparation', 'in_process', 'ready', 'closed']
const STATUS_LABELS = { '': 'All Statuses', new: 'New', preparation: 'Preparation', in_process: 'In Process', ready: 'Ready', closed: 'Closed' }

export default function AdminOrders() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [masters, setMasters] = useState([])
  const [filters, setFilters] = useState({ status: '', master_id: '', date_from: '', date_to: '', search: '' })
  const [loading, setLoading] = useState(false)

  const load = (p = page) => {
    setLoading(true)
    const f = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v !== null))
    getAdminOrders(f, p).then(data => {
      setOrders(data.items || [])
      setTotal(data.total || 0)
      setPage(data.page || p)
    }).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [])
  useEffect(() => { getAdminMasters(1).then(d => setMasters(d.items || [])).catch(console.error) }, [])

  const setFilter = (k, v) => setFilters(f => ({ ...f, [k]: v }))

  const handleSearch = (e) => { e.preventDefault(); setPage(1); load(1) }

  const exportFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ''))

  return (
    <AdminLayout>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Orders</h1>
          <ExportButton filters={exportFilters} />
        </div>

        <form onSubmit={handleSearch} className="card p-4">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <select className="input" value={filters.status} onChange={e => setFilter('status', e.target.value)}>
              {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
            <select className="input" value={filters.master_id} onChange={e => setFilter('master_id', e.target.value)}>
              <option value="">All Masters</option>
              {masters.map(m => <option key={m.id} value={m.id}>{m.full_name}</option>)}
            </select>
            <input type="date" className="input" value={filters.date_from} onChange={e => setFilter('date_from', e.target.value)} placeholder="From" />
            <input type="date" className="input" value={filters.date_to} onChange={e => setFilter('date_to', e.target.value)} placeholder="To" />
            <div className="flex gap-2">
              <input className="input flex-1" placeholder="Search order#, plate, client…" value={filters.search} onChange={e => setFilter('search', e.target.value)} />
              <button type="submit" className="btn-primary px-3"><Search size={16} /></button>
            </div>
          </div>
        </form>

        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50 text-sm text-gray-500">{total} orders found</div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading…</div>
          ) : orders.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No orders found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                    <th className="px-4 py-3">Order #</th>
                    <th className="px-4 py-3">Car / Plate</th>
                    <th className="px-4 py-3">Client</th>
                    <th className="px-4 py-3">Master</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Price</th>
                    <th className="px-4 py-3 text-right">Profit</th>
                    <th className="px-4 py-3">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {orders.map(o => (
                    <tr key={o.order_number}
                      onClick={() => navigate(`/admin/orders/${o.order_number}`)}
                      className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                      <td className="px-4 py-3">
                        <div>{`${o.brand || ''} ${o.model || ''}`.trim() || '—'}</div>
                        {o.plate && <div className="text-xs font-mono text-gray-400">{o.plate}</div>}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{o.client_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{o.master_name || '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                      <td className="px-4 py-3 text-right">{fmt(o.agreed_price)}</td>
                      <td className={`px-4 py-3 text-right ${o.status === 'closed' && Number(o.profit) < 0 ? 'text-red-600' : ''}`}>
                        {o.status === 'closed' ? fmt(o.profit) : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="px-4 border-t border-gray-50">
                <Pagination total={total} page={page} pageSize={20} onChange={p => { setPage(p); load(p) }} />
              </div>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  )
}
