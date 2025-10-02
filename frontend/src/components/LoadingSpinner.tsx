import React from 'react'
import styled, { keyframes } from 'styled-components'

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`

const SpinnerContainer = styled.div<{ size?: 'small' | 'medium' | 'large' }>`
  display: inline-block;
  ${props => {
    switch (props.size) {
      case 'small':
        return 'width: 16px; height: 16px;'
      case 'large':
        return 'width: 32px; height: 32px;'
      default:
        return 'width: 24px; height: 24px;'
    }
  }}
`

const Spinner = styled.div<{ size?: 'small' | 'medium' | 'large' }>`
  width: 100%;
  height: 100%;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;

  ${props => props.size === 'small' && `
    border-width: 1px;
  `}
`

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'
  className?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  className
}) => {
  return (
    <SpinnerContainer size={size} className={className}>
      <Spinner size={size} />
    </SpinnerContainer>
  )
}