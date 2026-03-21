import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import {
  LayoutDashboard, ShoppingCart, Users, Wrench,
  DollarSign, Send, MessageSquare, Car, LogOut,
} from 'lucide-react'

const NAV = [
  { to: '/admin', label: 'Boshqaruv paneli', icon: LayoutDashboard, end: true },
  { to: '/admin/orders', label: 'Buyurtmalar', icon: ShoppingCart },
  { to: '/admin/clients', label: 'Mijozlar', icon: Users },
  { to: '/admin/masters', label: 'Ustalar', icon: Wrench },
  { to: '/admin/financials', label: 'Moliya', icon: DollarSign },
  { to: '/admin/broadcast', label: 'Xabar yuborish', icon: Send },
  { to: '/admin/feedbacks', label: 'Fikr-mulohazalar', icon: MessageSquare },
  { to: '/admin/cars', label: 'Mashina tarixi', icon: Car },
]

export default function AdminLayout({ children }) {
  const navigate = useNavigate()
  const { logout } = useAuth()

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-56 bg-white border-r border-gray-100 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-100">
          <h1 className="text-base font-bold text-gray-900">AutoService</h1>
          <p className="text-xs text-gray-400 mt-0.5">Boshqaruv paneli</p>
        </div>
        <nav className="flex-1 py-3 px-2 space-y-0.5">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-100">
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut size={16} /> Chiqish
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
