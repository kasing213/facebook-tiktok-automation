import React from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { easings, reduceMotion } from '../../styles/animations'
import { useStaggeredAnimation } from '../../hooks/useScrollAnimation'

// Platform logos
import facebookLogo from '../../assets/images/social/facebook-logo.png'
import tiktokLogo from '../../assets/images/social/tiktok-logo.png'
import telegramLogo from '../../assets/images/social/telegram-logo.png'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

// Stats Grid
const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
`

const StatCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border-radius: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  padding: 1.25rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              box-shadow 0.2s ease,
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
    transform: ${props => props.$isVisible ? 'translateY(-2px)' : 'translateY(20px)'};
  }

  ${reduceMotion}
`

const StatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
`

const StatLabel = styled.span`
  font-size: 0.875rem;
  color: ${props => props.theme.textSecondary};
`

const StatBadge = styled.span<{ $variant?: 'success' | 'warning' | 'info' }>`
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;

  ${props => {
    switch (props.$variant) {
      case 'success':
        return `
          background: ${props.theme.successLight};
          color: ${props.theme.success};
        `
      case 'warning':
        return `
          background: ${props.theme.warningLight};
          color: ${props.theme.warning};
        `
      default:
        return `
          background: ${props.theme.accentLight};
          color: ${props.theme.accentDark};
        `
    }
  }}
`

const StatValue = styled.p`
  font-size: 1.5rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const StatSubtext = styled.p`
  font-size: 0.75rem;
  color: ${props => props.theme.textMuted};
  margin: 0.25rem 0 0 0;
`

const StatPlatforms = styled.p`
  font-size: 0.75rem;
  color: ${props => props.theme.textMuted};
  margin: 0.25rem 0 0 0;

  .fb {
    color: ${props => props.theme.accent};
  }
`

// Two Column Layout
const TwoColumnGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`

// Activity Feed
const ActivityCard = styled.div`
  background: ${props => props.theme.card};
  border-radius: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  overflow: hidden;
  transition: background-color 0.3s ease, border-color 0.3s ease;
`

const CardHeader = styled.div`
  padding: 1rem 1.25rem;
  border-bottom: 1px solid ${props => props.theme.borderLight};
  display: flex;
  align-items: center;
  justify-content: space-between;
`

const CardTitle = styled.h3`
  font-size: 1rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const ViewAllLink = styled.a`
  font-size: 0.875rem;
  color: ${props => props.theme.accent};
  text-decoration: none;
  cursor: pointer;

  &:hover {
    color: ${props => props.theme.accentDark};
  }
`

const ActivityList = styled.div``

const ActivityItem = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  padding: 0.75rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid ${props => props.theme.borderLight};
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateX(0)' : 'translateX(-15px)'};
  transition: opacity 0.4s ${easings.easeOutCubic},
              transform 0.4s ${easings.easeOutCubic},
              background 0.15s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    background: ${props => props.theme.cardHover};
  }

  &:last-child {
    border-bottom: none;
  }

  ${reduceMotion}
`

const ActivityIcon = styled.div<{ $variant: 'success' | 'warning' | 'info' }>`
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  ${props => {
    switch (props.$variant) {
      case 'success':
        return `
          background: ${props.theme.successLight};
          color: ${props.theme.success};
        `
      case 'warning':
        return `
          background: ${props.theme.warningLight};
          color: ${props.theme.warning};
        `
      default:
        return `
          background: ${props.theme.accentLight};
          color: ${props.theme.accent};
        `
    }
  }}
`

const ActivityContent = styled.div`
  flex: 1;
  min-width: 0;
`

const ActivityTitle = styled.p`
  font-size: 0.875rem;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const ActivityMeta = styled.p<{ $variant?: 'success' | 'warning' }>`
  font-size: 0.75rem;
  margin: 0;
  color: ${props => {
    switch (props.$variant) {
      case 'success': return props.theme.success
      case 'warning': return props.theme.warning
      default: return props.theme.textMuted
    }
  }};
`

const ActivityTime = styled.span`
  font-size: 0.75rem;
  color: ${props => props.theme.textMuted};
  flex-shrink: 0;
`

// Right Column
const RightColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`

// Connected Platforms
const PlatformCard = styled.div`
  background: ${props => props.theme.card};
  border-radius: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  transition: background-color 0.3s ease, border-color 0.3s ease;
`

const PlatformList = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`

const PlatformItem = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: ${props => props.theme.cardHover};
  border-radius: 0.5rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(10px)'};
  transition: opacity 0.4s ${easings.easeOutCubic},
              transform 0.4s ${easings.easeOutCubic};
  transition-delay: ${props => props.$delay || 0}ms;

  ${reduceMotion}
`

const PlatformInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

const PlatformIcon = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 6px;
  object-fit: contain;
`

