import React from 'react'
import styled from 'styled-components'
import { useTranslation } from 'react-i18next'

const StyledRefreshButton = styled.button<{ $refreshing?: boolean }>`
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  background: ${props => props.theme.card};
  color: ${props => props.theme.textSecondary};
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: ${props => props.theme.hover};
    color: ${props => props.theme.textPrimary};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  svg {
    width: 16px;
    height: 16px;
    transition: transform 0.2s ease;
    transform: ${props => props.$refreshing ? 'rotate(360deg)' : 'rotate(0deg)'};
  }

  ${props => props.$refreshing && `
    svg {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `}
`

const LastUpdated = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.textMuted};
  margin-left: 0.5rem;
`

const RefreshContainer = styled.div`
  display: flex;
  align-items: center;
`

interface RefreshButtonProps {
  onRefresh: () => void | Promise<void>
  refreshing?: boolean
  disabled?: boolean
  lastUpdated?: Date | null
  showLastUpdated?: boolean
  className?: string
}

export const RefreshButton: React.FC<RefreshButtonProps> = ({
  onRefresh,
  refreshing = false,
  disabled = false,
  lastUpdated = null,
  showLastUpdated = true,
  className
}) => {
  const { t } = useTranslation()

  return (
    <RefreshContainer className={className}>
      <StyledRefreshButton
        $refreshing={refreshing}
        onClick={onRefresh}
        disabled={refreshing || disabled}
        title={t('common.refresh', 'Refresh data')}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      </StyledRefreshButton>
      {showLastUpdated && lastUpdated && (
        <LastUpdated title={`Last updated: ${lastUpdated.toLocaleString()}`}>
          {lastUpdated.toLocaleTimeString()}
        </LastUpdated>
      )}
    </RefreshContainer>
  )
}