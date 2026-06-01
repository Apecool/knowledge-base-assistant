import apiClient from './index'
import type { TokenResponse, UserLogin, UserCreate } from '../types/api'

export const authAPI = {
  async login(data: UserLogin): Promise<TokenResponse> {
    return apiClient.post('/api/v1/auth/login', data)
  },

  async register(data: UserCreate): Promise<TokenResponse> {
    return apiClient.post('/api/v1/auth/register', data)
  },
}