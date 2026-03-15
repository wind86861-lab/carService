import React from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBadge from './StatusBadge'
import { Car, Calendar, User } from 'lucide-react'

function fmt(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('ru-RU') + ' UZS'
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function OrderCard({ order }) {
  const navigate = useNavigate()
  const car = `${order.brand || ''} ${order.model || ''}`.trim() || '—'

  return (
    <div
      onClick={() => navigate(`/orders/${order.order_number}`)}
      className="bg-white border border-gray-100 rounded-xl p-4 hover:border-blue-200 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="font-mono font-bold text-blue-700 text-sm">{order.order_number}</span>
        <StatusBadge status={order.status} />
      </div>
      <div className="space-y-1.5 text-sm text-gray-600">
        <div className="flex items-center gap-1.5">
          <Car size={13} className="text-gray-400" />
          <span>{car}</span>
          {order.plate && <span className="ml-auto font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">{order.plate}</span>}
        </div>
        {order.client_name && (
          <div className="flex items-center gap-1.5">
            <User size={13} className="text-gray-400" />
            <span>{order.client_name}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <Calendar size={13} className="text-gray-400" />
          <span>{fmtDate(order.created_at)}</span>
        </div>
      </div>
      {order.agreed_price > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-50 flex justify-between text-xs">
          <span className="text-gray-500">Agreed</span>
          <span className="font-semibold">{fmt(order.agreed_price)}</span>
        </div>
      )}
    </div>
  )
}
