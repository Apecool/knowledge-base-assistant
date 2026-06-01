import { computed } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'

export function useKnowledge() {
  const store = useKnowledgeStore()

  const items = computed(() => store.items)
  const currentItem = computed(() => store.currentItem)
  const total = computed(() => store.total)
  const currentPage = computed(() => store.currentPage)
  const pageSize = computed(() => store.pageSize)
  const loading = computed(() => store.loading)

  return {
    items,
    currentItem,
    total,
    currentPage,
    pageSize,
    loading,
    fetchItems: store.fetchItems,
    fetchItem: store.fetchItem,
    createItem: store.createItem,
    updateItem: store.updateItem,
    deleteItem: store.deleteItem,
  }
}