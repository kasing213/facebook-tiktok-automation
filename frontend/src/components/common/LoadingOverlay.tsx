import React from 'react'
import styled, { keyframes } from 'styled-components'
import { LoadingSpinner } from '../LoadingSpinner'
import { ProgressIndicator, LoadingDots } from './ProgressIndicator'

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`

const slideUp = keyframes`
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`

const Overlay = styled.div<{ $blur?: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: ${props => props.$blur ? 'blur(4px)' : 'none'};
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: ${fadeIn} 0.2s ease-out;
`

const LoadingCard = styled.div`
  background: ${props => props.theme?.card || '#ffffff'};
  border-radius: 12px;
  padding: 2rem;
  min-width: 300px;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  text-align: center;
  animation: ${slideUp} 0.3s ease-out;
`

const LoadingTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: ${props => props.theme?.textPrimary || '#1f2937'};
`

const LoadingMessage = styled.p`
  margin: 0 0 1.5rem 0;
  color: ${props => props.theme?.textSecondary || '#6b7280'};
  font-size: 0.9375rem;
  line-height: 1.5;
`

const LoadingContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
`

const SpinnerContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
`

const StepsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: left;
  width: 100%;
`

const Step = styled.div<{ $active?: boolean; $completed?: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  font-size: 0.875rem;
  color: ${props => {
    if (props.$completed) return props.theme?.success || '#10b981'
    if (props.$active) return props.theme?.accent || '#3b82f6'
    return props.theme?.textMuted || '#9ca3af'
  }};
  transition: all 0.2s ease;
`

const StepIcon = styled.div<{ $active?: boolean; $completed?: boolean }>`
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: ${props => {
    if (props.$completed) return props.theme?.success || '#10b981'
    if (props.$active) return props.theme?.accent || '#3b82f6'
    return props.theme?.backgroundTertiary || '#e5e7eb'
  }};
  color: ${props => {
    if (props.$completed || props.$active) return '#ffffff'
    return props.theme?.textMuted || '#9ca3af'
  }};
`

const CancelButton = styled.button`
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid ${props => props.theme?.border || '#e5e7eb'};
  border-radius: 6px;
  color: ${props => props.theme?.textSecondary || '#6b7280'};
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.theme?.backgroundTertiary || '#f3f4f6'};
    border-color: ${props => props.theme?.textMuted || '#9ca3af'};
  }
`

interface LoadingStep {
  id: string
  label: string
  completed?: boolean
}

interface LoadingOverlayProps {
  visible: boolean
  title?: string
  message?: string
  variant?: 'spinner' | 'progress' | 'steps'
  steps?: LoadingStep[]
  currentStep?: string
  onCancel?: () => void
  cancelLabel?: string
  blur?: boolean
  className?: string
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  title = 'Loading',
  message,
  variant = 'spinner',
  steps = [],
  currentStep,
  onCancel,
  cancelLabel = 'Cancel',
  blur = true,
  className
}) => {
  if (!visible) return null

  return (
    <Overlay $blur={blur} className={className}>
      <LoadingCard>
        <LoadingTitle>{title}</LoadingTitle>

        {message && <LoadingMessage>{message}</LoadingMessage>}

        <LoadingContent>
          {variant === 'spinner' && (
            <SpinnerContainer>
              <LoadingSpinner size="large" />
            </SpinnerContainer>
          )}

          {variant === 'progress' && (
            <ProgressIndicator
              message="Processing..."
              variant="default"
              size="medium"
            />
          )}

          {variant === 'steps' && steps.length > 0 && (
            <StepsContainer>
              {steps.map((step, index) => {
                const isActive = step.id === currentStep
                const isCompleted = step.completed

                return (
                  <Step key={step.id} $active={isActive} $completed={isCompleted}>
                    <StepIcon $active={isActive} $completed={isCompleted}>
                      {isCompleted ? '✓' : index + 1}
                    </StepIcon>
                    <span>{step.label}</span>
                    {isActive && !isCompleted && <LoadingDots size="small" />}
                  </Step>
                )
              })}
            </StepsContainer>
          )}

          {onCancel && (
            <CancelButton onClick={onCancel}>
              {cancelLabel}
            </CancelButton>
          )}
        </LoadingContent>
      </LoadingCard>
    </Overlay>
  )
}

export default LoadingOverlay