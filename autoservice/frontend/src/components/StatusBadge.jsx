import React from 'react'

const STATUS_CONFIG = {
  new:         { label: 'New',         bg: 'bg-gray-100',   text: 'text-gray-700',  dot: 'bg-gray-400'   },
  preparation: { label: 'Preparation', bg: 'bg-yellow-100', text: 'text-yellow-800', dot: 'bg-yellow-500' },
  in_process:  { label: 'In Process',  bg: 'bg-blue-100',   text: 'text-blue-800',  dot: 'bg-blue-500'   },
  ready:       { label: 'Ready',       bg: 'bg-green-100',  text: 'text-green-800', dot: 'bg-green-500'  },
  closed:      { label: 'Closed',      bg: 'bg-purple-100', text: 'text-purple-800', dot: 'bg-purple-500' },
}

export default function StatusBadge({ status, size = 'sm' }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.new
  const padding = size === 'lg' ? 'px-3 py-1.5 text-sm' : 'px-2.5 py-0.5 text-xs'
  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full ${cfg.bg} ${cfg.text} ${padding}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}
