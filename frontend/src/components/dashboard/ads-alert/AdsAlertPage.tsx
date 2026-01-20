// frontend/src/components/dashboard/ads-alert/AdsAlertPage.tsx
import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { Promotion, AdsAlertStats } from '../../../types/adsAlert'
import PromotionList from './PromotionList'
import PromotionForm from './PromotionForm'
import ChatList from './ChatList'

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
  color: #1f2937;
  margin: 0 0 4px 0;
`

const Subtitle = styled.p`
  font-size: 14px;
  color: #6b7280;
  margin: 0;
`

const CreateButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #4A90E2;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #357ABD;
  }
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`

const StatCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
`

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
`

const StatLabel = styled.div`
  font-size: 13px;
  color: #6b7280;
`

const StatIcon = styled.span`
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
  color: #6b7280;

  svg {
    width: 20px;
    height: 20px;
  }
`

const Tabs = styled.div`
  display: flex;
  gap: 4px;
  background: #f3f4f6;
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
  background: ${props => props.$active ? 'white' : 'transparent'};
  color: ${props => props.$active ? '#1f2937' : '#6b7280'};
  box-shadow: ${props => props.$active ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none'};

  &:hover {
    color: #1f2937;
  }
`

const TabContent = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
`

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 16px;

  &:hover {
    color: #4A90E2;
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
  color: #1f2937;
  margin: 0 0 8px 0;
`

const DetailMeta = styled.div`
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
`

const StatusBadge = styled.span<{ $status: string }>`
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;

  ${props => {
    switch (props.$status) {
      case 'draft':
        return `background: #f3f4f6; color: #6b7280;`
      case 'scheduled':
        return `background: #fef3c7; color: #d97706;`
      case 'sent':
        return `background: #d1fae5; color: #059669;`
      default:
        return `background: #f3f4f6; color: #6b7280;`
    }
  }}
`

const DetailSection = styled.div`
  margin-bottom: 24px;
`

const SectionLabel = styled.h3`
  font-size: 12px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  margin: 0 0 8px 0;
`

const ContentBox = styled.div`
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
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
  background: #f3f4f6;
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
  border-top: 1px solid #e5e7eb;
`

const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' }>`
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  ${props => props.$variant === 'primary' ? `
    background: #4A90E2;
    color: white;
    border: none;

    &:hover {
      background: #357ABD;
    }
  ` : props.$variant === 'danger' ? `
    background: white;
    color: #dc2626;
    border: 1px solid #fecaca;

    &:hover {
      background: #fef2f2;
    }
  ` : `
    background: white;
    color: #6b7280;
    border: 1px solid #d1d5db;

    &:hover {
      background: #f3f4f6;
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
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontSize: '24px' }}>
                      {url.includes('.mp4') ? '🎬' : '📄'}
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
          <Title>📢 Ads Alert</Title>
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
          <StatCard>
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
          <StatCard>
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
          <StatCard>
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
          <StatCard>
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
          <StatCard>
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
          📢 Promotions
        </Tab>
        <Tab
          $active={activeTab === 'chats'}
          onClick={() => { setActiveTab('chats'); setViewMode('list') }}
        >
          💬 Chats
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
