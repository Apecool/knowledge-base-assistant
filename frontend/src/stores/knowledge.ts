import { defineStore } from 'pinia'
import { ref } from 'vue'
import { knowledgeAPI } from '../api/knowledge'
import type { KnowledgeItemResponse, KnowledgeItemList } from '../types/api'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const items = ref<KnowledgeItemResponse[]>([])
  const currentItem = ref<KnowledgeItemResponse | null>(null)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)

  async function fetchItems(params?: {
    page?: number
    page_size?: number
    category?: string
    status?: string
    search?: string
  }) {
    loading.value = true
    try {
      const result = await knowledgeAPI.list(params)
      items.value = result.items
      total.value = result.total
      currentPage.value = result.page
      pageSize.value = result.page_size
    } finally {
      loading.value = false
    }
  }

  async function fetchItem(id: number) {
    loading.value = true
    try {
      currentItem.value = await knowledgeAPI.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createItem(data: { title: string; content: string; category?: string; tags?: string; source?: string }) {
    const result = await knowledgeAPI.create(data)
    await fetchItems()
    return result
  }

  async function updateItem(id: number, data: Partial<KnowledgeItemResponse>) {
    const result = await knowledgeAPI.update(id, data)
    if (currentItem.value?.id === id) {
      currentItem.value = result
    }
    await fetchItems()
    return result
  }

  async function deleteItem(id: number) {
    await knowledgeAPI.delete(id)
    if (currentItem.value?.id === id) {
      currentItem.value = null
    }
    await fetchItems()
  }

  return {
    items,
    currentItem,
    total,
    currentPage,
    pageSize,
    loading,
    fetchItems,
    fetchItem,
    createItem,
    updateItem,
    deleteItem,
  }
})