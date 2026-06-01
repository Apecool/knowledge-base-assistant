<template>
  <div class="knowledge-card" @click="handleClick">
    <div class="card-header">
      <h3 class="card-title">{{ item.title }}</h3>
      <span class="card-status" :class="item.status">{{ statusLabel }}</span>
    </div>
    <p class="card-content">{{ truncatedContent }}</p>
    <div class="card-footer">
      <span class="card-category" v-if="item.category">{{ item.category }}</span>
      <span class="card-date">{{ formattedDate }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { KnowledgeItemResponse } from '../../types/api'

const props = defineProps<{
  item: KnowledgeItemResponse
}>()

const router = useRouter()

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档',
  }
  return labels[props.item.status] || props.item.status
})

const truncatedContent = computed(() => {
  const maxLength = 120
  if (props.item.content.length > maxLength) {
    return props.item.content.slice(0, maxLength) + '...'
  }
  return props.item.content
})

const formattedDate = computed(() => {
  const date = new Date(props.item.updated_at)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
})

function handleClick() {
  router.push({ name: 'knowledge-detail', params: { id: props.item.id } })
}
</script>

<style scoped>
.knowledge-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e8e8e8;
}

.knowledge-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
  flex: 1;
  margin-right: 12px;
  line-height: 1.4;
}

.card-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.card-status.draft {
  background: #fff7e6;
  color: #d48806;
}

.card-status.published {
  background: #f6ffed;
  color: #389e0d;
}

.card-status.archived {
  background: #f5f5f5;
  color: #999;
}

.card-content {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-category {
  font-size: 12px;
  padding: 2px 8px;
  background: #f0f2ff;
  color: #667eea;
  border-radius: 10px;
}

.card-date {
  font-size: 12px;
  color: #999;
}
</style>