export interface UserResponse {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface KnowledgeItemResponse {
  id: number
  title: string
  content: string
  category: string | null
  tags: string | null
  status: string
  visibility: string
  source: string | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface KnowledgeItemList {
  items: KnowledgeItemResponse[]
  total: number
  page: number
  page_size: number
}

export interface KnowledgeItemCreate {
  title: string
  content: string
  category?: string
  tags?: string
  source?: string
  visibility?: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string
}