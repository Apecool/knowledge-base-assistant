<template>
  <div class="login-page">
    <div class="login-card">
      <h2 class="login-title">{{ isRegister ? '注册' : '登录' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" class="form-input" placeholder="请输入用户名" required />
        </div>
        <div class="form-group" v-if="isRegister">
          <label>邮箱</label>
          <input v-model="form.email" type="email" class="form-input" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" class="form-input" placeholder="请输入密码" required />
        </div>
        <div class="form-group" v-if="isRegister">
          <label>姓名（可选）</label>
          <input v-model="form.full_name" type="text" class="form-input" placeholder="请输入姓名" />
        </div>
        <p v-if="error" class="error-message">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>
      <p class="switch-mode">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="toggleMode">{{ isRegister ? '去登录' : '去注册' }}</a>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const isRegister = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  full_name: '',
})

function toggleMode() {
  isRegister.value = !isRegister.value
  error.value = ''
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    if (isRegister.value) {
      await authStore.register({
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
      })
    } else {
      await authStore.login(form.username, form.password)
    }
    router.push({ name: 'home' })
  } catch (err: any) {
    error.value = err.response?.data?.detail || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.login-title {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
  font-size: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #555;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.btn {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd6;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 15px;
}

.error-message {
  color: #ff4d4f;
  font-size: 13px;
  text-align: center;
  margin-bottom: 12px;
}

.switch-mode {
  text-align: center;
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}

.switch-mode a {
  color: #667eea;
  text-decoration: none;
}

.switch-mode a:hover {
  text-decoration: underline;
}
</style>