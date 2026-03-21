import React, { useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../App'
import {
  LayoutDashboard, ShoppingCart, Users, Wrench,
  DollarSign, Send, MessageSquare, Car, LogOut, Menu, X,
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
  const location = useLocation()
  const { logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const sidebarContent = (
    <>
      <div className="px-5 py-5 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-gray-900">AutoService</h1>
          <p className="text-xs text-gray-400 mt-0.5">Boshqaruv paneli</p>
        </div>
        <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-1 text-gray-400 hover:text-gray-600"><X size={20} /></button>
      </div>
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setSidebarOpen(false)}
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
          onClick={() => { logout(); navigate('/admin/login') }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut size={16} /> Chiqish
        </button>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Mobile top bar */}
      <div className="fixed top-0 left-0 right-0 z-30 bg-white border-b border-gray-100 flex items-center gap-3 px-4 py-3 lg:hidden">
        <button onClick={() => setSidebarOpen(true)} className="p-1 text-gray-600"><Menu size={22} /></button>
        <span className="font-bold text-sm text-gray-900">AutoService</span>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-56 bg-white border-r border-gray-100 flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-auto
      `}>
        {sidebarContent}
      </aside>

      <main className="flex-1 overflow-auto pt-14 lg:pt-0">{children}</main>
    </div>
  )
}