const PlatformName = styled.p`
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const PlatformDetail = styled.p`
  font-size: 0.75rem;
  color: ${props => props.theme.textSecondary};
  margin: 0;
`

const StatusDot = styled.span`
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 9999px;
  background: ${props => props.theme.success};
`

const ManageButton = styled.a`
  display: block;
  text-align: center;
  font-size: 0.875rem;
  color: ${props => props.theme.accent};
  padding: 0.5rem;
  margin: 0 1rem 1rem;
  border: 1px solid ${props => props.theme.accentLightBorder};
  border-radius: 0.5rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: ${props => props.theme.accentLight};
  }
`

// Quick Actions
const QuickActionsCard = styled.div`
  background: ${props => props.theme.card};
  border-radius: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  transition: background-color 0.3s ease, border-color 0.3s ease;
`

const QuickActionsList = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`

const QuickActionItem = styled.a`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: ${props => props.theme.textSecondary};
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s ease,
              color 0.2s ease,
              transform 0.2s ${easings.easeOutCubic};

  &:hover {
    background: ${props => props.theme.cardHover};
    color: ${props => props.theme.textPrimary};
    transform: translateX(4px);
  }

  &:active {
    transform: translateX(2px);
  }

  ${reduceMotion}
`

const QuickActionIcon = styled.div<{ $color: 'blue' | 'green' | 'amber' }>`
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;

  ${props => {
    switch (props.$color) {
      case 'green':
        return `
          background: ${props.theme.successLight};
          color: ${props.theme.success};
        `
      case 'amber':
        return `
          background: ${props.theme.warningLight};
          color: ${props.theme.warning};
        `
      default:
        return `
          background: ${props.theme.accentLight};
          color: ${props.theme.accent};
        `
    }
  }}
`

// Mock data
const stats = {
  revenue: { value: 2450000, currency: 'KHR', change: 18.2 },
  invoicesPending: { count: 12, amount: 890000 },
  postsScheduled: { count: 24, platforms: { facebook: 15, tiktok: 9 } },
  verifiedToday: { count: 8, autoApproved: 6 }
}

const recentActivity = [
  { type: 'invoice_paid', title: 'Invoice #INV-0042 paid', amount: 125000, time: '5 min ago', status: 'success' as const },
  { type: 'post_published', title: 'Posted to Facebook', platform: 'facebook', time: '12 min ago', status: 'success' as const },
  { type: 'verification', title: 'Payment verified via OCR', confidence: 94, time: '18 min ago', status: 'success' as const },
  { type: 'post_scheduled', title: 'TikTok video scheduled', platform: 'tiktok', time: '1 hour ago', status: 'info' as const },
  { type: 'low_stock', title: 'Low stock: iPhone 15 Pro', stock: 3, time: '2 hours ago', status: 'warning' as const },
  { type: 'invoice_sent', title: 'Invoice #INV-0043 sent via Telegram', time: '3 hours ago', status: 'success' as const },
]

const connectedPlatforms = [
  { name: 'Facebook', connected: true, detail: '2 pages', icon: facebookLogo },
  { name: 'TikTok', connected: true, detail: '1 account', icon: tiktokLogo },
  { name: 'Telegram Bot', connected: true, detail: '45 linked users', icon: telegramLogo },
]

const formatKHR = (amount: number) => {
  return new Intl.NumberFormat('en-US').format(amount) + ' ៛'
}

const formatUSD = (amount: number) => {
  return '$' + new Intl.NumberFormat('en-US', { minimumFractionDigits: 2 }).format(amount)
}

