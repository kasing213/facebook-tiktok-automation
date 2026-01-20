// Types for the Ads Alert promotional messaging system

export type PromotionStatus = 'draft' | 'scheduled' | 'sent' | 'cancelled'
export type MediaType = 'text' | 'image' | 'video' | 'document' | 'mixed'
export type TargetType = 'all' | 'selected'
export type BroadcastStatus = 'pending' | 'sent' | 'failed'

// Chat types
export interface Chat {
  id: string
  tenant_id: string
  platform: string
  chat_id: string
  chat_name?: string
  customer_name?: string
  tags: string[]
  subscribed: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ChatCreate {
  platform?: string
  chat_id: string
  chat_name?: string
  customer_name?: string
  tags?: string[]
}

export interface ChatUpdate {
  chat_name?: string
  customer_name?: string
  tags?: string[]
  subscribed?: boolean
}

// Promotion types
export interface Promotion {
  id: string
  tenant_id: string
  title: string
  content?: string
  status: PromotionStatus
  media_urls: string[]
  media_type: MediaType
  scheduled_at?: string
  target_type: TargetType
  target_chat_ids: string[]
  sent_at?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface PromotionCreate {
  title: string
  content?: string
  media_urls?: string[]
  media_type?: MediaType
  target_type?: TargetType
  target_chat_ids?: string[]
  scheduled_at?: string
}

export interface PromotionUpdate {
  title?: string
  content?: string
  media_urls?: string[]
  media_type?: MediaType
  target_type?: TargetType
  target_chat_ids?: string[]
  scheduled_at?: string
  status?: PromotionStatus
}

export interface PromotionScheduleRequest {
  scheduled_at: string
}

// Folder types
export interface MediaFolder {
  id: string
  tenant_id: string
  name: string
  parent_id?: string
  created_by?: string
  created_at: string
}

export interface FolderCreate {
  name: string
  parent_id?: string
}

export interface FolderTreeNode {
  id: string
  name: string
  parent_id?: string
  children: FolderTreeNode[]
}

// Media types
export interface MediaFile {
  id: string
  tenant_id: string
  folder_id?: string
  filename: string
  original_filename?: string
  storage_path: string
  url: string
  file_type: string
  file_size?: number
  thumbnail_url?: string
  width?: number
  height?: number
  duration?: number
  created_by?: string
  created_at: string
}

export interface MediaUploadResponse {
  id: string
  filename: string
  storage_path: string
  url: string
  file_type: string
  file_size: number
}

export interface MediaDeleteResponse {
  id: string
  filename: string
  deleted: boolean
}

// Broadcast types
export interface BroadcastResult {
  chat_id: string
  success: boolean
  error?: string
}

export interface BroadcastResponse {
  promotion_id: string
  total: number
  sent: number
  failed: number
  results: BroadcastResult[]
}

// Stats types
export interface AdsAlertStats {
  total_chats: number
  subscribed_chats: number
  total_promotions: number
  draft_promotions: number
  scheduled_promotions: number
  sent_promotions: number
  total_media: number
  total_folders: number
}

// List params
export interface ChatListParams {
  subscribed_only?: boolean
  tags?: string
  limit?: number
}

export interface PromotionListParams {
  status?: PromotionStatus
  limit?: number
}

export interface MediaListParams {
  folder_id?: string
  file_type?: string
  limit?: number
}
