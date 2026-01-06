import styled from 'styled-components'

// Layout
export const PageContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`

export const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
`

export const PageTitle = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

export const BackLink = styled.button`
  background: transparent;
  border: none;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
  margin-bottom: 1rem;

  &:hover {
    color: #4a90e2;
  }
`

// Cards
export const Card = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }
`

export const CardTitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

export const CardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`

// Summary Cards (OpenAI-style)
export const SummaryCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
`

export const SummaryLabel = styled.span`
  font-size: 0.875rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
  margin-bottom: 0.5rem;
`

export const SummaryValue = styled.span`
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
`

export const SummarySubtext = styled.span`
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.5rem;
`

// Plan Card
export const PlanCard = styled.div<{ $current?: boolean; $popular?: boolean }>`
  background: white;
  border: 2px solid ${props => props.$current ? '#4a90e2' : props.$popular ? '#ffd700' : '#e5e7eb'};
  border-radius: 12px;
  padding: 2rem;
  position: relative;
  transition: all 0.2s ease;

  ${props => props.$popular && `
    &:before {
      content: 'Popular';
      position: absolute;
      top: -12px;
      left: 50%;
      transform: translateX(-50%);
      background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
      color: #1f2937;
      padding: 0.25rem 1rem;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
    }
  `}

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
`

export const PlanName = styled.h3`
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
`

export const PlanPrice = styled.div`
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;

  span {
    font-size: 1rem;
    font-weight: 400;
    color: #6b7280;
  }
`

export const PlanPeriod = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 1.5rem 0;
`

export const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
`

export const FeatureItem = styled.li<{ $included: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  font-size: 0.9375rem;
  color: ${props => props.$included ? '#1f2937' : '#9ca3af'};
  text-decoration: ${props => props.$included ? 'none' : 'line-through'};

  &:before {
    content: '${props => props.$included ? '✓' : '✗'}';
    color: ${props => props.$included ? '#28a745' : '#dc3545'};
    font-weight: 700;
    font-size: 1rem;
  }
`

// Buttons
export const PrimaryButton = styled.button`
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
`

export const SecondaryButton = styled.button`
  background: white;
  color: #4a90e2;
  border: 2px solid #4a90e2;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:hover:not(:disabled) {
    background: #f0f7ff;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

export const UpgradeButton = styled.button`
  background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
  color: #1f2937;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3);
  }
`

export const CurrentPlanButton = styled.button`
  background: #e5e7eb;
  color: #6b7280;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: default;
  width: 100%;
`

// Payment Method
export const PaymentMethodCard = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
`

export const CardBrandIcon = styled.div<{ $brand?: string }>`
  width: 48px;
  height: 32px;
  background: ${props => {
    switch (props.$brand?.toLowerCase()) {
      case 'visa': return '#1A1F71'
      case 'mastercard': return '#EB001B'
      case 'amex': return '#006FCF'
      default: return '#6b7280'
    }
  }};
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
`

export const CardDetails = styled.div`
  flex: 1;
`

export const CardNumber = styled.p`
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
`

export const CardExpiry = styled.p`
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: #6b7280;
`

// Payment History Table
export const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`

export const TableHead = styled.thead`
  background: #f9fafb;
`

export const TableRow = styled.tr`
  border-bottom: 1px solid #e5e7eb;

  &:last-child {
    border-bottom: none;
  }
`

export const TableHeader = styled.th`
  text-align: left;
  padding: 0.875rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`

export const TableCell = styled.td`
  padding: 1rem;
  font-size: 0.9375rem;
  color: #1f2937;
`

export const StatusBadge = styled.span<{ $status: 'paid' | 'pending' | 'failed' | 'refunded' }>`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;

  ${props => {
    switch (props.$status) {
      case 'paid':
        return 'background: #d1fae5; color: #065f46;'
      case 'pending':
        return 'background: #fef3c7; color: #92400e;'
      case 'failed':
        return 'background: #fee2e2; color: #991b1b;'
      case 'refunded':
        return 'background: #e5e7eb; color: #374151;'
    }
  }}
`

export const DownloadLink = styled.button`
  background: transparent;
  border: none;
  color: #4a90e2;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    text-decoration: underline;
  }

  &:disabled {
    color: #9ca3af;
    cursor: not-allowed;
  }
`

// Pagination
export const Pagination = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  margin-top: 1rem;
  border-top: 1px solid #e5e7eb;
`

export const PaginationInfo = styled.span`
  font-size: 0.875rem;
  color: #6b7280;
`

export const PaginationButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`

export const PaginationButton = styled.button<{ $active?: boolean }>`
  padding: 0.5rem 0.75rem;
  border: 1px solid ${props => props.$active ? '#4a90e2' : '#e5e7eb'};
  background: ${props => props.$active ? '#4a90e2' : 'white'};
  color: ${props => props.$active ? 'white' : '#6b7280'};
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    border-color: #4a90e2;
    color: ${props => props.$active ? 'white' : '#4a90e2'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

// Tier Badge
export const TierBadge = styled.span<{ $tier: 'free' | 'pro' }>`
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;

  ${props => props.$tier === 'pro' ? `
    background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
    color: #1f2937;
  ` : `
    background: #e5e7eb;
    color: #6b7280;
  `}
`

// Empty State
export const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 2rem;
  color: #6b7280;
`

export const EmptyIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
`

export const EmptyText = styled.p`
  font-size: 1rem;
  margin: 0;
`

// Loading
export const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 3rem;

  &:after {
    content: '';
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top-color: #4a90e2;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

// Error
export const ErrorMessage = styled.div`
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  color: #991b1b;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

// Pricing Toggle
export const PricingToggle = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
`

export const ToggleLabel = styled.span<{ $active: boolean }>`
  font-size: 0.9375rem;
  font-weight: ${props => props.$active ? 600 : 400};
  color: ${props => props.$active ? '#1f2937' : '#6b7280'};
  cursor: pointer;
  transition: all 0.2s ease;
`

export const ToggleSwitch = styled.button<{ $checked: boolean }>`
  width: 56px;
  height: 28px;
  background: ${props => props.$checked ? 'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)' : '#e5e7eb'};
  border: none;
  border-radius: 14px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;

  &:after {
    content: '';
    position: absolute;
    top: 2px;
    left: ${props => props.$checked ? '30px' : '2px'};
    width: 24px;
    height: 24px;
    background: white;
    border-radius: 50%;
    transition: left 0.2s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
`

export const SaveBadge = styled.span`
  background: #d1fae5;
  color: #065f46;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
`
