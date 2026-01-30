// frontend/src/components/dashboard/ads-alert/PromotionList.tsx
import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { Promotion } from '../../../types/adsAlert'
import { easings, reduceMotion } from '../../../styles/animations'
import { useStaggeredAnimation } from '../../../hooks/useScrollAnimation'

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

const PromotionCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: ${props => props.theme.card || 'white'};
  border: 1px solid ${props => props.theme.border || '#e5e7eb'};
  border-radius: 12px;
  cursor: pointer;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(15px)'};
  transition: opacity 0.4s ${easings.easeOutCubic},
              transform 0.4s ${easings.easeOutCubic},
              border-color 0.2s ease,
              box-shadow 0.2s ease,
              background-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    border-color: ${props => props.theme.accent || '#4A90E2'};
    box-shadow: 0 2px 8px ${props => props.theme.shadowColor || 'rgba(74, 144, 226, 0.1)'};
  }

  ${reduceMotion}
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

  svg {
    width: 14px;
    height: 14px;
  }
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

const ModerationBadge = styled.span<{ $status: string }>`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;

  ${props => {
    switch (props.$status) {
      case 'approved':
        return `
          background: #d1fae5;
          color: #059669;
        `
      case 'pending':
        return `
          background: #fef3c7;
          color: #d97706;
        `
      case 'rejected':
        return `
          background: #fee2e2;
          color: #dc2626;
        `
      case 'flagged':
        return `
          background: #fde68a;
          color: #f59e0b;
        `
      case 'skipped':
        return `
          background: #e5e7eb;
          color: #6b7280;
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
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
  color: #9ca3af;

  svg {
    width: 48px;
    height: 48px;
  }
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
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [imageBlobs, setImageBlobs] = useState<Record<string, string>>({})

  // Animation for promotion cards (max 10 for performance)
  const cardsVisible = useStaggeredAnimation(Math.min(promotions.length, 10), 80)

  useEffect(() => {
    loadPromotions()
  }, [filter])

  // Fetch blob URLs for images when promotions change
  useEffect(() => {
    const loadImageBlobs = async () => {
      const blobMap: Record<string, string> = {}
      for (const promotion of promotions) {
        const imageUrl = getFirstImageUrl(promotion)
        if (imageUrl && imageUrl.includes('/ads-alert/media/file/')) {
          try {
            const blobUrl = await adsAlertService.getMediaBlobUrl(imageUrl)
            if (blobUrl) {
              blobMap[promotion.id] = blobUrl
            }
          } catch (error) {
            console.error(`Failed to load image for promotion ${promotion.id}:`, error)
          }
        }
      }
      setImageBlobs(blobMap)
    }

    if (promotions.length > 0) {
      loadImageBlobs()
    }

    // Cleanup blob URLs on unmount or when promotions change
    return () => {
      Object.values(imageBlobs).forEach(url => {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })
    }
  }, [promotions])

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

    // Check if promotion can be sent based on moderation status
    if (promotion.moderation_status === 'rejected') {
      const reason = promotion.rejection_reason || 'Content violates platform policies'
      alert(`❌ Cannot send promotion: ${reason}\n\nPlease edit the content to remove policy violations.`)
      return
    }

    if (promotion.moderation_status === 'pending') {
      alert('⏳ Cannot send promotion: Content is still being reviewed for policy compliance. Please wait for approval.')
      return
    }

    if (promotion.moderation_status === 'flagged') {
      alert('⚠️ Cannot send promotion: Content requires manual admin approval before sending.')
      return
    }

    if (!confirm('Send this promotion now?')) return

    try {
      await adsAlertService.sendPromotion(promotion.id)
      loadPromotions()
      alert('✅ Promotion sent successfully!')
    } catch (error: any) {
      console.error('Failed to send promotion:', error)

      // Handle specific error responses from the backend
      if (error.response?.data?.detail) {
        const errorDetail = error.response.data.detail

        if (typeof errorDetail === 'object') {
          // Handle structured error responses (content violations)
          if (errorDetail.error === 'content_rejected') {
            alert(`❌ Content Violation: ${errorDetail.message}\n\nViolations found: ${errorDetail.violations?.join(', ')}\n\nRecommendation: ${errorDetail.recommendation}`)
          } else if (errorDetail.error === 'content_pending_moderation') {
            alert(`⏳ ${errorDetail.message}`)
          } else if (errorDetail.error === 'content_flagged_for_review') {
            alert(`⚠️ ${errorDetail.message}`)
          } else {
            alert(`❌ Error: ${errorDetail.message || 'Failed to send promotion'}`)
          }
        } else {
          // Handle simple string error messages
          alert(`❌ Failed to send promotion: ${errorDetail}`)
        }
      } else {
        alert('❌ Failed to send promotion. Please try again.')
      }
    }
  }

  const handleDelete = async (promotion: Promotion, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this promotion?')) return

    setDeletingId(promotion.id)
    try {
      await adsAlertService.deletePromotion(promotion.id)
      loadPromotions()
    } catch (error: any) {
      console.error('Failed to delete promotion:', error)

      // Handle specific error responses
      if (error.response?.status === 403) {
        alert('Permission denied: You do not have permission to delete this promotion.')
      } else if (error.response?.status === 404) {
        alert('Promotion not found. It may have already been deleted.')
        loadPromotions()  // Refresh list
      } else if (error.response?.data?.detail) {
        alert(`Failed to delete promotion: ${error.response.data.detail}`)
      } else {
        alert('Failed to delete promotion. Please try again.')
      }
    } finally {
      setDeletingId(null)
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
    if (!promotion.media_urls || promotion.media_urls.length === 0) {
      return null
    }

    const url = promotion.media_urls[0]

    // Check 1: URL has image extension (external URLs)
    if (url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
      return url
    }

    // Check 2: API endpoint URL (GridFS - no extension)
    // These URLs are like /api/ads-alert/media/file/{file_id}
    if (url.includes('/ads-alert/media/file/')) {
      // Only return if media_type indicates image content
      if (promotion.media_type === 'image' || promotion.media_type === 'mixed') {
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
          <EmptyIcon>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
          </EmptyIcon>
          <EmptyText>No promotions found</EmptyText>
        </EmptyState>
      ) : (
        <List>
          {filteredPromotions.map((promotion, index) => {
            const imageUrl = getFirstImageUrl(promotion)
            return (
              <PromotionCard
                key={promotion.id}
                onClick={() => onView?.(promotion)}
                $isVisible={cardsVisible[index] ?? true}
                $delay={index * 80}
              >
                <MediaPreview>
                  {imageUrl ? (
                    <PreviewImage
                      src={imageBlobs[promotion.id] || imageUrl}
                      alt=""
                      onError={(e) => {
                        // Hide broken images
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
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
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {formatDate(promotion.created_at)}
                    </MetaItem>
                    {promotion.scheduled_at && (
                      <MetaItem>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Scheduled: {formatDate(promotion.scheduled_at)}
                      </MetaItem>
                    )}
                    <MetaItem>
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      {promotion.target_type === 'all' ? 'All subscribers' : `${promotion.target_chat_ids.length} chats`}
                    </MetaItem>
                    {promotion.media_urls.length > 0 && (
                      <MetaItem>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                        </svg>
                        {promotion.media_urls.length} file{promotion.media_urls.length !== 1 ? 's' : ''}
                      </MetaItem>
                    )}
                  </Meta>
                </Content>

                <StatusBadge $status={promotion.status}>
                  {promotion.status.charAt(0).toUpperCase() + promotion.status.slice(1)}
                </StatusBadge>

                {promotion.moderation_status && (
                  <ModerationBadge $status={promotion.moderation_status}>
                    {promotion.moderation_status}
                  </ModerationBadge>
                )}

                <Actions onClick={e => e.stopPropagation()}>
                  {promotion.status === 'draft' && (
                    <>
                      <ActionButton onClick={(e) => { e.stopPropagation(); onEdit?.(promotion) }}>
                        Edit
                      </ActionButton>
                      <ActionButton
                        $variant="primary"
                        onClick={(e) => handleSend(promotion, e)}
                        disabled={promotion.moderation_status === 'rejected' || promotion.moderation_status === 'pending' || promotion.moderation_status === 'flagged'}
                        style={{
                          opacity: (promotion.moderation_status === 'rejected' || promotion.moderation_status === 'pending' || promotion.moderation_status === 'flagged') ? 0.5 : 1,
                          cursor: (promotion.moderation_status === 'rejected' || promotion.moderation_status === 'pending' || promotion.moderation_status === 'flagged') ? 'not-allowed' : 'pointer'
                        }}
                      >
                        Send
                      </ActionButton>
                    </>
                  )}
                  {promotion.status === 'scheduled' && (
                    <ActionButton onClick={(e) => { e.stopPropagation(); onEdit?.(promotion) }}>
                      Edit
                    </ActionButton>
                  )}
                  {(promotion.status === 'draft' || promotion.status === 'cancelled' || promotion.status === 'sent') && (
                    <ActionButton
                      $variant="danger"
                      onClick={(e) => handleDelete(promotion, e)}
                      disabled={deletingId === promotion.id}
                      style={{
                        opacity: deletingId === promotion.id ? 0.6 : 1,
                        cursor: deletingId === promotion.id ? 'not-allowed' : 'pointer'
                      }}
                    >
                      {deletingId === promotion.id ? 'Deleting...' : 'Delete'}
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
