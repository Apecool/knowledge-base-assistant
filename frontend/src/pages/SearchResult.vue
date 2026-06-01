<template>
  <div class="search-result-page">
    <div class="page-header">
      <h2>搜索结果</h2>
    </div>

    <div class="search-box">
      <input
        v-model="query"
        type="text"
        class="search-input"
        placeholder="输入关键词搜索..."
        @keyup.enter="handleSearch"
      />
      <button class="btn btn-primary" @click="handleSearch">搜索</button>
    </div>

    <LoadingSpinner :visible="loading" text="搜索中..." />

    <div v-if="!loading && results.length > 0" class="result-count">
      找到 {{ results.length }} 条结果
    </div>

    <div v-if="!loading && results.length > 0" class="result-list">
      <KnowledgeCard v-for="item in results" :key="item.id" :item="item" />
    </div>

    <div v-if="!loading && searched && results.length === 0" class="empty-state">
      <p>没有找到相关结果</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { knowledgeAPI } from '../api/knowledge'
import type { KnowledgeItemResponse } from '../types/api'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import KnowledgeCard from '../components/knowledge/KnowledgeCard.vue'

const route = useRoute()
const query = ref('')
const results = ref<KnowledgeItemResponse[]>([])
const loading = ref(false)
const searched = ref(false)

onMounted(() => {
  const q = route.query.q as string
  if (q) {
    query.value = q
    handleSearch()
  }
})

async function handleSearch() {
  if (!query.value.trim()) return
  loading.value = true
  searched.value = true
  try {
    results.value = await knowledgeAPI.search({ q: query.value.trim() })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-result-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header h2 {
  font-size: 22px;
  color: #333;
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 15px;
  outline: none;
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.btn {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a6fd6;
}

.result-count {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.result-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
  font-size: 15px;
}
</style>