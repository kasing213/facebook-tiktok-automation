import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FaExclamationTriangle, FaCheck, FaTimes, FaEye, FaClock, FaFlag } from 'react-icons/fa';
import { format } from 'date-fns';

interface ViolationDetail {
  pattern: string;
  category: string;
  severity: number;
  description: string;
  matches: string[];
  match_count: number;
  source: string;
}

interface ModerationQueueItem {
  promotion_id: string;
  title: string;
  content: string;
  media_type: string;
  media_urls: string[];
  moderation_status: string;
  moderation_score: number | null;
  violations: ViolationDetail[];
  created_at: string;
  created_by: string | null;
  creator_name: string | null;
  tenant_id: string;
}

interface ModerationQueueResponse {
  items: ModerationQueueItem[];
  total: number;
  pending_count: number;
  flagged_count: number;
}

const Container = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

const Title = styled.h1`
  margin: 0;
  color: ${props => props.theme.textPrimary};
  font-size: 28px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
`;

const StatCard = styled.div<{ $severity?: 'info' | 'warning' | 'danger' }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;

  ${props => {
    switch (props.$severity) {
      case 'warning':
        return `border-left: 4px solid #f59e0b;`;
      case 'danger':
        return `border-left: 4px solid #ef4444;`;
      default:
        return `border-left: 4px solid ${props.theme.accent};`;
    }
  }}
`;

const StatIcon = styled.div<{ $severity?: 'info' | 'warning' | 'danger' }>`
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;

  ${props => {
    switch (props.$severity) {
      case 'warning':
        return `background: #f59e0b;`;
      case 'danger':
        return `background: #ef4444;`;
      default:
        return `background: ${props.theme.accent};`;
    }
  }}
`;

const StatDetails = styled.div`
  flex: 1;
`;

const StatLabel = styled.div`
  color: ${props => props.theme.textSecondary};
  font-size: 14px;
  margin-bottom: 4px;
`;

const StatValue = styled.div`
  color: ${props => props.theme.textPrimary};
  font-size: 24px;
  font-weight: 600;
`;

const FiltersContainer = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
`;

const FilterButton = styled.button<{ $active?: boolean }>`
  padding: 8px 16px;
  border: 1px solid ${props => props.$active ? props.theme.accent : props.theme.border};
  background: ${props => props.$active ? props.theme.accent : props.theme.backgroundSecondary};
  color: ${props => props.$active ? 'white' : props.theme.textPrimary};
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.$active ? props.theme.accentDark : props.theme.border};
  }
`;

const QueueContainer = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  overflow: hidden;
`;

const QueueHeader = styled.div`
  background: ${props => props.theme.backgroundTertiary};
  border-bottom: 1px solid ${props => props.theme.border};
  padding: 16px 20px;
  display: grid;
  grid-template-columns: 1fr 120px 100px 150px 120px;
  gap: 16px;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  font-size: 14px;
`;

const QueueItem = styled.div`
  border-bottom: 1px solid ${props => props.theme.border};
  padding: 16px 20px;
  display: grid;
  grid-template-columns: 1fr 120px 100px 150px 120px;
  gap: 16px;
  align-items: center;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: ${props => props.theme.backgroundTertiary};
  }
`;

const PromotionInfo = styled.div``;

const PromotionTitle = styled.div`
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin-bottom: 4px;
  font-size: 16px;
`;

const PromotionContent = styled.div`
  color: ${props => props.theme.textSecondary};
  font-size: 14px;
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const PromotionMeta = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
  color: ${props => props.theme.textSecondary};
`;

const StatusBadge = styled.span<{ $status: string }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;

  ${props => {
    switch (props.$status) {
      case 'pending':
        return `background: #f59e0b20; color: #f59e0b; border: 1px solid #f59e0b40;`;
      case 'flagged':
        return `background: #ef444420; color: #ef4444; border: 1px solid #ef444440;`;
      case 'approved':
        return `background: #10b98120; color: #10b981; border: 1px solid #10b98140;`;
      case 'rejected':
        return `background: #ef444420; color: #ef4444; border: 1px solid #ef444440;`;
      default:
        return `background: ${props.theme.backgroundTertiary}; color: ${props.theme.textSecondary}; border: 1px solid ${props.theme.border};`;
    }
  }}
`;

const ScoreBadge = styled.div<{ $score: number }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 40px;

  ${props => {
    if (props.$score >= 80) return `background: #ef444420; color: #ef4444;`;
    if (props.$score >= 60) return `background: #f59e0b20; color: #f59e0b;`;
    return `background: #10b98120; color: #10b981;`;
  }}
