import React from 'react'
import { AlertTriangle, X } from 'lucide-react'

export default function ConfirmDialog({ title, message, confirmLabel = 'Tasdiqlash', cancelLabel = 'Bekor qilish', onConfirm, onClose, danger = true, loading = false }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-start gap-3 p-6">
          {danger && (
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle size={18} className="text-red-600" />
            </div>
          )}
          <div className="flex-1">
            <h3 className="font-bold text-gray-900">{title}</h3>
            <p className="mt-1 text-sm text-gray-500">{message}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>
        <div className="px-6 pb-6 flex gap-2 justify-end">
          <button onClick={onClose} disabled={loading} className="btn-secondary">
            {cancelLabel}
          </button>
          <button onClick={onConfirm} disabled={loading} className={danger ? 'btn-danger' : 'btn-primary'}>
            {loading ? 'Bajarilmoqda…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
