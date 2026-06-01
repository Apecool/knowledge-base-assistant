<template>
  <div class="knowledge-detail-page">
    <div v-if="loading">
      <LoadingSpinner :visible="true" text="加载中..." />
    </div>

    <div v-else-if="item" class="detail-content">
      <div class="detail-header">
        <button class="btn btn-back" @click="goBack">← 返回</button>
        <div class="detail-actions" v-if="!editing">
          <button class="btn btn-edit" @click="startEdit">编辑</button>
          <button class="btn btn-delete" @click="handleDelete">删除</button>
        </div>
      </div>

      <KnowledgeEditor
        v-if="editing"
        :initial-data="item"
        :edit-mode="true"
        @save="handleUpdate"
        @cancel="editing = false"
      />

      <div v-else class="item-detail">
        <div class="item-header">
          <h1 class="item-title">{{ item.title }}</h1>
          <span class="item-status" :class="item.status">{{ statusLabel }}</span>
        </div>

        <div class="item-meta">
          <span v-if="item.category" class="meta-tag">{{ item.category }}</span>
          <span class="meta-date">更新于 {{ formattedDate }}</span>
        </div>

        <div class="item-content" v-html="renderedContent"></div>

        <div class="item-footer" v-if="item.tags || item.source">
          <div class="item-tags" v-if="item.tags">
            <span class="tag" v-for="tag in tagList" :key="tag">{{ tag }}</span>
          </div>
          <div class="item-source" v-if="item.source">
            来源：{{ item.source }}
          </div>
        </div>
      </div>
    </div>

    <div v-else class="not-found">
      <p>未找到知识条目</p>
      <button class="btn btn-back" @click="goBack">返回列表</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKnowledgeStore } from '../stores/knowledge'
import { storeToRefs } from 'pinia'
import KnowledgeEditor from '../components/knowledge/KnowledgeEditor.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const knowledgeStore = useKnowledgeStore()
const { currentItem: item, loading } = storeToRefs(knowledgeStore)
const editing = ref(false)

const statusLabel = computed(() => {
  const labels: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
  return labels[item.value?.status || ''] || item.value?.status
})

const formattedDate = computed(() => {
  if (!item.value) return ''
  return new Date(item.value.updated_at).toLocaleString('zh-CN')
})

const tagList = computed(() => {
  if (!item.value?.tags) return []
  return item.value.tags.split(',').map(t => t.trim()).filter(Boolean)
})

const renderedContent = computed(() => {
  if (!item.value?.content) return ''
  return item.value.content.replace(/\n/g, '<br>')
})

onMounted(() => {
  const id = Number(route.params.id)
  if (id) {
    knowledgeStore.fetchItem(id)
  }
})

function goBack() {
  router.push({ name: 'home' })
}

function startEdit() {
  editing.value = true
}

async function handleUpdate(data: { title: string; content: string; category?: string; tags?: string; source?: string }) {
  if (!item.value) return
  try {
    await knowledgeStore.updateItem(item.value.id, data)
    editing.value = false
  } catch (err: any) {
    alert('保存失败: ' + (err.response?.data?.detail || err.message || '未知错误'))
  }
}

async function handleDelete() {
  if (!item.value) return
  if (confirm('确定要删除这条知识条目吗？')) {
    await knowledgeStore.deleteItem(item.value.id)
    router.push({ name: 'home' })
  }
}
</script>

<style scoped>
.knowledge-detail-page {
  max-width: 900px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.btn-back {
  background: white;
  color: #666;
  border-color: #d9d9d9;
}

.btn-back:hover {
  border-color: #667eea;
  color: #667eea;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.btn-edit {
  background: #667eea;
  color: white;
}

.btn-edit:hover {
  background: #5a6fd6;
}

.btn-delete {
  background: white;
  color: #ff4d4f;
  border-color: #ff4d4f;
}

.btn-delete:hover {
  background: #ff4d4f;
  color: white;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.item-title {
  font-size: 26px;
  color: #333;
  margin: 0;
}

.item-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}

.item-status.draft { background: #fff7e6; color: #d48806; }
.item-status.published { background: #f6ffed; color: #389e0d; }
.item-status.archived { background: #f5f5f5; color: #999; }

.item-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}

.meta-tag {
  font-size: 12px;
  padding: 2px 8px;
  background: #f0f2ff;
  color: #667eea;
  border-radius: 10px;
}

.meta-date {
  font-size: 13px;
  color: #999;
}

.item-content {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 24px;
  line-height: 1.8;
  font-size: 15px;
  color: #333;
  white-space: pre-wrap;
}

.item-footer {
  margin-top: 20px;
}

.item-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.tag {
  font-size: 12px;
  padding: 3px 10px;
  background: #f5f5f5;
  color: #666;
  border-radius: 10px;
}

.item-source {
  font-size: 13px;
  color: #999;
}

.not-found {
  text-align: center;
  padding: 60px;
  color: #999;
}
</style>