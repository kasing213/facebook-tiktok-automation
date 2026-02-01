import React from 'react'
import styled, { keyframes } from 'styled-components'

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
`

const progressFill = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
`

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`

const ProgressBar = styled.div<{ $variant?: 'default' | 'success' | 'warning' | 'error' }>`
  width: 100%;
  height: 4px;
  background: ${props => props.theme?.background || '#f3f4f6'};
  border-radius: 2px;
  overflow: hidden;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 30%;
    background: ${props => {
      switch (props.$variant) {
        case 'success': return '#10b981'
        case 'warning': return '#f59e0b'
        case 'error': return '#ef4444'
        default: return '#3b82f6'
      }
    }};
    animation: ${progressFill} 1.5s infinite ease-in-out;
  }
`

const Message = styled.div<{ $size?: 'small' | 'medium' | 'large' }>`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${props => props.theme?.textSecondary || '#6b7280'};
  font-size: ${props => {
    switch (props.$size) {
      case 'small': return '0.75rem'
      case 'large': return '1rem'
      default: return '0.875rem'
    }
  }};
`

const Dot = styled.div`
  width: 6px;
  height: 6px;
  background: ${props => props.theme?.accent || '#3b82f6'};
  border-radius: 50%;
  animation: ${pulse} 1s infinite;

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
`

const DotsContainer = styled.div`
  display: flex;
  gap: 2px;
`

const SkeletonLine = styled.div<{ $width?: string; $height?: string }>`
  height: ${props => props.$height || '1rem'};
  width: ${props => props.$width || '100%'};
  background: linear-gradient(
    90deg,
    ${props => props.theme?.background || '#f3f4f6'} 25%,
    ${props => props.theme?.backgroundTertiary || '#e5e7eb'} 50%,
    ${props => props.theme?.background || '#f3f4f6'} 75%
  );
  background-size: 200% 100%;
  border-radius: 4px;
  animation: ${progressFill} 1.5s infinite;
`

const SkeletonContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
`

interface ProgressIndicatorProps {
  variant?: 'default' | 'success' | 'warning' | 'error'
  message?: string
  size?: 'small' | 'medium' | 'large'
  showProgress?: boolean
  className?: string
}

interface LoadingDotsProps {
  size?: 'small' | 'medium' | 'large'
  className?: string
}

interface SkeletonLoaderProps {
  lines?: number
  className?: string
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  variant = 'default',
  message = 'Loading...',
  size = 'medium',
  showProgress = true,
  className
}) => {
  return (
    <Container className={className}>
      {showProgress && <ProgressBar $variant={variant} />}
      <Message $size={size}>
        <LoadingDots size={size} />
        {message}
      </Message>
    </Container>
  )
}

export const LoadingDots: React.FC<LoadingDotsProps> = ({
  size: _size = 'medium',
  className
}) => {
  return (
    <DotsContainer className={className}>
      <Dot />
      <Dot />
      <Dot />
    </DotsContainer>
  )
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  lines = 3,
  className
}) => {
  return (
    <SkeletonContainer className={className}>
      {Array.from({ length: lines }, (_, i) => (
        <SkeletonLine
          key={i}
          $width={i === lines - 1 ? '60%' : '100%'}
          $height={i === 0 ? '1.25rem' : '1rem'}
        />
      ))}
    </SkeletonContainer>
  )
}

export default ProgressIndicator