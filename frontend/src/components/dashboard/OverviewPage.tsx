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

const SummaryCardsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const SummaryCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
`

const CardIcon = styled.div`
  font-size: 1.5rem;
`

const CardLabel = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`

const CardValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
`

const CardChange = styled.div<{ $positive?: boolean }>`
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.$positive ? '#28a745' : '#dc3545'};
  display: flex;
  align-items: center;
  gap: 0.25rem;
`

const ChartSection = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
`

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
`

const PlaceholderChart = styled.div`
  background: linear-gradient(135deg, #f8f9fa 0%, #e5e7eb 100%);
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: 1rem;
  font-weight: 500;

  @media (max-width: 768px) {
    height: 200px;
    font-size: 0.875rem;
  }
`

const ActivitySection = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
`

const ActivityTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`

const TableHeader = styled.thead`
  border-bottom: 2px solid #e5e7eb;
`

const TableHeaderCell = styled.th`
  text-align: left;
  padding: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  @media (max-width: 768px) {
    padding: 0.5rem;
    font-size: 0.75rem;
  }
`

const TableBody = styled.tbody``

const TableRow = styled.tr`
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #f9fafb;
  }

  &:last-child {
    border-bottom: none;
  }
`

const TableCell = styled.td`
  padding: 0.875rem 0.75rem;
  font-size: 0.9375rem;
  color: #1f2937;

  @media (max-width: 768px) {
    padding: 0.625rem 0.5rem;
    font-size: 0.875rem;
  }
`

const StatusBadge = styled.span<{ $status: 'success' | 'error' | 'warning' }>`
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;

  ${props => {
    switch (props.$status) {
      case 'success':
        return `
          background: #d4edda;
          color: #155724;
        `
      case 'error':
        return `
          background: #f8d7da;
          color: #721c24;
        `
      case 'warning':
        return `
          background: #fff3cd;
          color: #856404;
        `
    }
  }}
`

const ServiceLabel = styled.span`
  font-weight: 500;
  color: #4a90e2;
`

// Mock data
const mockActivities = [
  { id: 1, time: '2 mins ago', service: 'Facebook', event: 'Post Published', status: 'success' as const },
  { id: 2, time: '15 mins ago', service: 'TikTok', event: 'Video Uploaded', status: 'success' as const },
  { id: 3, time: '1 hour ago', service: 'Facebook', event: 'OAuth Refresh', status: 'success' as const },
  { id: 4, time: '2 hours ago', service: 'TikTok', event: 'Auth Failed', status: 'error' as const },
  { id: 5, time: '3 hours ago', service: 'Facebook', event: 'Campaign Started', status: 'success' as const },
  { id: 6, time: '5 hours ago', service: 'TikTok', event: 'Rate Limit Warning', status: 'warning' as const },
  { id: 7, time: '6 hours ago', service: 'Facebook', event: 'Post Scheduled', status: 'success' as const },
  { id: 8, time: '8 hours ago', service: 'TikTok', event: 'Analytics Fetched', status: 'success' as const },
  { id: 9, time: '10 hours ago', service: 'Facebook', event: 'Token Refreshed', status: 'success' as const },
  { id: 10, time: '12 hours ago', service: 'TikTok', event: 'Video Published', status: 'success' as const },
]

const OverviewPage: React.FC = () => {
  return (
    <Container>
      <Title>Overview</Title>

      <SummaryCardsGrid>
        <SummaryCard>
          <CardHeader>
            <CardIcon>📊</CardIcon>
            <CardLabel>Total Requests</CardLabel>
          </CardHeader>
          <CardValue>1,234</CardValue>
          <CardChange $positive={true}>
            ↑ +12% from last week
          </CardChange>
        </SummaryCard>

        <SummaryCard>
          <CardHeader>
            <CardIcon>🔗</CardIcon>
            <CardLabel>Active Integrations</CardLabel>
          </CardHeader>
          <CardValue>2</CardValue>
          <CardChange $positive={true}>
            Facebook, TikTok
          </CardChange>
        </SummaryCard>

        <SummaryCard>
          <CardHeader>
            <CardIcon>✅</CardIcon>
            <CardLabel>Success Rate</CardLabel>
          </CardHeader>
          <CardValue>98.5%</CardValue>
          <CardChange $positive={true}>
            ↑ +1.2% from last week
          </CardChange>
        </SummaryCard>

        <SummaryCard>
          <CardHeader>
            <CardIcon>⚡</CardIcon>
            <CardLabel>Avg Response Time</CardLabel>
          </CardHeader>
          <CardValue>245ms</CardValue>
          <CardChange $positive={true}>
            ↓ -15ms from last week
          </CardChange>
        </SummaryCard>
      </SummaryCardsGrid>

      <ChartSection>
        <SectionTitle>Activity Over Time</SectionTitle>
        <PlaceholderChart>
          📈 Chart visualization will be added here (Chart.js or Recharts)
        </PlaceholderChart>
      </ChartSection>

      <ActivitySection>
        <SectionTitle>Recent Activity</SectionTitle>
        <ActivityTable>
          <TableHeader>
            <tr>
              <TableHeaderCell>Time</TableHeaderCell>
              <TableHeaderCell>Service</TableHeaderCell>
              <TableHeaderCell>Event</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {mockActivities.map(activity => (
              <TableRow key={activity.id}>
                <TableCell>{activity.time}</TableCell>
                <TableCell>
                  <ServiceLabel>{activity.service}</ServiceLabel>
                </TableCell>
                <TableCell>{activity.event}</TableCell>
                <TableCell>
                  <StatusBadge $status={activity.status}>
                    {activity.status}
                  </StatusBadge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </ActivityTable>
      </ActivitySection>
    </Container>
  )
}

export default OverviewPage
