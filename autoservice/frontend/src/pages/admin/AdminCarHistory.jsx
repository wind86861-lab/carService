import React, { useState } from 'react'
import AdminLayout from '../../components/AdminLayout'
import StatusBadge from '../../components/StatusBadge'
import { getAdminCarHistory } from '../../api/admin'
import { Search, Car } from 'lucide-react'

function fmt(n) { return Number(n || 0).toLocaleString('ru-RU') + ' UZS' }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export default function AdminCarHistory() {
  const [plate, setPlate] = useState('')
  const [query, setQuery] = useState('')
  const [visits, setVisits] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setSearched(false)
    try {
      const data = await getAdminCarHistory(query.trim().toUpperCase())
      setVisits(Array.isArray(data) ? data : [])
      setPlate(query.trim().toUpperCase())
    } catch (e) {
      setVisits([])
    } finally {
      setLoading(false)
      setSearched(true)
    }
  }

  const carInfo = visits[0] ? `${visits[0].brand || ''} ${visits[0].model || ''}`.trim() : ''

  return (
    <AdminLayout>
      <div className="p-6 space-y-6">
        <h1 className="text-xl font-bold text-gray-900">Car History</h1>

        <div className="card p-4">
          <form onSubmit={handleSearch} className="flex gap-3">
            <input
              className="input flex-1 font-mono uppercase"
              placeholder="Enter license plate (e.g. 01A123BB)"
              value={query}
              onChange={e => setQuery(e.target.value.toUpperCase())}
            />
            <button type="submit" disabled={loading} className="btn-primary">
              <Search size={16} /> {loading ? 'Searching…' : 'Search'}
            </button>
          </form>
        </div>

        {searched && (
          visits.length === 0 ? (
            <div className="card text-center py-12">
              <Car className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No history found for plate <span className="font-mono font-bold">{plate}</span>.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="font-mono font-bold text-lg text-blue-700">{plate}</span>
                {carInfo && <span className="text-gray-600">{carInfo}</span>}
                <span className="text-sm text-gray-400">{visits.length} visit{visits.length !== 1 ? 's' : ''}</span>
              </div>

              <div className="relative">
                <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-100" />
                <div className="space-y-4">
                  {visits.map((v, i) => (
                    <div key={v.order_number} className="relative pl-12">
                      <div className="absolute left-3.5 top-4 w-3.5 h-3.5 rounded-full bg-blue-500 border-2 border-white shadow-sm" />
                      <div className="card">
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-blue-700">{v.order_number}</span>
                            <StatusBadge status={v.status} />
                          </div>
                          <span className="text-xs text-gray-400 whitespace-nowrap">{fmtDate(v.created_at)}</span>
                        </div>
                        <div className="grid lg:grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Problem</p>
                            <p className="text-gray-700">{v.problem || '—'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Work Performed</p>
                            <p className="text-gray-700">{v.work_desc || '—'}</p>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between text-sm">
                          <span className="text-gray-500">Master: <span className="text-gray-700">{v.master_name || '—'}</span></span>
                          <span className="font-semibold">{fmt(v.agreed_price)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </AdminLayout>
  )
}
