<template>
  <div class="knowledge-base-page">
    <div class="page-header">
      <h2>知识库</h2>
      <button class="btn btn-primary" @click="showEditor = true">+ 新建条目</button>
    </div>

    <KnowledgeEditor
      v-if="showEditor"
      @save="handleCreate"
      @cancel="showEditor = false"
    />

    <div v-else>
      <div class="filter-bar">
        <select v-model="filter.category" class="filter-select" @change="handleFilter">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <select v-model="filter.status" class="filter-select" @change="handleFilter">
          <option value="">全部状态</option>
          <option value="published">已发布</option>
          <option value="draft">草稿</option>
          <option value="archived">已归档</option>
        </select>
      </div>

      <LoadingSpinner :visible="loading" text="加载中..." />
      <KnowledgeList :items="items" :loading="loading" />

      <Pagination
        :current="currentPage"
        :total="total"
        :page-size="pageSize"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'
import { storeToRefs } from 'pinia'
import KnowledgeList from '../components/knowledge/KnowledgeList.vue'
import KnowledgeEditor from '../components/knowledge/KnowledgeEditor.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import Pagination from '../components/common/Pagination.vue'

const knowledgeStore = useKnowledgeStore()
const { items, total, currentPage, pageSize, loading } = storeToRefs(knowledgeStore)

const showEditor = ref(false)

const filter = ref({
  category: '',
  status: '',
})

const categories = ['技术', '产品', '设计', '运营', '管理', '其他']

onMounted(() => {
  knowledgeStore.fetchItems()
})

function handleFilter() {
  knowledgeStore.fetchItems({
    category: filter.value.category || undefined,
    status: filter.value.status || undefined,
  })
}

function handlePageChange(page: number) {
  knowledgeStore.fetchItems({ page, category: filter.value.category || undefined, status: filter.value.status || undefined })
}

async function handleCreate(data: { title: string; content: string; category?: string; tags?: string; source?: string }) {
  try {
    await knowledgeStore.createItem(data)
    showEditor.value = false
  } catch (err: any) {
    alert('创建失败: ' + (err.response?.data?.detail || err.message || '未知错误'))
  }
}
</script>

<style scoped>
.knowledge-base-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  color: #333;
  margin: 0;
}

.btn {
  padding: 8px 20px;
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

.btn-primary:hover {
  background: #5a6fd6;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: white;
  cursor: pointer;
}

.filter-select:focus {
  border-color: #667eea;
}
</style>