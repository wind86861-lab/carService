import React, { createContext, useContext, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewOrder from './pages/NewOrder'
import OrderDetail from './pages/OrderDetail'
import Statistics from './pages/Statistics'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminOrders from './pages/admin/AdminOrders'
import AdminOrderDetail from './pages/admin/AdminOrderDetail'
import AdminClients from './pages/admin/AdminClients'
import AdminClientProfile from './pages/admin/AdminClientProfile'
import AdminMasters from './pages/admin/AdminMasters'
import AdminMasterProfile from './pages/admin/AdminMasterProfile'
import AdminFinancials from './pages/admin/AdminFinancials'
import AdminBroadcast from './pages/admin/AdminBroadcast'
import AdminFeedbacks from './pages/admin/AdminFeedbacks'
import AdminCarHistory from './pages/admin/AdminCarHistory'

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [role, setRole] = useState(() => localStorage.getItem('role'))

  const login = (newToken, newRole) => {
    localStorage.setItem('token', newToken)
    localStorage.setItem('role', newRole)
    setToken(newToken)
    setRole(newRole)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setToken(null)
    setRole(null)
  }

  return (
    <AuthContext.Provider value={{ token, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const { token, role } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (role !== 'admin') return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/new-order" element={<ProtectedRoute><NewOrder /></ProtectedRoute>} />
          <Route path="/orders/:orderNumber" element={<ProtectedRoute><OrderDetail /></ProtectedRoute>} />
          <Route path="/statistics" element={<ProtectedRoute><Statistics /></ProtectedRoute>} />
          <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
          <Route path="/admin/orders" element={<AdminRoute><AdminOrders /></AdminRoute>} />
          <Route path="/admin/orders/:orderNumber" element={<AdminRoute><AdminOrderDetail /></AdminRoute>} />
          <Route path="/admin/clients" element={<AdminRoute><AdminClients /></AdminRoute>} />
          <Route path="/admin/clients/:id" element={<AdminRoute><AdminClientProfile /></AdminRoute>} />
          <Route path="/admin/masters" element={<AdminRoute><AdminMasters /></AdminRoute>} />
          <Route path="/admin/masters/:id" element={<AdminRoute><AdminMasterProfile /></AdminRoute>} />
          <Route path="/admin/financials" element={<AdminRoute><AdminFinancials /></AdminRoute>} />
          <Route path="/admin/broadcast" element={<AdminRoute><AdminBroadcast /></AdminRoute>} />
          <Route path="/admin/feedbacks" element={<AdminRoute><AdminFeedbacks /></AdminRoute>} />
          <Route path="/admin/cars" element={<AdminRoute><AdminCarHistory /></AdminRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
