// frontend/src/components/dashboard/ads-alert/AdsAlertPage.tsx
import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { Promotion, AdsAlertStats } from '../../../types/adsAlert'
import PromotionList from './PromotionList'
import PromotionForm from './PromotionForm'
import ChatList from './ChatList'
import { easings, reduceMotion } from '../../../styles/animations'
import { useStaggeredAnimation } from '../../../hooks/useScrollAnimation'

const Container = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`

const TitleSection = styled.div``

const Title = styled.h1`
  font-size: 24px;
  font-weight: 700;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;

  svg {
    width: 24px;
    height: 24px;
  }
`

const Subtitle = styled.p`
  font-size: 14px;
  color: ${props => props.theme.textSecondary};
  margin: 0;
`

const CreateButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: ${props => props.theme.accent};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: ${props => props.theme.accentDark};
  }
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`

const StatCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 20px;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
  }

  ${reduceMotion}
`

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: ${props => props.theme.textPrimary};
  margin-bottom: 4px;
`

const StatLabel = styled.div`
  font-size: 13px;
  color: ${props => props.theme.textSecondary};
`

const StatIcon = styled.span`
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
  color: ${props => props.theme.textSecondary};

  svg {
    width: 20px;
    height: 20px;
  }
`

const Tabs = styled.div`
  display: flex;
  gap: 4px;
  background: ${props => props.theme.backgroundTertiary};
  padding: 4px;
  border-radius: 10px;
  margin-bottom: 24px;
`

const Tab = styled.button<{ $active: boolean }>`
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: ${props => props.$active ? props.theme.card : 'transparent'};
  color: ${props => props.$active ? props.theme.textPrimary : props.theme.textSecondary};
  box-shadow: ${props => props.$active ? `0 1px 3px ${props.theme.shadowColor}` : 'none'};
  display: flex;
  align-items: center;
  gap: 6px;

  svg {
    width: 16px;
    height: 16px;
  }

  &:hover {
    color: ${props => props.theme.textPrimary};
  }
`

const TabContent = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 24px;
  transition: background-color 0.3s ease, border-color 0.3s ease;
`

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: ${props => props.theme.textSecondary};
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 16px;

  &:hover {
    color: ${props => props.theme.accent};
  }
`

const PromotionDetail = styled.div`
  max-width: 600px;
`

const DetailHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
`

const DetailTitle = styled.h2`
  font-size: 20px;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 8px 0;
`

const DetailMeta = styled.div`
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: ${props => props.theme.textSecondary};
`

const StatusBadge = styled.span<{ $status: string }>`
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;

  ${props => {
    switch (props.$status) {
      case 'draft':
        return `background: ${props.theme.backgroundTertiary}; color: ${props.theme.textSecondary};`
      case 'scheduled':
        return `background: ${props.theme.warningLight}; color: ${props.theme.warning};`
      case 'sent':
        return `background: ${props.theme.successLight}; color: ${props.theme.success};`
      default:
        return `background: ${props.theme.backgroundTertiary}; color: ${props.theme.textSecondary};`
    }
  }}
`

const DetailSection = styled.div`
  margin-bottom: 24px;
`

const SectionLabel = styled.h3`
  font-size: 12px;
  font-weight: 600;
  color: ${props => props.theme.textMuted};
  text-transform: uppercase;
  margin: 0 0 8px 0;
`

const ContentBox = styled.div`
  padding: 16px;
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 8px;
  font-size: 14px;
  color: ${props => props.theme.textPrimary};
  white-space: pre-wrap;
`

const MediaGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
`

const MediaItem = styled.div`
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: ${props => props.theme.backgroundTertiary};
`

const MediaImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const DetailActions = styled.div`
  display: flex;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid ${props => props.theme.border};
`

