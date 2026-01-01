import React from 'react'
import styled from 'styled-components'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2rem;
`

const IntegrationsPage: React.FC = () => {
  return (
    <Container>
      <Title>Integrations Page - Coming Soon</Title>
    </Container>
  )
}

export default IntegrationsPage
