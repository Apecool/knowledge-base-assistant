import apiClient from './index'
import type { KnowledgeItemResponse } from '../types/api'

export interface FileParseResult {
  title: string
  content: string
  file_type: string
  file_size: number
}

export const uploadAPI = {
  /**
   * Parse a file without saving it (POST /api/v1/knowledge/parse-file).
   * Returns extracted title + content for user to preview before saving.
   */
  async parseFile(file: File): Promise<FileParseResult> {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/api/v1/knowledge/parse-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60s for parsing
    })
  },

  /**
   * Upload a file and create a knowledge item directly.
   * Indexing runs in background — response returns quickly.
   */
  async uploadFile(
    file: File,
    category?: string,
    tags?: string,
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    if (category) formData.append('category', category)
    if (tags) formData.append('tags', tags)
    formData.append('source', file.name)

    return apiClient.post('/api/v1/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60s — indexing runs in background, response is fast
    })
  },
}