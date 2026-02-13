import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FaCheck, FaTimes, FaClock, FaHistory, FaSyncAlt } from 'react-icons/fa';
import { LoadingSpinner } from '../LoadingSpinner';
import { LoadingButton } from '../common/LoadingButton';
import { verificationApi } from '../../services/verificationApi';

interface PendingVerification {
  id: string;
  invoice_number: string;
  customer_name: string;
  amount: number;
  currency: string;
  verification_status: string;
  created_at: string;
  screenshot_uploaded_at?: string;
  confidence_score?: number;
  ocr_notes?: string;
}

interface AuditTrailEntry {
  id: string;
  action: string;
  previous_status?: string;
  new_status: string;
  confidence_score?: number;
  verified_by_name: string;
  verification_method?: string;
  notes?: string;
  created_at: string;
}

interface VerificationStats {
  total_verifications: number;
  auto_verified: number;
  manual_actions: number;
  avg_confidence: number;
}

// Styled components

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const AlertBox = styled.div<{ $type: 'error' | 'success' }>`
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: ${props => props.$type === 'error' ? props.theme.errorLight : props.theme.successLight};
  color: ${props => props.$type === 'error' ? props.theme.error : props.theme.success};
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0.25rem;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  background: linear-gradient(135deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`;

const RefreshButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  background: ${props => props.theme.card};
  color: ${props => props.theme.textSecondary};
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    background: ${props => props.theme.cardHover};
    color: ${props => props.theme.accent};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 14px;
    height: 14px;
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.25rem;
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
  }
`;

const StatValue = styled.div<{ $color?: string }>`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.$color || props.theme.textPrimary};
`;

const StatLabel = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.25rem;
`;

const Card = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  overflow: hidden;
`;

const CardHeader = styled.div`
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid ${props => props.theme.border};
`;

const CardTitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`;

const TableWrapper = styled.div`
  overflow-x: auto;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
`;

const TableHead = styled.thead`
  background: ${props => props.theme.backgroundTertiary};
`;

const HeaderCell = styled.th`
  text-align: left;
  padding: 0.875rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid ${props => props.theme.border};
  white-space: nowrap;

  &:last-child {
    text-align: center;
  }
`;

const TableRow = styled.tr`
  border-bottom: 1px solid ${props => props.theme.border};

  &:hover {
    background-color: ${props => props.theme.backgroundTertiary};
  }
`;

const TableCell = styled.td`
  padding: 1rem;
  font-size: 0.875rem;
  color: ${props => props.theme.textPrimary};
  vertical-align: middle;
`;

const MonoText = styled.span`
  font-family: 'SF Mono', 'Fira Code', 'Fira Mono', monospace;
  font-size: 0.8125rem;
`;

const MutedText = styled.span`
  color: ${props => props.theme.textSecondary};
  font-size: 0.8125rem;
`;

const StatusBadge = styled.span<{ $status: string }>`
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;

  ${props => {
    switch (props.$status) {
      case 'verified':
        return `background: #d4edda; color: #155724;`;
      case 'pending':
        return `background: #fff3cd; color: #856404;`;
      case 'reviewing':
        return `background: #cce5ff; color: #004085;`;
      case 'rejected':
        return `background: #f8d7da; color: #721c24;`;
      default:
        return `background: #e2e3e5; color: #383d41;`;
    }
  }}
`;

const ConfidenceBadge = styled.span<{ $high: boolean }>`
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  background: ${props => props.$high ? '#d4edda' : '#fff3cd'};
  color: ${props => props.$high ? '#155724' : '#856404'};
`;

const ActionsCell = styled.td`
  padding: 1rem;
  vertical-align: middle;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.25rem;
  justify-content: center;
