<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="app-title">知识库助手</h1>
    </div>
    <div class="header-right">
      <SearchBar />
      <div class="user-info">
        <span class="username">{{ user?.username }}</span>
        <button class="btn-logout" @click="handleLogout">退出</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import SearchBar from '../common/SearchBar.vue'

const authStore = useAuthStore()
const router = useRouter()
const user = authStore.user

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 14px;
  opacity: 0.9;
}

.btn-logout {
  padding: 6px 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 4px;
  background: transparent;
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: white;
}
</style>