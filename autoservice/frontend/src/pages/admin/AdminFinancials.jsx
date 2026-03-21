import React, { useEffect, useState } from 'react'
import AdminLayout from '../../components/AdminLayout'
import ExportButton from '../../components/ExportButton'
import { getAdminFinancials, getAdminMasters } from '../../api/admin'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const PERIODS = [
  { value: 'today', label: 'Bugun' },
  { value: 'week', label: 'Shu hafta' },
  { value: 'month', label: 'Shu oy' },
  { value: 'last_month', label: 'O\'tgan oy' },
  { value: 'custom', label: 'Boshqa' },
]

function buildDates(period) {
  const now = new Date()
  const iso = d => d.toISOString().slice(0, 10)
  if (period === 'today') return { date_from: iso(now), date_to: iso(now) }
  if (period === 'week') { const f = new Date(now); f.setDate(now.getDate() - 7); return { date_from: iso(f), date_to: iso(now) } }
  if (period === 'month') return { date_from: iso(new Date(now.getFullYear(), now.getMonth(), 1)), date_to: iso(now) }
  if (period === 'last_month') {
    const f = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const t = new Date(now.getFullYear(), now.getMonth(), 0)
    return { date_from: iso(f), date_to: iso(t) }
  }
  return {}
}

export default function AdminFinancials() {
  const [period, setPeriod] = useState('month')
  const [masterId, setMasterId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [masters, setMasters] = useState([])
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getAdminMasters(1).then(d => setMasters(d.items || [])).catch(console.error)
  }, [])

  const buildFilters = () => {
    const dates = period === 'custom' ? { date_from: dateFrom, date_to: dateTo } : buildDates(period)
    return { ...dates, ...(masterId ? { master_id: masterId } : {}) }
  }

  const load = () => {
    setLoading(true)
    getAdminFinancials(buildFilters()).then(setReport).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { if (period !== 'custom') load() }, [period, masterId])

  const summary = report?.summary || {}
  const orders = report?.orders || []
  const exportFilters = buildFilters()

  const summaryCards = [
    { label: 'Daromad', value: fmt(summary.total_revenue), color: 'text-blue-700' },
    { label: 'Qismlar narxi', value: fmt(summary.total_parts_cost), color: 'text-orange-600' },
    { label: 'Foyda', value: fmt(summary.total_profit), color: Number(summary.total_profit) < 0 ? 'text-red-600' : 'text-gray-900' },
    { label: 'Servis ulushi (60%)', value: fmt(summary.total_service_share), color: 'text-purple-700' },
    { label: 'Ustalar ulushi (40%)', value: fmt(summary.total_master_share), color: 'text-green-700' },
  ]

  return (
    <AdminLayout>
      <div className="p-3 sm:p-6 space-y-4 sm:space-y-5">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-xl font-bold text-gray-900">Moliya</h1>
          <ExportButton filters={exportFilters} />
        </div>

        <div className="card p-3 sm:p-4 flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3">
          <div className="flex gap-1 flex-wrap">
            {PERIODS.map(p => (
              <button key={p.value} onClick={() => setPeriod(p.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${period === p.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >{p.label}</button>
            ))}
          </div>
          {period === 'custom' && (
            <div className="flex items-center gap-2">
              <input type="date" className="input w-auto text-sm py-1.5" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
              <span className="text-gray-400">—</span>
              <input type="date" className="input w-auto text-sm py-1.5" value={dateTo} onChange={e => setDateTo(e.target.value)} />
              <button onClick={load} className="btn-primary py-1.5">Qo'llash</button>
            </div>
          )}
          <select className="input w-full sm:w-48 sm:ml-auto" value={masterId} onChange={e => setMasterId(e.target.value)}>
            <option value="">Barcha ustalar</option>
            {masters.map(m => <option key={m.id} value={m.id}>{m.full_name}</option>)}
          </select>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Yuklanmoqda…</div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
              {summaryCards.map(({ label, value, color }) => (
                <div key={label} className="card text-center">
                  <p className={`text-lg font-bold ${color}`}>{value}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{label}</p>
                </div>
              ))}
            </div>

            {orders.length > 0 ? (
              <div className="card p-0 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-50 text-sm font-medium text-gray-700">{orders.length} ta yopilgan buyurtma</div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                        <th className="px-4 py-3">Buyurtma №</th>
                        <th className="px-4 py-3">Usta</th>
                        <th className="px-4 py-3">Mashina</th>
                        <th className="px-4 py-3 text-right">Daromad</th>
                        <th className="px-4 py-3 text-right">Qismlar</th>
                        <th className="px-4 py-3 text-right">Foyda</th>
                        <th className="px-4 py-3 text-right">Usta ul.</th>
                        <th className="px-4 py-3 text-right">Servis ul.</th>
                        <th className="px-4 py-3">Yopilgan</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {orders.map(o => {
                        const profit = Number(o.profit)
                        return (
                          <tr key={o.order_number} className={profit < 0 ? 'bg-red-50/40' : ''}>
                            <td className="px-4 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                            <td className="px-4 py-3 text-gray-600">{o.master_name || '—'}</td>
                            <td className="px-4 py-3">{`${o.brand || ''} ${o.model || ''}`.trim() || '—'}</td>
                            <td className="px-4 py-3 text-right">{fmt(o.agreed_price)}</td>
                            <td className="px-4 py-3 text-right text-orange-600">{fmt(o.parts_cost)}</td>
                            <td className={`px-4 py-3 text-right font-medium ${profit < 0 ? 'text-red-600' : ''}`}>{fmt(o.profit)}</td>
                            <td className="px-4 py-3 text-right text-green-700">{fmt(o.master_share)}</td>
                            <td className="px-4 py-3 text-right text-purple-700">{fmt(o.service_share)}</td>
                            <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(o.closed_at)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="card text-center py-12 text-gray-400">Bu davrda yopilgan buyurtmalar yo'q.</div>
            )}
          </>
        )}
      </div>
    </AdminLayout>
  )
}