const OverviewPage: React.FC = () => {
  const navigate = useNavigate()

  // Animation hooks
  const statsVisible = useStaggeredAnimation(4, 100) // 4 stat cards, 100ms stagger
  const activityVisible = useStaggeredAnimation(recentActivity.length, 60)
  const platformsVisible = useStaggeredAnimation(connectedPlatforms.length, 80)

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'invoice_paid':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case 'post_published':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684" />
          </svg>
        )
      case 'verification':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'post_scheduled':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'low_stock':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'invoice_sent':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        )
      default:
        return null
    }
  }

  const getActivityVariant = (status: string): 'success' | 'warning' | 'info' => {
    switch (status) {
      case 'success': return 'success'
      case 'warning': return 'warning'
      default: return 'info'
    }
  }

  return (
    <Container>
      {/* Stats Grid */}
      <StatsGrid>
        {/* Revenue */}
        <StatCard $isVisible={statsVisible[0]} $delay={0}>
          <StatHeader>
            <StatLabel>Revenue (This Month)</StatLabel>
            <StatBadge $variant="success">+{stats.revenue.change}%</StatBadge>
          </StatHeader>
          <StatValue>{formatKHR(stats.revenue.value)}</StatValue>
          <StatSubtext>≈ {formatUSD(stats.revenue.value / 4000)}</StatSubtext>
        </StatCard>

        {/* Pending Invoices */}
        <StatCard $isVisible={statsVisible[1]} $delay={100}>
          <StatHeader>
            <StatLabel>Pending Invoices</StatLabel>
            <StatBadge $variant="warning">{stats.invoicesPending.count} unpaid</StatBadge>
          </StatHeader>
          <StatValue>{formatKHR(stats.invoicesPending.amount)}</StatValue>
          <StatSubtext>Awaiting payment</StatSubtext>
        </StatCard>

        {/* Scheduled Posts */}
        <StatCard $isVisible={statsVisible[2]} $delay={200}>
          <StatHeader>
            <StatLabel>Scheduled Posts</StatLabel>
            <StatBadge>Next 7 days</StatBadge>
          </StatHeader>
          <StatValue>{stats.postsScheduled.count}</StatValue>
          <StatPlatforms>
            <span className="fb">FB: {stats.postsScheduled.platforms.facebook}</span>
            <span> • TT: {stats.postsScheduled.platforms.tiktok}</span>
          </StatPlatforms>
        </StatCard>

        {/* Verified Today */}
        <StatCard $isVisible={statsVisible[3]} $delay={300}>
          <StatHeader>
            <StatLabel>Verified Today</StatLabel>
            <StatBadge>OCR</StatBadge>
          </StatHeader>
          <StatValue>{stats.verifiedToday.count}</StatValue>
          <StatSubtext>{stats.verifiedToday.autoApproved} auto-approved</StatSubtext>
        </StatCard>
      </StatsGrid>

      {/* Two Column Layout */}
      <TwoColumnGrid>
        {/* Activity Feed */}
        <ActivityCard>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <ViewAllLink onClick={() => navigate('/dashboard/logs')}>View all</ViewAllLink>
          </CardHeader>
          <ActivityList>
            {recentActivity.map((activity, i) => (
              <ActivityItem key={i} $isVisible={activityVisible[i]} $delay={i * 60}>
                <ActivityIcon $variant={getActivityVariant(activity.status)}>
                  {getActivityIcon(activity.type)}
                </ActivityIcon>
                <ActivityContent>
                  <ActivityTitle>{activity.title}</ActivityTitle>
                  {activity.amount && (
                    <ActivityMeta $variant="success">{formatKHR(activity.amount)}</ActivityMeta>
                  )}
                  {activity.confidence && (
                    <ActivityMeta $variant="success">{activity.confidence}% confidence</ActivityMeta>
                  )}
                  {activity.stock !== undefined && (
                    <ActivityMeta $variant="warning">Only {activity.stock} left</ActivityMeta>
                  )}
                </ActivityContent>
                <ActivityTime>{activity.time}</ActivityTime>
              </ActivityItem>
            ))}
          </ActivityList>
        </ActivityCard>

        {/* Right Column */}
        <RightColumn>
          {/* Connected Platforms */}
          <PlatformCard>
            <CardHeader>
              <CardTitle>Connected Platforms</CardTitle>
            </CardHeader>
            <PlatformList>
              {connectedPlatforms.map((platform, i) => (
                <PlatformItem key={i} $isVisible={platformsVisible[i]} $delay={i * 80 + 200}>
                  <PlatformInfo>
                    <PlatformIcon src={platform.icon} alt={platform.name} />
                    <div>
                      <PlatformName>{platform.name}</PlatformName>
                      <PlatformDetail>{platform.detail}</PlatformDetail>
                    </div>
                  </PlatformInfo>
                  <StatusDot />
                </PlatformItem>
              ))}
            </PlatformList>
            <ManageButton onClick={() => navigate('/dashboard/integrations')}>
              Manage Integrations
            </ManageButton>
          </PlatformCard>

          {/* Quick Actions */}
          <QuickActionsCard>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <QuickActionsList>
              <QuickActionItem onClick={() => navigate('/dashboard/invoices/new')}>
                <QuickActionIcon $color="blue">
                  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </QuickActionIcon>
                Create Invoice
              </QuickActionItem>
              <QuickActionItem onClick={() => navigate('/dashboard/integrations/facebook')}>
                <QuickActionIcon $color="green">
                  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </QuickActionIcon>
                Schedule Post
              </QuickActionItem>
              <QuickActionItem onClick={() => navigate('/dashboard/inventory')}>
                <QuickActionIcon $color="amber">
                  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </QuickActionIcon>
                Add Product
              </QuickActionItem>
            </QuickActionsList>
          </QuickActionsCard>
        </RightColumn>
      </TwoColumnGrid>
    </Container>
  )
}

export default OverviewPage
