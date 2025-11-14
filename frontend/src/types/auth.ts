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

// OAuthResult interface removed - OAuth now redirects directly to dashboard

export interface Tenant {
  id: string
  name: string
  slug: string
  is_active: boolean
  created_at: string
}