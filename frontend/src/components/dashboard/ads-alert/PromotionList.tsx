// frontend/src/components/dashboard/ads-alert/PromotionList.tsx
import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { Promotion } from '../../../types/adsAlert'

interface PromotionListProps {
  onEdit?: (promotion: Promotion) => void
  onView?: (promotion: Promotion) => void
}

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`

const Filters = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`

const FilterButton = styled.button<{ $active: boolean }>`
  padding: 8px 16px;
  border: 1px solid ${props => props.$active ? '#4A90E2' : '#d1d5db'};
  border-radius: 20px;
  background: ${props => props.$active ? 'rgba(74, 144, 226, 0.1)' : 'white'};
  color: ${props => props.$active ? '#4A90E2' : '#6b7280'};
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #4A90E2;
    color: #4A90E2;
  }
`

const List = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`

const PromotionCard = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #4A90E2;
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.1);
  }
`

const MediaPreview = styled.div`
  width: 64px;
  height: 64px;
  border-radius: 8px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
`

const PreviewImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const PreviewIcon = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;

  svg {
    width: 24px;
    height: 24px;
  }
`

const Content = styled.div`
  flex: 1;
  min-width: 0;
`

const Title = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const Description = styled.p`
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`

const Meta = styled.div`
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #9ca3af;
`

const MetaItem = styled.span`
  display: flex;
  align-items: center;
  gap: 4px;
`

const StatusBadge = styled.span<{ $status: string }>`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;

  ${props => {
    switch (props.$status) {
      case 'draft':
        return `
          background: #f3f4f6;
          color: #6b7280;
        `
      case 'scheduled':
        return `
          background: #fef3c7;
          color: #d97706;
        `
      case 'sent':
        return `
          background: #d1fae5;
          color: #059669;
        `
      case 'cancelled':
        return `
          background: #fee2e2;
          color: #dc2626;
        `
      default:
        return `
          background: #f3f4f6;
          color: #6b7280;
        `
    }
  }}
`

const Actions = styled.div`
  display: flex;
  gap: 8px;
`

const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' }>`
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
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

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px;
  color: #9ca3af;
`

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
`

const EmptyText = styled.p`
  font-size: 14px;
  margin: 0;
`

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  padding: 48px;
  color: #9ca3af;
`

type StatusFilter = 'all' | 'draft' | 'scheduled' | 'sent'

const PromotionList: React.FC<PromotionListProps> = ({
  onEdit,
  onView
}) => {
  const [promotions, setPromotions] = useState<Promotion[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<StatusFilter>('all')

  useEffect(() => {
    loadPromotions()
  }, [filter])

  const loadPromotions = async () => {
    setLoading(true)
    try {
      const params = filter !== 'all' ? { status: filter } : undefined
      const data = await adsAlertService.listPromotions(params)
      setPromotions(data)
    } catch (error) {
      console.error('Failed to load promotions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async (promotion: Promotion, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Send this promotion now?')) return

    try {
      await adsAlertService.sendPromotion(promotion.id)
      loadPromotions()
    } catch (error) {
      console.error('Failed to send promotion:', error)
      alert('Failed to send promotion')
    }
  }

  const handleDelete = async (promotion: Promotion, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this promotion?')) return

    try {
      await adsAlertService.deletePromotion(promotion.id)
      loadPromotions()
    } catch (error) {
      console.error('Failed to delete promotion:', error)
      alert('Failed to delete promotion')
    }
  }

  const getMediaIcon = (type: string): React.ReactNode => {
    switch (type) {
      case 'image': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
      case 'video': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )
      case 'document': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      )
      case 'mixed': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
        </svg>
      )
      default: return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFirstImageUrl = (promotion: Promotion): string | null => {
    if (promotion.media_urls && promotion.media_urls.length > 0) {
      const url = promotion.media_urls[0]
      if (url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        return url
      }
    }
    return null
  }

  const filteredPromotions = promotions

  return (
    <Container>
      <Filters>
        <FilterButton $active={filter === 'all'} onClick={() => setFilter('all')}>
          All
        </FilterButton>
        <FilterButton $active={filter === 'draft'} onClick={() => setFilter('draft')}>
          Draft
        </FilterButton>
        <FilterButton $active={filter === 'scheduled'} onClick={() => setFilter('scheduled')}>
          Scheduled
        </FilterButton>
        <FilterButton $active={filter === 'sent'} onClick={() => setFilter('sent')}>
          Sent
        </FilterButton>
      </Filters>

      {loading ? (
        <LoadingState>Loading promotions...</LoadingState>
      ) : filteredPromotions.length === 0 ? (
        <EmptyState>
          <EmptyIcon>📢</EmptyIcon>
          <EmptyText>No promotions found</EmptyText>
        </EmptyState>
      ) : (
        <List>
          {filteredPromotions.map(promotion => {
            const imageUrl = getFirstImageUrl(promotion)
            return (
              <PromotionCard
                key={promotion.id}
                onClick={() => onView?.(promotion)}
              >
                <MediaPreview>
                  {imageUrl ? (
                    <PreviewImage src={imageUrl} alt="" />
                  ) : (
                    <PreviewIcon>{getMediaIcon(promotion.media_type)}</PreviewIcon>
                  )}
                </MediaPreview>

                <Content>
                  <Title>{promotion.title}</Title>
                  {promotion.content && (
                    <Description>{promotion.content}</Description>
                  )}
                  <Meta>
                    <MetaItem>
                      📅 {formatDate(promotion.created_at)}
                    </MetaItem>
                    {promotion.scheduled_at && (
                      <MetaItem>
                        ⏰ Scheduled: {formatDate(promotion.scheduled_at)}
                      </MetaItem>
                    )}
                    <MetaItem>
                      👥 {promotion.target_type === 'all' ? 'All subscribers' : `${promotion.target_chat_ids.length} chats`}
                    </MetaItem>
                    {promotion.media_urls.length > 0 && (
                      <MetaItem>
                        📎 {promotion.media_urls.length} file{promotion.media_urls.length !== 1 ? 's' : ''}
                      </MetaItem>
                    )}
                  </Meta>
                </Content>

                <StatusBadge $status={promotion.status}>
                  {promotion.status.charAt(0).toUpperCase() + promotion.status.slice(1)}
                </StatusBadge>

                <Actions onClick={e => e.stopPropagation()}>
                  {promotion.status === 'draft' && (
                    <>
                      <ActionButton onClick={(e) => { e.stopPropagation(); onEdit?.(promotion) }}>
                        Edit
                      </ActionButton>
                      <ActionButton $variant="primary" onClick={(e) => handleSend(promotion, e)}>
                        Send
                      </ActionButton>
                    </>
                  )}
                  {promotion.status === 'scheduled' && (
                    <ActionButton onClick={(e) => { e.stopPropagation(); onEdit?.(promotion) }}>
                      Edit
                    </ActionButton>
                  )}
                  {(promotion.status === 'draft' || promotion.status === 'cancelled') && (
                    <ActionButton $variant="danger" onClick={(e) => handleDelete(promotion, e)}>
                      Delete
                    </ActionButton>
                  )}
                </Actions>
              </PromotionCard>
            )
          })}
        </List>
      )}
    </Container>
  )
}

export default PromotionList
