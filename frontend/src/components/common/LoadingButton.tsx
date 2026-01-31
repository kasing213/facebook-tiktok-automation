import React from 'react'
import styled from 'styled-components'
import { LoadingSpinner } from '../LoadingSpinner'
import { easings } from '../../styles/animations'

interface LoadingButtonProps {
  children: React.ReactNode
  loading?: boolean
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'small' | 'medium' | 'large'
  onClick?: () => void | Promise<void>
  type?: 'button' | 'submit' | 'reset'
  className?: string
  fullWidth?: boolean
  minLoadingTime?: number
  style?: React.CSSProperties
}

const StyledButton = styled.button<{
  $variant: 'primary' | 'secondary' | 'danger'
  $size: 'small' | 'medium' | 'large'
  $fullWidth?: boolean
  $loading?: boolean
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ${easings.easeOutCubic};
  opacity: ${props => props.disabled ? 0.6 : 1};
  pointer-events: ${props => props.disabled ? 'none' : 'auto'};
  width: ${props => props.$fullWidth ? '100%' : 'auto'};

  ${props => {
    switch (props.$size) {
      case 'small':
        return `
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
        `
      case 'large':
        return `
          padding: 1rem 1.5rem;
          font-size: 1rem;
        `
      default:
        return `
          padding: 0.75rem 1.25rem;
          font-size: 0.9375rem;
        `
    }
  }}

  ${props => {
    switch (props.$variant) {
      case 'primary':
        return `
          background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
          color: white;

          &:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(74, 144, 226, 0.35);
          }

          &:active:not(:disabled) {
            transform: translateY(0) scale(0.98);
          }
        `
      case 'danger':
        return `
          background: #dc3545;
          color: white;

          &:hover:not(:disabled) {
            background: #c82333;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
          }

          &:active:not(:disabled) {
            transform: translateY(0) scale(0.98);
          }
        `
      default:
        return `
          background: ${props.theme?.card || '#ffffff'};
          color: ${props.theme?.textSecondary || '#6b7280'};
          border: 1px solid ${props.theme?.border || '#e5e7eb'};

          &:hover:not(:disabled) {
            background: ${props.theme?.cardHover || '#f9fafb'};
            transform: translateY(-1px);
          }

          &:active:not(:disabled) {
            transform: translateY(0) scale(0.98);
          }
        `
    }
  }}
`

const ButtonContent = styled.span<{ $loading?: boolean }>`
  opacity: ${props => props.$loading ? 0 : 1};
  transition: opacity 0.2s ease;
`

const SpinnerWrapper = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
`

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  children,
  loading = false,
  disabled = false,
  variant = 'primary',
  size = 'medium',
  onClick,
  type = 'button',
  className,
  fullWidth = false,
  minLoadingTime = 300,
  style
}) => {
  const [isLoading, setIsLoading] = React.useState(false)

  const handleClick = async () => {
    if (loading || isLoading || disabled || !onClick) return

    setIsLoading(true)
    const startTime = Date.now()

    try {
      await onClick()
    } catch (error) {
      console.error('Button action failed:', error)
    } finally {
      // Ensure minimum loading time for better UX
      const elapsed = Date.now() - startTime
      const remainingTime = minLoadingTime - elapsed

      if (remainingTime > 0) {
        setTimeout(() => setIsLoading(false), remainingTime)
      } else {
        setIsLoading(false)
      }
    }
  }

  const isButtonLoading = loading || isLoading
  const isButtonDisabled = disabled || isButtonLoading

  return (
    <StyledButton
      $variant={variant}
      $size={size}
      $fullWidth={fullWidth}
      $loading={isButtonLoading}
      disabled={isButtonDisabled}
      onClick={handleClick}
      type={type}
      className={className}
      style={style}
    >
      <ButtonContent $loading={isButtonLoading}>
        {children}
      </ButtonContent>
      {isButtonLoading && (
        <SpinnerWrapper>
          <LoadingSpinner size={size === 'small' ? 'small' : 'small'} />
        </SpinnerWrapper>
      )}
    </StyledButton>
  )
}