const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' }>`
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  ${props => props.$variant === 'primary' ? `
    background: ${props.theme.accent};
    color: white;
    border: none;

    &:hover {
      background: ${props.theme.accentDark};
    }
  ` : props.$variant === 'danger' ? `
    background: ${props.theme.card};
    color: ${props.theme.error};
    border: 1px solid ${props.theme.errorLight};

    &:hover {
      background: ${props.theme.errorLight};
    }
  ` : `
    background: ${props.theme.card};
    color: ${props.theme.textSecondary};
    border: 1px solid ${props.theme.border};

    &:hover {
      background: ${props.theme.backgroundTertiary};
    }
  `}
`

type TabType = 'promotions' | 'chats' | 'media'
type ViewMode = 'list' | 'create' | 'edit' | 'view'

const AdsAlertPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('promotions')
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedPromotion, setSelectedPromotion] = useState<Promotion | null>(null)
  const [stats, setStats] = useState<AdsAlertStats | null>(null)
  const [loading, setLoading] = useState(true)

  // Animation state for stat cards (5 stat cards)
  const statsVisible = useStaggeredAnimation(5, 100)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await adsAlertService.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setSelectedPromotion(null)
    setViewMode('create')
  }

  const handleEdit = (promotion: Promotion) => {
    setSelectedPromotion(promotion)
    setViewMode('edit')
  }

  const handleView = (promotion: Promotion) => {
    setSelectedPromotion(promotion)
    setViewMode('view')
  }

  const handleSave = () => {
    setViewMode('list')
    setSelectedPromotion(null)
    loadStats()
  }

  const handleCancel = () => {
    setViewMode('list')
    setSelectedPromotion(null)
  }

  const handleSendPromotion = async () => {
    if (!selectedPromotion) return
    if (!confirm('Send this promotion now?')) return

    try {
      await adsAlertService.sendPromotion(selectedPromotion.id)
      setViewMode('list')
      loadStats()
    } catch (error) {
      console.error('Failed to send promotion:', error)
      alert('Failed to send promotion')
    }
  }

  const handleDeletePromotion = async () => {
    if (!selectedPromotion) return
    if (!confirm('Delete this promotion?')) return

    try {
      await adsAlertService.deletePromotion(selectedPromotion.id)
      setViewMode('list')
      loadStats()
    } catch (error) {
      console.error('Failed to delete promotion:', error)
      alert('Failed to delete promotion')
    }
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const renderPromotionView = () => {
    if (!selectedPromotion) return null

    return (
      <PromotionDetail>
        <BackButton onClick={handleCancel}>
          ← Back to Promotions
        </BackButton>

        <DetailHeader>
          <div>
            <DetailTitle>{selectedPromotion.title}</DetailTitle>
            <DetailMeta>
              <span>Created {formatDate(selectedPromotion.created_at)}</span>
              {selectedPromotion.sent_at && (
                <span>Sent {formatDate(selectedPromotion.sent_at)}</span>
              )}
            </DetailMeta>
          </div>
          <StatusBadge $status={selectedPromotion.status}>
            {selectedPromotion.status.charAt(0).toUpperCase() + selectedPromotion.status.slice(1)}
          </StatusBadge>
        </DetailHeader>

        {selectedPromotion.content && (
          <DetailSection>
            <SectionLabel>Content</SectionLabel>
            <ContentBox>{selectedPromotion.content}</ContentBox>
          </DetailSection>
        )}

        {selectedPromotion.media_urls && selectedPromotion.media_urls.length > 0 && (
          <DetailSection>
            <SectionLabel>Media ({selectedPromotion.media_urls.length})</SectionLabel>
            <MediaGrid>
              {selectedPromotion.media_urls.map((url, index) => (
                <MediaItem key={index}>
                  {url.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? (
                    <MediaImage src={url} alt="" />
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
                      {url.includes('.mp4') ? (
                        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      ) : (
                        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      )}
                    </div>
                  )}
                </MediaItem>
              ))}
            </MediaGrid>
          </DetailSection>
        )}

        <DetailSection>
          <SectionLabel>Target</SectionLabel>
          <ContentBox>
            {selectedPromotion.target_type === 'all'
              ? 'All subscribers'
              : `${selectedPromotion.target_chat_ids.length} selected chats`
            }
          </ContentBox>
        </DetailSection>

        {selectedPromotion.scheduled_at && (
          <DetailSection>
            <SectionLabel>Scheduled</SectionLabel>
            <ContentBox>{formatDate(selectedPromotion.scheduled_at)}</ContentBox>
          </DetailSection>
        )}

        <DetailActions>
          {selectedPromotion.status === 'draft' && (
            <>
              <ActionButton onClick={() => handleEdit(selectedPromotion)}>
                Edit
              </ActionButton>
              <ActionButton $variant="primary" onClick={handleSendPromotion}>
                Send Now
              </ActionButton>
              <ActionButton $variant="danger" onClick={handleDeletePromotion}>
                Delete
              </ActionButton>
            </>
          )}
          {selectedPromotion.status === 'scheduled' && (
            <ActionButton onClick={() => handleEdit(selectedPromotion)}>
              Edit Schedule
            </ActionButton>
          )}
        </DetailActions>
      </PromotionDetail>
    )
  }

  return (
    <Container>
      <Header>
        <TitleSection>
          <Title>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
            Ads Alert
          </Title>
          <Subtitle>Create and manage promotional broadcasts to your customers</Subtitle>
        </TitleSection>
        {activeTab === 'promotions' && viewMode === 'list' && (
          <CreateButton onClick={handleCreate}>
            + New Promotion
          </CreateButton>
        )}
      </Header>

      {!loading && stats && (
        <StatsGrid>
          <StatCard $isVisible={statsVisible[0]} $delay={0}>
            <StatValue>
              <StatIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </StatIcon>
              {stats.subscribed_chats}
            </StatValue>
            <StatLabel>Active Subscribers</StatLabel>
          </StatCard>
          <StatCard $isVisible={statsVisible[1]} $delay={100}>
            <StatValue>
              <StatIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </StatIcon>
              {stats.draft_promotions}
            </StatValue>
            <StatLabel>Draft Promotions</StatLabel>
          </StatCard>
          <StatCard $isVisible={statsVisible[2]} $delay={200}>
            <StatValue>
              <StatIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </StatIcon>
              {stats.scheduled_promotions}
            </StatValue>
            <StatLabel>Scheduled</StatLabel>
          </StatCard>
          <StatCard $isVisible={statsVisible[3]} $delay={300}>
            <StatValue>
              <StatIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </StatIcon>
              {stats.sent_promotions}
            </StatValue>
            <StatLabel>Sent</StatLabel>
          </StatCard>
          <StatCard $isVisible={statsVisible[4]} $delay={400}>
            <StatValue>
              <StatIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </StatIcon>
              {stats.total_media}
            </StatValue>
            <StatLabel>Media Files</StatLabel>
          </StatCard>
        </StatsGrid>
      )}

      <Tabs>
        <Tab
          $active={activeTab === 'promotions'}
          onClick={() => { setActiveTab('promotions'); setViewMode('list') }}
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
          </svg>
          Promotions
        </Tab>
        <Tab
          $active={activeTab === 'chats'}
          onClick={() => { setActiveTab('chats'); setViewMode('list') }}
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Chats
        </Tab>
      </Tabs>

      <TabContent>
        {activeTab === 'promotions' && (
          <>
            {viewMode === 'list' && (
              <PromotionList
                onEdit={handleEdit}
                onView={handleView}
              />
            )}
            {(viewMode === 'create' || viewMode === 'edit') && (
              <>
                <BackButton onClick={handleCancel}>
                  ← Back to Promotions
                </BackButton>
                <PromotionForm
                  promotion={viewMode === 'edit' ? selectedPromotion || undefined : undefined}
                  onSave={handleSave}
                  onCancel={handleCancel}
                />
              </>
            )}
            {viewMode === 'view' && renderPromotionView()}
          </>
        )}
        {activeTab === 'chats' && (
          <ChatList />
        )}
      </TabContent>
    </Container>
  )
}

export default AdsAlertPage
