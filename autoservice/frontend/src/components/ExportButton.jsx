import React, { useState, useRef, useEffect } from 'react'
import { Download, ChevronDown } from 'lucide-react'
import { exportFinancials } from '../api/admin'

export default function ExportButton({ filters = {} }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const download = (format) => {
    setOpen(false)
    const url = exportFinancials(filters, format)
    const a = document.createElement('a')
    a.href = url
    a.download = `report.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(o => !o)} className="btn-secondary">
        <Download size={16} /> Export <ChevronDown size={14} />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 min-w-[160px] overflow-hidden">
          <button onClick={() => download('xlsx')} className="w-full px-4 py-2.5 text-sm text-left hover:bg-gray-50 flex items-center gap-2">
            <span className="text-green-600">📊</span> Download Excel
          </button>
          <button onClick={() => download('pdf')} className="w-full px-4 py-2.5 text-sm text-left hover:bg-gray-50 flex items-center gap-2">
            <span className="text-red-600">📄</span> Download PDF
          </button>
        </div>
      )}
    </div>
  )
}
