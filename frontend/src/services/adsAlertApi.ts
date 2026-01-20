import axios from 'axios'
import {
  Chat, ChatCreate, ChatUpdate, ChatListParams,
  Promotion, PromotionCreate, PromotionUpdate, PromotionListParams,
  PromotionScheduleRequest, BroadcastResponse,
  MediaFolder, FolderCreate, FolderTreeNode,
  MediaFile, MediaUploadResponse, MediaDeleteResponse, MediaListParams,
  AdsAlertStats
} from '../types/adsAlert'

// Use same API base URL as main api.ts
const API_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://web-production-3ed15.up.railway.app' : 'http://localhost:8000')

const adsAlertApi = axios.create({
  baseURL: `${API_URL}/ads-alert`,
  timeout: 30000, // Longer timeout for uploads
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth interceptor
adsAlertApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors by redirecting to login
adsAlertApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const adsAlertService = {
  // ==================== Stats ====================
  async getStats(): Promise<AdsAlertStats> {
    const response = await adsAlertApi.get('/stats')
    return response.data
  },

  // ==================== Chats ====================
  async listChats(params?: ChatListParams): Promise<Chat[]> {
    const response = await adsAlertApi.get('/chats', { params })
    return response.data
  },

  async getChat(id: string): Promise<Chat> {
    const response = await adsAlertApi.get(`/chats/${id}`)
    return response.data
  },

  async createChat(data: ChatCreate): Promise<Chat> {
    const response = await adsAlertApi.post('/chats', data)
    return response.data
  },

  async updateChat(id: string, data: ChatUpdate): Promise<Chat> {
    const response = await adsAlertApi.put(`/chats/${id}`, data)
    return response.data
  },

  async deleteChat(id: string): Promise<void> {
    await adsAlertApi.delete(`/chats/${id}`)
  },

  // ==================== Promotions ====================
  async listPromotions(params?: PromotionListParams): Promise<Promotion[]> {
    const response = await adsAlertApi.get('/promotions', { params })
    return response.data
  },

  async getPromotion(id: string): Promise<Promotion> {
    const response = await adsAlertApi.get(`/promotions/${id}`)
    return response.data
  },

  async createPromotion(data: PromotionCreate): Promise<Promotion> {
    const response = await adsAlertApi.post('/promotions', data)
    return response.data
  },

  async updatePromotion(id: string, data: PromotionUpdate): Promise<Promotion> {
    const response = await adsAlertApi.put(`/promotions/${id}`, data)
    return response.data
  },

  async deletePromotion(id: string): Promise<void> {
    await adsAlertApi.delete(`/promotions/${id}`)
  },

  async sendPromotion(id: string): Promise<BroadcastResponse> {
    const response = await adsAlertApi.post(`/promotions/${id}/send`)
    return response.data
  },

  async schedulePromotion(id: string, data: PromotionScheduleRequest): Promise<Promotion> {
    const response = await adsAlertApi.post(`/promotions/${id}/schedule`, data)
    return response.data
  },

  // ==================== Folders ====================
  async listFolders(parentId?: string): Promise<MediaFolder[]> {
    const params = parentId ? { parent_id: parentId } : undefined
    const response = await adsAlertApi.get('/folders', { params })
    return response.data
  },

  async getFolderTree(): Promise<FolderTreeNode[]> {
    const response = await adsAlertApi.get('/folders/tree')
    return response.data
  },

  async createFolder(data: FolderCreate): Promise<MediaFolder> {
    const response = await adsAlertApi.post('/folders', data)
    return response.data
  },

  async deleteFolder(id: string): Promise<void> {
    await adsAlertApi.delete(`/folders/${id}`)
  },

  // ==================== Media ====================
  async listMedia(params?: MediaListParams): Promise<MediaFile[]> {
    const response = await adsAlertApi.get('/media', { params })
    return response.data
  },

  async searchMedia(query: string, limit?: number): Promise<MediaFile[]> {
    const response = await adsAlertApi.get('/media/search', {
      params: { q: query, limit }
    })
    return response.data
  },

  async uploadMedia(file: File, folderId?: string): Promise<MediaUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (folderId) {
      formData.append('folder_id', folderId)
    }

    const response = await adsAlertApi.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async deleteMedia(id: string): Promise<MediaDeleteResponse> {
    const response = await adsAlertApi.delete(`/media/${id}`)
    return response.data
  },

  // ==================== Helpers ====================
  /**
   * Get media type category from MIME type
   */
  getMediaCategory(mimeType: string): 'image' | 'video' | 'document' {
    if (mimeType.startsWith('image/')) return 'image'
    if (mimeType.startsWith('video/')) return 'video'
    return 'document'
  },

  /**
   * Format file size for display
   */
  formatFileSize(bytes?: number): string {
    if (!bytes) return 'Unknown'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  },

  /**
   * Check if file type is allowed
   */
  isAllowedFileType(mimeType: string): boolean {
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'video/mp4', 'video/webm', 'video/quicktime',
      'application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    return allowedTypes.includes(mimeType)
  }
}

export default adsAlertService
