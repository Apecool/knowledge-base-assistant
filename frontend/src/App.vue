<template>
  <div id="app-container">
    <AppHeader v-if="isAuthenticated" />
    <div class="main-content" :class="{ 'with-sidebar': isAuthenticated }">
      <AppSidebar v-if="isAuthenticated" />
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import apiClient from './api'

const authStore = useAuthStore()
const router = useRouter()
const isAuthenticated = computed(() => authStore.isAuthenticated)

// Verify token is still valid on startup
onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      // Call a lightweight endpoint to verify the token
      await apiClient.get('/health')
    } catch {
      // Token invalid or backend unavailable — clear it
      authStore.logout()
      router.push({ name: 'login' })
    }
  }
})
</script>

<style scoped>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  display: flex;
  flex: 1;
}

.with-sidebar {
  display: flex;
}

.content-area {
  flex: 1;
  padding: 24px;
  background-color: #f5f7fa;
}
</style>