import React from 'react'
import styled from 'styled-components'
import { InvoiceStatus } from '../../types/invoice'

interface StatusBadgeProps {
  status: InvoiceStatus
}

const Badge = styled.span<{ $status: InvoiceStatus }>`
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;

  ${props => {
    switch (props.$status) {
      case 'paid':
        return `
          background: #d4edda;
          color: #155724;
        `
      case 'pending':
        return `
          background: #fff3cd;
          color: #856404;
        `
      case 'overdue':
        return `
          background: #f8d7da;
          color: #721c24;
        `
      case 'cancelled':
        return `
          background: #e2e3e5;
          color: #383d41;
        `
      case 'draft':
      default:
        return `
          background: #cce5ff;
          color: #004085;
        `
    }
  }}
`

export const InvoiceStatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  return <Badge $status={status}>{status}</Badge>
}

export default InvoiceStatusBadge