`;

const ViolationsCount = styled.div<{ $count: number }>`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: ${props => props.$count > 0 ? '#ef4444' : props.theme.textSecondary};
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button<{ $variant: 'approve' | 'reject' | 'view' }>`
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;

  ${props => {
    switch (props.$variant) {
      case 'approve':
        return `
          background: #10b981;
          color: white;
          &:hover { background: #059669; }
        `;
      case 'reject':
        return `
          background: #ef4444;
          color: white;
          &:hover { background: #dc2626; }
        `;
      case 'view':
        return `
          background: ${props.theme.backgroundTertiary};
          color: ${props.theme.textPrimary};
          border: 1px solid ${props.theme.border};
          &:hover { background: ${props.theme.border}; }
        `;
    }
  }}
`;

const EmptyState = styled.div`
  padding: 60px 20px;
  text-align: center;
  color: ${props => props.theme.textSecondary};
`;

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
`;

const LoadingState = styled.div`
  padding: 40px 20px;
  text-align: center;
  color: ${props => props.theme.textSecondary};
`;

export const ModerationQueuePage: React.FC = () => {
  const [queueData, setQueueData] = useState<ModerationQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModerationQueue();
  }, [filter]);

  const fetchModerationQueue = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== 'all') {
        params.append('status_filter', filter);
      }

      const response = await fetch(`/moderation/queue?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch moderation queue');
      }

      const data = await response.json();
      setQueueData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (promotionId: string) => {
    try {
      const response = await fetch(`/moderation/decide/${promotionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          action: 'approve',
          reason: 'Approved by admin',
        }),
      });

      if (response.ok) {
        await fetchModerationQueue();
      }
    } catch (err) {
      console.error('Failed to approve promotion:', err);
    }
  };

  const handleReject = async (promotionId: string) => {
    try {
      const response = await fetch(`/moderation/decide/${promotionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          action: 'reject',
          reason: 'Rejected by admin',
        }),
      });

      if (response.ok) {
        await fetchModerationQueue();
      }
    } catch (err) {
      console.error('Failed to reject promotion:', err);
    }
  };

  if (loading) {
    return (
      <Container>
        <LoadingState>Loading moderation queue...</LoadingState>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Title>
          <FaExclamationTriangle />
          Error
        </Title>
        <div>Error loading moderation queue: {error}</div>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Title>
          <FaFlag />
          Content Moderation Queue
        </Title>
      </Header>

      {queueData && (
        <StatsContainer>
          <StatCard>
            <StatIcon>
              <FaClock />
            </StatIcon>
            <StatDetails>
              <StatLabel>Pending Review</StatLabel>
              <StatValue>{queueData.pending_count}</StatValue>
            </StatDetails>
          </StatCard>

          <StatCard $severity="warning">
            <StatIcon $severity="warning">
              <FaFlag />
            </StatIcon>
            <StatDetails>
              <StatLabel>Flagged for Review</StatLabel>
              <StatValue>{queueData.flagged_count}</StatValue>
            </StatDetails>
          </StatCard>

          <StatCard>
            <StatIcon>
              <FaEye />
            </StatIcon>
            <StatDetails>
              <StatLabel>Total Items</StatLabel>
              <StatValue>{queueData.total}</StatValue>
            </StatDetails>
          </StatCard>
        </StatsContainer>
      )}

      <FiltersContainer>
        <FilterButton
          $active={filter === 'all'}
          onClick={() => setFilter('all')}
        >
          All Items
        </FilterButton>
        <FilterButton
          $active={filter === 'pending'}
          onClick={() => setFilter('pending')}
        >
          <FaClock style={{ marginRight: 4 }} />
          Pending
        </FilterButton>
        <FilterButton
          $active={filter === 'flagged'}
          onClick={() => setFilter('flagged')}
        >
          <FaFlag style={{ marginRight: 4 }} />
          Flagged
        </FilterButton>
      </FiltersContainer>

      <QueueContainer>
        <QueueHeader>
          <div>Promotion</div>
          <div>Status</div>
          <div>Score</div>
          <div>Violations</div>
          <div>Actions</div>
        </QueueHeader>

        {queueData?.items.length === 0 ? (
          <EmptyState>
            <EmptyIcon>
              <FaCheck />
            </EmptyIcon>
            <div>No items requiring moderation</div>
          </EmptyState>
        ) : (
          queueData?.items.map((item) => (
            <QueueItem key={item.promotion_id}>
              <PromotionInfo>
                <PromotionTitle>{item.title}</PromotionTitle>
                <PromotionContent>{item.content}</PromotionContent>
                <PromotionMeta>
                  <span>By {item.creator_name || 'Unknown'}</span>
                  <span>•</span>
                  <span>{format(new Date(item.created_at), 'MMM d, yyyy')}</span>
                  <span>•</span>
                  <span>{item.media_type}</span>
                </PromotionMeta>
              </PromotionInfo>

              <StatusBadge $status={item.moderation_status}>
                {item.moderation_status}
              </StatusBadge>

              <ScoreBadge $score={item.moderation_score || 0}>
                {item.moderation_score?.toFixed(0) || 0}
              </ScoreBadge>

              <ViolationsCount $count={item.violations.length}>
                <FaExclamationTriangle />
                {item.violations.length}
              </ViolationsCount>

              <ActionButtons>
                {(item.moderation_status === 'pending' || item.moderation_status === 'flagged') && (
                  <>
                    <ActionButton
                      $variant="approve"
                      onClick={() => handleApprove(item.promotion_id)}
                    >
                      <FaCheck />
                      Approve
                    </ActionButton>
                    <ActionButton
                      $variant="reject"
                      onClick={() => handleReject(item.promotion_id)}
                    >
                      <FaTimes />
                      Reject
                    </ActionButton>
                  </>
                )}
                <ActionButton $variant="view">
                  <FaEye />
                  View
                </ActionButton>
              </ActionButtons>
            </QueueItem>
          ))
        )}
      </QueueContainer>
    </Container>
  );
};