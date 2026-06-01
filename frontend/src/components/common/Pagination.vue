<template>
  <div class="pagination" v-if="totalPages > 1">
    <button
      class="page-btn"
      :disabled="current === 1"
      @click="$emit('page-change', current - 1)"
    >
      上一页
    </button>

    <button
      v-for="page in visiblePages"
      :key="page"
      class="page-btn"
      :class="{ active: page === current }"
      @click="$emit('page-change', page)"
    >
      {{ page }}
    </button>

    <button
      class="page-btn"
      :disabled="current === totalPages"
      @click="$emit('page-change', current + 1)"
    >
      下一页
    </button>
    <span class="page-info">共 {{ total }} 条</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  current: number
  total: number
  pageSize: number
}>()

defineEmits<{
  'page-change': [page: number]
}>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

const visiblePages = computed(() => {
  const pages: number[] = []
  const start = Math.max(1, props.current - 2)
  const end = Math.min(totalPages.value, props.current + 2)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 0;
  justify-content: center;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  color: #667eea;
  border-color: #667eea;
}

.page-btn:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.page-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.page-info {
  margin-left: 12px;
  color: #999;
  font-size: 13px;
}
</style>