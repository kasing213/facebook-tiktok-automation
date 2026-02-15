export interface OAuthToken {
  id: string
  account_ref: string
  account_name?: string
  is_valid: boolean
  expires_at: string | null
}

export interface PlatformStatus {
  connected: boolean
  valid_tokens: number
  tokens?: OAuthToken[]
  accounts?: OAuthToken[]
}

export interface AuthStatus {
  tenant_id: string
  platforms?: {
    facebook: PlatformStatus
    tiktok: PlatformStatus
  }
  facebook?: PlatformStatus
  tiktok?: PlatformStatus
}

export interface OAuthResult {
  success: boolean
  platform: string
  message?: string
  error?: string
  tenant_id?: string
  token_id?: string
  expires_at?: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
  turnstileToken?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user?: {
    id: string
    username: string
    email?: string
    tenant_id: string
  }
}

export interface RegisterRequest {
  email?: string
  username: string
  password: string
  tenant_id?: string
  turnstile_token?: string
}

export interface RegisterResponse {
  id: string
  username: string
  email?: string
  tenant_id: string
  message?: string
}

export interface User {
  id: string
  username: string
  email?: string
  tenant_id: string
  role: string
  is_active: boolean
  email_verified: boolean
}