import React from 'react'
import styled from 'styled-components'

const ErrorContainer = styled.div`
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  color: #721c24;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:before {
    content: "!";
    font-size: 1rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    background: #dc3545;
    color: white;
    border-radius: 50%;
  }
`

const ErrorText = styled.span`
  flex: 1;
  line-height: 1.4;
`

interface ErrorMessageProps {
  message: string
  className?: string
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  className
}) => {
  return (
    <ErrorContainer className={className}>
      <ErrorText>{message}</ErrorText>
    </ErrorContainer>
  )
}