import React, { useEffect, useState } from 'react'
import AdminLayout from '../../components/AdminLayout'
import Pagination from '../../components/Pagination'
import { getAdminFeedbacks, getFeedbackStats, getAdminMasters } from '../../api/admin'
import { Star } from 'lucide-react'

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const CATEGORY_COLORS = {
  Communication: 'bg-blue-100 text-blue-700',
  Time: 'bg-yellow-100 text-yellow-700',
  Quality: 'bg-green-100 text-green-700',
  Price: 'bg-red-100 text-red-700',
  Uncategorized: 'bg-gray-100 text-gray-700',
}

export default function AdminFeedbacks() {
  const [stats, setStats] = useState(null)
  const [feedbacks, setFeedbacks] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [masters, setMasters] = useState([])
  const [filters, setFilters] = useState({ master_id: '', rating_max: '', date_from: '', date_to: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getFeedbackStats().then(setStats).catch(console.error)
    getAdminMasters(1).then(d => setMasters(d.items || [])).catch(console.error)
    loadFeedbacks(1)
  }, [])

  const loadFeedbacks = (p = 1) => {
    setLoading(true)
    const f = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ''))
    getAdminFeedbacks(f, p).then(d => {
      setFeedbacks(d.items || [])
      setTotal(d.total || 0)
      setPage(p)
    }).catch(console.error).finally(() => setLoading(false))
  }

  const setFilter = (k, v) => setFilters(f => ({ ...f, [k]: v }))
  const maxDist = stats ? Math.max(...(stats.distribution || []).map(d => d.count), 1) : 1

  return (
    <AdminLayout>
      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
        <h1 className="text-xl font-bold text-gray-900">Fikr-mulohazalar</h1>

        {stats && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
              <div className="card text-center lg:col-span-1">
                <div className="text-5xl font-bold text-yellow-500 mb-1">
                  {Number(stats.avg_rating).toFixed(1)}
                </div>
                <div className="flex justify-center gap-0.5 text-yellow-400 text-sm mb-1">
                  {[...Array(10)].map((_, i) => (
                    <span key={i} className={i < Math.round(stats.avg_rating) ? 'text-yellow-400' : 'text-gray-300'}>★</span>
                  ))}
                </div>
                <p className="text-sm text-gray-500">{stats.total} ta fikr-mulohaza</p>
              </div>

              <div className="card lg:col-span-2">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Baho taqsimoti</h3>
                <div className="space-y-1.5">
                  {(stats.distribution || []).map(d => (
                    <div key={d.score} className="flex items-center gap-2 text-xs">
                      <span className="w-3 text-gray-500">{d.score}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                        <div
                          className="h-full bg-yellow-400 rounded-full transition-all"
                          style={{ width: `${(d.count / maxDist) * 100}%` }}
                        />
                      </div>
                      <span className="w-6 text-right text-gray-500">{d.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              {(stats.categories || []).map(c => (
                <div key={c.category} className="card text-center">
                  <p className="text-2xl font-bold">{c.count}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${CATEGORY_COLORS[c.category] || CATEGORY_COLORS.Uncategorized}`}>
                    {c.category}
                  </span>
                </div>
              ))}
            </div>

            {stats.masters?.length > 0 && (
              <div className="card p-0 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-50 font-medium text-sm text-gray-700">Ustalar reytingi</div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                        <th className="px-4 py-3">Usta</th>
                        <th className="px-4 py-3 text-right">O'rtacha baho</th>
                        <th className="px-4 py-3 text-right">Fikrlar</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {stats.masters.map((m, i) => (
                        <tr key={m.master_id}>
                          <td className="px-4 py-3">
                            <span className="text-gray-400 mr-2 text-xs">#{i + 1}</span>{m.master_name}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-yellow-500">★</span> {Number(m.avg_rating).toFixed(1)}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-500">{m.total_feedback}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        <div className="card p-3 sm:p-4 flex flex-wrap gap-2 sm:gap-3">
          <select className="input w-48" value={filters.master_id} onChange={e => setFilter('master_id', e.target.value)}>
            <option value="">Barcha ustalar</option>
            {masters.map(m => <option key={m.id} value={m.id}>{m.full_name}</option>)}
          </select>
          <select className="input w-40" value={filters.rating_max} onChange={e => setFilter('rating_max', e.target.value)}>
            <option value="">Barcha baholar</option>
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>≤ {n} stars</option>)}
          </select>
          <input type="date" className="input w-auto text-sm" value={filters.date_from} onChange={e => setFilter('date_from', e.target.value)} />
          <input type="date" className="input w-auto text-sm" value={filters.date_to} onChange={e => setFilter('date_to', e.target.value)} />
          <button onClick={() => loadFeedbacks(1)} className="btn-primary">Qo'llash</button>
          <button onClick={() => { setFilters({ master_id: '', rating_max: '', date_from: '', date_to: '' }); loadFeedbacks(1) }} className="btn-secondary">Tozalash</button>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50 text-sm text-gray-500">{total} ta fikr-mulohaza</div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Yuklanmoqda…</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs font-medium text-gray-500 uppercase text-left">
                      <th className="px-4 py-3">Baho</th>
                      <th className="px-4 py-3">Kategoriya</th>
                      <th className="px-4 py-3">Izoh</th>
                      <th className="px-4 py-3">Mijoz</th>
                      <th className="px-4 py-3">Usta</th>
                      <th className="px-4 py-3">Buyurtma №</th>
                      <th className="px-4 py-3">Sana</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {feedbacks.map(f => (
                      <tr key={f.id}>
                        <td className="px-4 py-3">
                          <span className={`font-bold ${f.rating <= 4 ? 'text-red-600' : f.rating <= 7 ? 'text-yellow-600' : 'text-green-600'}`}>
                            {f.rating}/10
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {f.category && (
                            <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[f.category] || CATEGORY_COLORS.Uncategorized}`}>
                              {f.category}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{f.comment || '—'}</td>
                        <td className="px-4 py-3">{f.client_name || '—'}</td>
                        <td className="px-4 py-3 text-gray-500">{f.master_name || '—'}</td>
                        <td className="px-4 py-3 font-mono text-xs text-blue-700">{f.order_number}</td>
                        <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(f.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 border-t border-gray-50">
                <Pagination total={total} page={page} pageSize={20} onChange={p => loadFeedbacks(p)} />
              </div>
            </>
          )}
        </div>
      </div>
    </AdminLayout>
  )
}
