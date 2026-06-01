<template>
  <div class="knowledge-list">
    <div v-if="items.length === 0 && !loading" class="empty-state">
      <p>暂无知识条目</p>
    </div>
    <div v-else class="list-grid">
      <KnowledgeCard v-for="item in items" :key="item.id" :item="item" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { KnowledgeItemResponse } from '../../types/api'
import KnowledgeCard from './KnowledgeCard.vue'

defineProps<{
  items: KnowledgeItemResponse[]
  loading: boolean
}>()
</script>

<style scoped>
.knowledge-list {
  padding: 16px 0;
}

.list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 15px;
}
</style>