`;

const IconBtn = styled.button<{ $color?: string }>`
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: ${props => props.theme.textMuted};
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: color 0.2s ease, transform 0.15s ease, background 0.15s ease;

  &:hover:not(:disabled) {
    color: ${props => props.$color || props.theme.accent};
    background: ${props => props.theme.mode === 'dark'
      ? 'rgba(62, 207, 142, 0.1)'
      : 'rgba(74, 144, 226, 0.08)'};
    transform: scale(1.1);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 16px;
    height: 16px;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 1rem;
  color: ${props => props.theme.textSecondary};
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
`;

// Modal styles

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${props => props.theme.overlay};
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
`;

const ModalContent = styled.div<{ $wide?: boolean }>`
  background: ${props => props.theme.card};
  border-radius: 12px;
  padding: 0;
  max-width: ${props => props.$wide ? '700px' : '500px'};
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: scaleIn 0.3s ease-out;

  @keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
`;

const ModalHeader = styled.div`
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid ${props => props.theme.border};
`;

const ModalTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`;

const ModalSubtitle = styled.div`
  font-size: 0.8125rem;
  color: ${props => props.theme.textSecondary};
  margin-top: 0.25rem;
`;

const ModalBody = styled.div`
  padding: 1.5rem;
`;

const ModalFooter = styled.div`
  padding: 1rem 1.5rem;
  border-top: 1px solid ${props => props.theme.border};
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
`;

const DetailRow = styled.div`
  font-size: 0.875rem;
  color: ${props => props.theme.textSecondary};
  margin-bottom: 0.25rem;
`;

const FormTextarea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.875rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};
  min-height: 80px;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;

  &::placeholder {
    color: ${props => props.theme.textMuted};
  }

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
    box-shadow: 0 0 0 2px ${props => props.theme.mode === 'dark'
      ? 'rgba(62, 207, 142, 0.1)'
      : 'rgba(74, 144, 226, 0.1)'};
  }
`;

const FormLabel = styled.label`
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  margin-bottom: 0.5rem;
`;

const AuditTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const AuditHeaderCell = styled.th`
  text-align: left;
  padding: 0.625rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid ${props => props.theme.border};
`;

const AuditRow = styled.tr`
  border-bottom: 1px solid ${props => props.theme.border};
`;

const AuditCell = styled.td`
  padding: 0.75rem;
  font-size: 0.8125rem;
  color: ${props => props.theme.textPrimary};
  vertical-align: top;
`;

const Arrow = styled.span`
  color: ${props => props.theme.textMuted};
  margin: 0 0.25rem;
`;

const ConfidenceCaption = styled.div`
  font-size: 0.6875rem;
  color: ${props => props.theme.textMuted};
  margin-top: 0.125rem;
`;

// Component

const VerificationsPage: React.FC = () => {
  const [verifications, setVerifications] = useState<PendingVerification[]>([]);
  const [stats, setStats] = useState<VerificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog states
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<PendingVerification | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditTrailEntry[]>([]);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'review'>('approve');
  const [notes, setNotes] = useState('');

  const loadVerifications = async () => {
    try {
      setLoading(true);
      setError(null);

      const [verificationsData, statsData] = await Promise.all([
        verificationApi.getPendingVerifications(),
        verificationApi.getStats()
      ]);

      setVerifications(verificationsData);
      setStats(statsData);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load verifications';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVerifications();
  }, []);

  const handleAction = (verification: PendingVerification, action: 'approve' | 'reject' | 'review') => {
    setSelectedInvoice(verification);
    setActionType(action);
    setNotes('');
    setActionDialogOpen(true);
  };

  const confirmAction = async () => {
    if (!selectedInvoice) return;

    try {
      setProcessing(selectedInvoice.id);
      setError(null);

      let response;
      switch (actionType) {
        case 'approve':
          response = await verificationApi.approveVerification(selectedInvoice.id, notes);
          break;
        case 'reject':
          response = await verificationApi.rejectVerification(selectedInvoice.id, notes);
          break;
        case 'review':
          response = await verificationApi.markForReview(selectedInvoice.id, notes);
          break;
      }

      setSuccess(response.message);
      setActionDialogOpen(false);
      setSelectedInvoice(null);
      setNotes('');

      await loadVerifications();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Action failed';
      setError(message);
    } finally {
      setProcessing(null);
    }
  };

  const showAuditTrail = async (verification: PendingVerification) => {
    try {
      setSelectedInvoice(verification);
      const trail = await verificationApi.getAuditTrail(verification.id);
      setAuditTrail(trail);
      setAuditDialogOpen(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load audit trail';
      setError(message);
    }
  };

  const formatCurrency = (amount: number, currency: string): string => {
    if (amount === null || amount === undefined || isNaN(amount)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency === 'KHR' ? 'USD' : currency
    }).format(amount);
  };

  const formatDateTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getActionLabel = (action: string) => {
    switch (action) {
      case 'auto_verified': return 'Auto Verified';
      case 'manual_approved': return 'Manually Approved';
      case 'manual_rejected': return 'Manually Rejected';
      case 'manual_pending': return 'Marked for Review';
      default: return action;
    }
  };

  if (loading) {
    return (
      <LoadingContainer>
        <LoadingSpinner size="large" />
      </LoadingContainer>
    );
  }

  return (
    <Container>
      {error && (
        <AlertBox $type="error">
          <span>{error}</span>
          <CloseButton onClick={() => setError(null)}>&times;</CloseButton>
        </AlertBox>
      )}

      {success && (
        <AlertBox $type="success">
          <span>{success}</span>
          <CloseButton onClick={() => setSuccess(null)}>&times;</CloseButton>
        </AlertBox>
      )}

      {/* Header */}
      <Header>
        <Title>Payment Verifications</Title>
        <RefreshButton onClick={loadVerifications} disabled={loading}>
          <FaSyncAlt />
          Refresh
        </RefreshButton>
      </Header>

      {/* Stats Cards */}
      {stats && (
        <StatsGrid>
          <StatCard>
            <StatValue $color="#4a90e2">{verifications.length}</StatValue>
            <StatLabel>Pending Reviews</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue $color="#28a745">{stats.auto_verified}</StatValue>
            <StatLabel>Auto Verified</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue $color="#17a2b8">{stats.manual_actions}</StatValue>
            <StatLabel>Manual Actions</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue $color="#ffc107">{stats.avg_confidence.toFixed(1)}%</StatValue>
            <StatLabel>Avg Confidence</StatLabel>
          </StatCard>
        </StatsGrid>
      )}

      {/* Verifications Table */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Payment Verifications</CardTitle>
        </CardHeader>

        {verifications.length === 0 ? (
          <EmptyState>No pending verifications found.</EmptyState>
        ) : (
          <TableWrapper>
            <Table>
              <TableHead>
                <tr>
                  <HeaderCell>Invoice #</HeaderCell>
                  <HeaderCell>Customer</HeaderCell>
                  <HeaderCell>Amount</HeaderCell>
                  <HeaderCell>Status</HeaderCell>
                  <HeaderCell>Confidence</HeaderCell>
                  <HeaderCell>Submitted</HeaderCell>
                  <HeaderCell>Actions</HeaderCell>
                </tr>
              </TableHead>
              <tbody>
                {verifications.map((verification) => (
                  <TableRow key={verification.id}>
                    <TableCell>
                      <MonoText>{verification.invoice_number}</MonoText>
                    </TableCell>
                    <TableCell>{verification.customer_name}</TableCell>
                    <TableCell>
                      {formatCurrency(verification.amount, verification.currency)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge $status={verification.verification_status}>
                        {verification.verification_status}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      {verification.confidence_score ? (
                        <ConfidenceBadge $high={verification.confidence_score >= 80}>
                          {verification.confidence_score.toFixed(0)}%
                        </ConfidenceBadge>
                      ) : (
                        <MutedText>&mdash;</MutedText>
                      )}
                    </TableCell>
                    <TableCell>
                      <MutedText>{formatDateTime(verification.created_at)}</MutedText>
                    </TableCell>
                    <ActionsCell>
                      <ActionButtons>
                        <IconBtn
                          $color="#28a745"
                          title="Approve Payment"
                          onClick={() => handleAction(verification, 'approve')}
                          disabled={processing === verification.id}
                        >
                          {processing === verification.id ? (
                            <LoadingSpinner size="small" />
                          ) : (
                            <FaCheck />
                          )}
                        </IconBtn>

                        <IconBtn
                          $color="#17a2b8"
                          title="Mark for Review"
                          onClick={() => handleAction(verification, 'review')}
                          disabled={processing === verification.id}
                        >
                          <FaClock />
                        </IconBtn>

                        <IconBtn
                          $color="#dc3545"
                          title="Reject Payment"
                          onClick={() => handleAction(verification, 'reject')}
                          disabled={processing === verification.id}
                        >
                          <FaTimes />
                        </IconBtn>

                        <IconBtn
                          title="View Audit Trail"
                          onClick={() => showAuditTrail(verification)}
                        >
                          <FaHistory />
                        </IconBtn>
                      </ActionButtons>
                    </ActionsCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>
          </TableWrapper>
        )}
      </Card>

      {/* Action Confirmation Dialog */}
      {actionDialogOpen && (
        <ModalOverlay onClick={() => setActionDialogOpen(false)}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>
                {actionType === 'approve' && 'Approve Payment'}
                {actionType === 'reject' && 'Reject Payment'}
                {actionType === 'review' && 'Mark for Review'}
              </ModalTitle>
            </ModalHeader>
            <ModalBody>
              {selectedInvoice && (
                <div style={{ marginBottom: '1rem' }}>
                  <DetailRow>Invoice: {selectedInvoice.invoice_number}</DetailRow>
                  <DetailRow>Customer: {selectedInvoice.customer_name}</DetailRow>
                  <DetailRow>Amount: {formatCurrency(selectedInvoice.amount, selectedInvoice.currency)}</DetailRow>
                </div>
              )}
              <FormLabel>Notes (Optional)</FormLabel>
              <FormTextarea
                value={notes}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
                placeholder="Add any notes about this verification..."
              />
            </ModalBody>
            <ModalFooter>
              <LoadingButton
                variant="secondary"
                size="small"
                onClick={() => setActionDialogOpen(false)}
              >
                Cancel
              </LoadingButton>
              <LoadingButton
                variant={actionType === 'reject' ? 'danger' : 'primary'}
                size="small"
                loading={processing !== null}
                onClick={confirmAction}
              >
                Confirm
              </LoadingButton>
            </ModalFooter>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* Audit Trail Dialog */}
      {auditDialogOpen && (
        <ModalOverlay onClick={() => setAuditDialogOpen(false)}>
          <ModalContent $wide onClick={e => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>Verification Audit Trail</ModalTitle>
              {selectedInvoice && (
                <ModalSubtitle>Invoice: {selectedInvoice.invoice_number}</ModalSubtitle>
              )}
            </ModalHeader>
            <ModalBody>
              {auditTrail.length === 0 ? (
                <MutedText>No audit trail found.</MutedText>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <AuditTable>
                    <thead>
                      <tr>
                        <AuditHeaderCell>Date/Time</AuditHeaderCell>
                        <AuditHeaderCell>Action</AuditHeaderCell>
                        <AuditHeaderCell>Status Change</AuditHeaderCell>
                        <AuditHeaderCell>By</AuditHeaderCell>
                        <AuditHeaderCell>Notes</AuditHeaderCell>
                      </tr>
                    </thead>
                    <tbody>
                      {auditTrail.map((entry) => (
                        <AuditRow key={entry.id}>
                          <AuditCell>{formatDateTime(entry.created_at)}</AuditCell>
                          <AuditCell>
                            <StatusBadge $status={entry.new_status}>
                              {getActionLabel(entry.action)}
                            </StatusBadge>
                          </AuditCell>
                          <AuditCell>
                            {entry.previous_status && (
                              <>
                                <StatusBadge $status={entry.previous_status}>
                                  {entry.previous_status}
                                </StatusBadge>
                                <Arrow>&rarr;</Arrow>
                              </>
                            )}
                            <StatusBadge $status={entry.new_status}>
                              {entry.new_status}
                            </StatusBadge>
                          </AuditCell>
                          <AuditCell>
                            {entry.verified_by_name}
                            {entry.confidence_score && (
                              <ConfidenceCaption>
                                Confidence: {entry.confidence_score.toFixed(1)}%
                              </ConfidenceCaption>
                            )}
                          </AuditCell>
                          <AuditCell>
                            <MutedText>{entry.notes || '\u2014'}</MutedText>
                          </AuditCell>
                        </AuditRow>
                      ))}
                    </tbody>
                  </AuditTable>
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              <LoadingButton
                variant="secondary"
                size="small"
                onClick={() => setAuditDialogOpen(false)}
              >
                Close
              </LoadingButton>
            </ModalFooter>
          </ModalContent>
        </ModalOverlay>
      )}
    </Container>
  );
};

export default VerificationsPage;
