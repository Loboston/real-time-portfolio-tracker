import { api } from './client'

export async function login(email, password) {
  const data = await api.post('/auth/login', { email, password })
  localStorage.setItem('token', data.access_token)
  return data
}

export async function register(email, password) {
  const data = await api.post('/auth/register', { email, password })
  localStorage.setItem('token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('token')
}

export function getStoredToken() {
  return localStorage.getItem('token')
}
