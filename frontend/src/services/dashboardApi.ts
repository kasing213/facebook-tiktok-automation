import api from './api'

export interface ActivityItem {
  type: string  // 'invoice_paid', 'invoice_sent', 'verification', 'post_scheduled', 'low_stock'
  title: string
  time: string  // Relative time like "5 min ago"
  status: 'success' | 'warning' | 'info'
  amount?: number
  currency?: string
  confidence?: number
  platform?: string
}

export interface DashboardStats {
  // Revenue section
  revenue_this_month: number
  revenue_currency: string
  revenue_change_percent: number | null

  // Pending invoices
  pending_count: number
  pending_amount: number

  // Scheduled posts
  scheduled_posts: number

  // Verified today
  verified_today: number
  auto_approved_today: number

  // Connected platforms
  facebook_pages: number
  tiktok_accounts: number
  telegram_linked_users: number

  // Recent activity
  recent_activity: ActivityItem[]
}

// Default empty stats for loading/error states
export const emptyDashboardStats: DashboardStats = {
  revenue_this_month: 0,
  revenue_currency: 'KHR',
  revenue_change_percent: null,
  pending_count: 0,
  pending_amount: 0,
  scheduled_posts: 0,
  verified_today: 0,
  auto_approved_today: 0,
  facebook_pages: 0,
  tiktok_accounts: 0,
  telegram_linked_users: 0,
  recent_activity: []
}

export const dashboardApi = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get('/dashboard/stats')
    return response.data
  }
}

export default dashboardApi
