import apiClient from './index'
import type { KnowledgeItemResponse, KnowledgeItemList, KnowledgeItemCreate } from '../types/api'

export const knowledgeAPI = {
  async list(params?: {
    page?: number
    page_size?: number
    category?: string
    status?: string
    search?: string
  }): Promise<KnowledgeItemList> {
    return apiClient.get('/api/v1/knowledge/', { params })
  },

  async get(id: number): Promise<KnowledgeItemResponse> {
    return apiClient.get(`/api/v1/knowledge/${id}`)
  },

  async create(data: KnowledgeItemCreate): Promise<KnowledgeItemResponse> {
    return apiClient.post('/api/v1/knowledge/', data)
  },

  async update(id: number, data: Partial<KnowledgeItemCreate>): Promise<KnowledgeItemResponse> {
    return apiClient.put(`/api/v1/knowledge/${id}`, data)
  },

  async delete(id: number): Promise<void> {
    return apiClient.delete(`/api/v1/knowledge/${id}`)
  },

  async search(params: { q: string; category?: string; limit?: number }): Promise<KnowledgeItemResponse[]> {
    return apiClient.get('/api/v1/search/', { params })
  },
}