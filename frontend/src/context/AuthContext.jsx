import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [owner, setOwner] = useState(() => {
    const stored = localStorage.getItem('owner')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)

  const login = async (email, password) => {
    const res = await authApi.login({ email, password })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    return res.data
  }

  const signup = async (email, password, restaurantName) => {
    const res = await authApi.signup({ email, password, restaurant_name: restaurantName })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    return res.data
  }

  const logout = () => {
    authApi.logout().catch(() => {})
    localStorage.removeItem('token')
    localStorage.removeItem('owner')
    setOwner(null)
  }

  return (
    <AuthContext.Provider value={{ owner, setOwner, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
