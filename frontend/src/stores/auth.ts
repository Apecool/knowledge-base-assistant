import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api/auth'
import type { UserResponse } from '../types/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<UserResponse | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const response = await authAPI.login({ username, password })
    token.value = response.access_token
    user.value = response.user
    localStorage.setItem('access_token', response.access_token)
    return response
  }

  async function register(data: { username: string; email: string; password: string; full_name?: string }) {
    const response = await authAPI.register(data)
    token.value = response.access_token
    user.value = response.user
    localStorage.setItem('access_token', response.access_token)
    return response
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
  }
})