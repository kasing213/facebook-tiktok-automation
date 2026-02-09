import apiClient from './apiClient';

export interface PendingVerification {
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

export interface AuditTrailEntry {
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

export interface VerificationStats {
  total_verifications: number;
  auto_verified: number;
  manual_actions: number;
  avg_confidence: number;
  actions_breakdown: Array<{
    action: string;
    method?: string;
    count: number;
    avg_confidence?: number;
  }>;
}

export interface ActionResponse {
  success: boolean;
  message: string;
  invoice_id: string;
  status: string;
}

class VerificationApi {
  private baseUrl = '/api/verifications';

  /**
   * Get list of pending payment verifications
   */
  async getPendingVerifications(params?: {
    limit?: number;
    skip?: number;
  }): Promise<PendingVerification[]> {
    const queryParams = new URLSearchParams();

    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.skip) queryParams.append('skip', params.skip.toString());

    const response = await apiClient.get(
      `${this.baseUrl}/pending${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    );

    if (response.status !== 200) {
      throw new Error(`Failed to fetch pending verifications: ${response.statusText}`);
    }

    return response.data;
  }

  /**
   * Get audit trail for a specific invoice
   */
  async getAuditTrail(invoiceId: string): Promise<AuditTrailEntry[]> {
    const response = await apiClient.get(`${this.baseUrl}/${invoiceId}/history`);

    if (response.status !== 200) {
      throw new Error(`Failed to fetch audit trail: ${response.statusText}`);
    }

    return response.data;
  }

  /**
   * Approve a payment verification
   */
  async approveVerification(invoiceId: string, notes?: string): Promise<ActionResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${invoiceId}/approve`, {
      notes
    });

    if (response.status !== 200) {
      throw new Error(`Failed to approve verification: ${response.statusText}`);
    }

    return response.data;
  }

  /**
   * Reject a payment verification
   */
  async rejectVerification(invoiceId: string, notes?: string): Promise<ActionResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${invoiceId}/reject`, {
      notes
    });

    if (response.status !== 200) {
      throw new Error(`Failed to reject verification: ${response.statusText}`);
    }

    return response.data;
  }

  /**
   * Mark verification for manual review
   */
  async markForReview(invoiceId: string, notes?: string): Promise<ActionResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${invoiceId}/review`, {
      notes
    });

    if (response.status !== 200) {
      throw new Error(`Failed to mark for review: ${response.statusText}`);
    }

    return response.data;
  }

  /**
   * Get verification statistics
   */
  async getStats(days: number = 30): Promise<VerificationStats> {
    const response = await apiClient.get(`${this.baseUrl}/stats?days=${days}`);

    if (response.status !== 200) {
      throw new Error(`Failed to fetch verification stats: ${response.statusText}`);
    }

    return response.data;
  }
}

export const verificationApi = new VerificationApi();