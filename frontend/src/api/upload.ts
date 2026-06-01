import apiClient from './index'

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
      timeout: 300000,
    })
  },

  /**
   * Upload a file and create a knowledge item directly.
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
      timeout: 300000,
    })
  },
}