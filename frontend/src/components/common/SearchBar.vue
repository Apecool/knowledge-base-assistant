<template>
  <div class="search-bar">
    <input
      v-model="query"
      type="text"
      placeholder="搜索知识库..."
      class="search-input"
      @keyup.enter="handleSearch"
    />
    <button class="search-btn" @click="handleSearch">搜索</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const query = ref('')

function handleSearch() {
  if (query.value.trim()) {
    router.push({ name: 'search', query: { q: query.value.trim() } })
  }
}
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 240px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.6);
}

.search-btn {
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 6px;
  background: transparent;
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.search-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>