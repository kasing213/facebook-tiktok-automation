import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  IconButton,
  Badge,
  Tooltip,
  Grid,
  Stack
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Schedule as PendingIcon,
  History as HistoryIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
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
    } catch (err: any) {
      setError(err.message || 'Failed to load verifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVerifications();
  }, []);

  const handleAction = async (verification: PendingVerification, action: 'approve' | 'reject' | 'review') => {
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

      // Reload data
      await loadVerifications();
    } catch (err: any) {
      setError(err.message || 'Action failed');
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
    } catch (err: any) {
      setError(err.message || 'Failed to load audit trail');
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'reviewing': return 'info';
      case 'verified': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
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
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Header with Stats */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Payment Verifications</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadVerifications}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {verifications.length}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Pending Reviews
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="success.main">
                  {stats.auto_verified}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Auto Verified
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="info.main">
                  {stats.manual_actions}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Manual Actions
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="warning.main">
                  {stats.avg_confidence.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg Confidence
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Verifications Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Pending Payment Verifications
          </Typography>

          {verifications.length === 0 ? (
            <Typography color="textSecondary" textAlign="center" py={4}>
              No pending verifications found.
            </Typography>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Invoice #</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Submitted</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {verifications.map((verification) => (
                    <TableRow key={verification.id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {verification.invoice_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{verification.customer_name}</TableCell>
                      <TableCell>
                        {formatCurrency(verification.amount, verification.currency)}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={verification.verification_status}
                          color={getStatusColor(verification.verification_status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {verification.confidence_score ? (
                          <Badge
                            badgeContent={`${verification.confidence_score.toFixed(0)}%`}
                            color={verification.confidence_score >= 80 ? 'success' : 'warning'}
                          />
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {formatDateTime(verification.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} justifyContent="center">
                          <Tooltip title="Approve Payment">
                            <IconButton
                              color="success"
                              size="small"
                              onClick={() => handleAction(verification, 'approve')}
                              disabled={processing === verification.id}
                            >
                              {processing === verification.id ? (
                                <CircularProgress size={16} />
                              ) : (
                                <ApproveIcon />
                              )}
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Mark for Review">
                            <IconButton
                              color="info"
                              size="small"
                              onClick={() => handleAction(verification, 'review')}
                              disabled={processing === verification.id}
                            >
                              <PendingIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Reject Payment">
                            <IconButton
                              color="error"
                              size="small"
                              onClick={() => handleAction(verification, 'reject')}
                              disabled={processing === verification.id}
                            >
                              <RejectIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="View Audit Trail">
                            <IconButton
                              size="small"
                              onClick={() => showAuditTrail(verification)}
                            >
                              <HistoryIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Action Confirmation Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'approve' && 'Approve Payment'}
          {actionType === 'reject' && 'Reject Payment'}
          {actionType === 'review' && 'Mark for Review'}
        </DialogTitle>
        <DialogContent>
          {selectedInvoice && (
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">
                Invoice: {selectedInvoice.invoice_number}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Customer: {selectedInvoice.customer_name}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Amount: {formatCurrency(selectedInvoice.amount, selectedInvoice.currency)}
              </Typography>
            </Box>
          )}

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Notes (Optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any notes about this verification..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={confirmAction}
            disabled={processing !== null}
            color={actionType === 'reject' ? 'error' : 'primary'}
          >
            {processing !== null ? 'Processing...' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Audit Trail Dialog */}
      <Dialog open={auditDialogOpen} onClose={() => setAuditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Verification Audit Trail
          {selectedInvoice && (
            <Typography variant="subtitle2" color="textSecondary">
              Invoice: {selectedInvoice.invoice_number}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {auditTrail.length === 0 ? (
            <Typography color="textSecondary">No audit trail found.</Typography>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date/Time</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Status Change</TableCell>
                  <TableCell>By</TableCell>
                  <TableCell>Notes</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditTrail.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDateTime(entry.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={getActionLabel(entry.action)} size="small" />
                    </TableCell>
                    <TableCell>
                      {entry.previous_status && (
                        <span>
                          <Chip label={entry.previous_status} size="small" color="default" />
                          {' → '}
                        </span>
                      )}
                      <Chip
                        label={entry.new_status}
                        size="small"
                        color={getStatusColor(entry.new_status) as any}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {entry.verified_by_name}
                        {entry.confidence_score && (
                          <Typography variant="caption" display="block" color="textSecondary">
                            Confidence: {entry.confidence_score.toFixed(1)}%
                          </Typography>
                        )}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {entry.notes || '—'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAuditDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VerificationsPage;