import React, { useState } from 'react'
import { X, AlertTriangle } from 'lucide-react'
import { formatWithSpaces, stripSpaces } from '../utils/formatNumber'

function fmt(n) {
  return Number(n || 0).toLocaleString('ru-RU') + ' UZS'
}

export default function CloseOrderModal({ order, onClose, onConfirm, loading }) {
  const [partsCost, setPartsCost] = useState('')
  const [error, setError] = useState('')

  const agreed = Number(order?.agreed_price || 0)
  const parts = parseFloat(stripSpaces(partsCost)) || 0
  const profit = agreed - parts
  const masterShare = profit * 0.4
  const serviceShare = profit * 0.6

  const handleConfirm = () => {
    if (!partsCost || isNaN(parts) || parts < 0) {
      setError('To\'g\'ri qismlar narxini kiriting (0 bo\'lishi mumkin)')
      return
    }
    setError('')
    onConfirm(parts)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-lg font-bold">Buyurtmani yopish {order?.order_number}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <label className="label">Ehtiyot qismlar narxi (UZS)</label>
            <input
              type="text"
              inputMode="numeric"
              className="input"
              placeholder="0"
              value={partsCost}
              onChange={(e) => { setPartsCost(formatWithSpaces(e.target.value)); setError('') }}
              autoFocus
            />
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>

          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Kelishilgan narx</span>
              <span className="font-medium">{fmt(agreed)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Qismlar narxi</span>
              <span className="font-medium">{fmt(parts)}</span>
            </div>
            <div className="border-t border-gray-200 pt-3 flex justify-between text-sm">
              <span className="text-gray-700 font-medium">Foyda</span>
              <span className={`font-bold ${profit < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                {profit < 0 && '⚠️ '}{fmt(profit)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-green-700">Usta ulushi (40%)</span>
              <span className="font-semibold text-green-700">{fmt(masterShare)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-blue-700">Servis ulushi (60%)</span>
              <span className="font-semibold text-blue-700">{fmt(serviceShare)}</span>
            </div>
          </div>

          {profit < 0 && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <span>Manfiy foyda: qismlar narxi kelishilgan narxdan oshib ketdi. Siz baribir buyurtmani yopishingiz mumkin.</span>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-100 flex gap-3 justify-end">
          <button className="btn-secondary" onClick={onClose} disabled={loading}>
            Bekor qilish
          </button>
          <button className="btn-danger" onClick={handleConfirm} disabled={loading}>
            {loading ? 'Yopilmoqda...' : 'Yopishni tasdiqlash'}
          </button>
        </div>
      </div>
    </div>
  )
}
