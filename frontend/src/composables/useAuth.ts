import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

export function useAuth() {
  const authStore = useAuthStore()

  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const currentUser = computed(() => authStore.user)

  return {
    isAuthenticated,
    currentUser,
    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout,
  }
}