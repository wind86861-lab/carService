import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getFinancialSummary, getFinancialOrders } from '../api/client'
import { ArrowLeft, TrendingUp, Package, DollarSign, Award } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const PERIODS = [
  { value: 'today', label: 'Bugun' },
  { value: 'week', label: 'Shu hafta' },
  { value: 'month', label: 'Shu oy' },
  { value: 'custom', label: 'Boshqa davr' },
]

export default function Statistics() {
  const navigate = useNavigate()
  const [period, setPeriod] = useState('month')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [summary, setSummary] = useState(null)
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    const params = { period }
    if (period === 'custom') { params.from_date = fromDate; params.to_date = toDate }
    Promise.all([getFinancialSummary(params), getFinancialOrders(params)])
      .then(([s, o]) => { setSummary(s); setOrders(o) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (period !== 'custom') load() }, [period])

  const summaryCards = summary ? [
    { label: 'Yopilgan buyurtmalar', value: summary.order_count, icon: Award, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Jami tushum', value: fmt(summary.total_price), icon: TrendingUp, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Ehtiyot qismlar', value: fmt(summary.total_parts), icon: Package, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Sizning ulush', value: fmt(summary.total_master_share), icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50' },
  ] : []

  const totals = orders.reduce((acc, o) => ({
    agreed: acc.agreed + Number(o.agreed_price),
    parts: acc.parts + Number(o.parts_cost),
    profit: acc.profit + Number(o.profit),
    share: acc.share + Number(o.master_share),
  }), { agreed: 0, parts: 0, profit: 0, share: 0 })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="btn-secondary p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-lg font-bold">Statistika</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        <div className="card">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex gap-1 flex-wrap">
              {PERIODS.map(p => (
                <button
                  key={p.value}
                  onClick={() => setPeriod(p.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${period === p.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                >{p.label}</button>
              ))}
            </div>
            {period === 'custom' && (
              <div className="flex items-center gap-2 ml-auto">
                <input type="date" className="input w-auto text-sm py-1.5" value={fromDate} onChange={e => setFromDate(e.target.value)} />
                <span className="text-gray-400">—</span>
                <input type="date" className="input w-auto text-sm py-1.5" value={toDate} onChange={e => setToDate(e.target.value)} />
                <button onClick={load} className="btn-primary py-1.5">Qo'llash</button>
              </div>
            )}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Yuklanmoqda…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {summaryCards.map(({ label, value, icon: Icon, color, bg }) => (
                <div key={label} className="card">
                  <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-3`}>
                    <Icon size={20} className={color} />
                  </div>
                  <p className="text-xl font-bold text-gray-900">{value}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{label}</p>
                </div>
              ))}
            </div>

            {orders.length > 0 ? (
              <div className="card p-0 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-50">
                  <h2 className="font-semibold text-gray-700">Yopilgan buyurtmalar tafsiloti</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                        <th className="px-4 py-3">Buyurtma №</th>
                        <th className="px-4 py-3">Mashina</th>
                        <th className="px-4 py-3 text-right">Tushum</th>
                        <th className="px-4 py-3 text-right">Qismlar</th>
                        <th className="px-4 py-3 text-right">Foyda</th>
                        <th className="px-4 py-3 text-right">Sizning ulush</th>
                        <th className="px-4 py-3">Yopilgan</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {orders.map(o => (
                        <tr key={o.order_number} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-mono font-bold text-blue-700">{o.order_number}</td>
                          <td className="px-4 py-3">{`${o.brand || ''} ${o.model || ''}`.trim() || '—'}</td>
                          <td className="px-4 py-3 text-right">{fmt(o.agreed_price)}</td>
                          <td className="px-4 py-3 text-right text-orange-600">{fmt(o.parts_cost)}</td>
                          <td className={`px-4 py-3 text-right font-medium ${Number(o.profit) < 0 ? 'text-red-600' : ''}`}>{fmt(o.profit)}</td>
                          <td className="px-4 py-3 text-right text-green-700 font-semibold">{fmt(o.master_share)}</td>
                          <td className="px-4 py-3 text-gray-500">{fmtDate(o.closed_at)}</td>
                        </tr>
                      ))}
                      <tr className="bg-gray-50 font-semibold text-sm border-t-2 border-gray-200">
                        <td className="px-4 py-3" colSpan={2}>Jami ({orders.length} ta buyurtma)</td>
                        <td className="px-4 py-3 text-right">{fmt(totals.agreed)}</td>
                        <td className="px-4 py-3 text-right text-orange-600">{fmt(totals.parts)}</td>
                        <td className={`px-4 py-3 text-right ${totals.profit < 0 ? 'text-red-600' : ''}`}>{fmt(totals.profit)}</td>
                        <td className="px-4 py-3 text-right text-green-700">{fmt(totals.share)}</td>
                        <td />
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="card text-center py-12 text-gray-400">Bu davrda yopilgan buyurtmalar yo'q.</div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
