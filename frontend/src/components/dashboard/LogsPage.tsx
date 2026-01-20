import React, { useState } from 'react'
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

const FilterToolbar = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
`

const FilterRow = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
`

const SearchBox = styled.div`
  flex: 1;
  min-width: 250px;
  position: relative;
`

const SearchIcon = styled.span`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;

  svg {
    width: 16px;
    height: 16px;
  }
`

const SearchInput = styled.input`
  width: 100%;
  padding: 0.625rem 1rem 0.625rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }

  &::placeholder {
    color: #9ca3af;
  }
`

const FilterSelect = styled.select`
  padding: 0.625rem 2.5rem 0.625rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M10.293 3.293L6 7.586 1.707 3.293A1 1 0 00.293 4.707l5 5a1 1 0 001.414 0l5-5a1 1 0 10-1.414-1.414z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const LogsTableSection = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
`

const TableWrapper = styled.div`
  overflow-x: auto;
`

const LogsTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
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
  white-space: nowrap;
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
  font-size: 0.875rem;
  color: #1f2937;
  vertical-align: top;
`

const Timestamp = styled.div`
  font-weight: 500;
  color: #6b7280;
  white-space: nowrap;
`

const ServiceLabel = styled.span`
  font-weight: 600;
  color: #4a90e2;
`

const EventType = styled.div`
  font-weight: 500;
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

const Message = styled.div`
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #6b7280;

  @media (max-width: 1024px) {
    max-width: 200px;
  }
`

const PaginationSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem 1.5rem;
`

const PageInfo = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`

const PaginationButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`

const PageButton = styled.button<{ $active?: boolean }>`
  padding: 0.5rem 0.875rem;
  border: 1px solid ${props => props.$active ? '#4a90e2' : '#e5e7eb'};
  border-radius: 6px;
  background: ${props => props.$active ? 'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)' : 'white'};
  color: ${props => props.$active ? 'white' : '#6b7280'};
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #4a90e2;
    ${props => !props.$active && `
      background: #f3f4f6;
    `}
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

// Mock log data
const mockLogs = [
  { id: 1, timestamp: '2024-01-15 14:32:15', service: 'Facebook', eventType: 'Post Published', status: 'success' as const, message: 'Successfully published post to timeline' },
  { id: 2, timestamp: '2024-01-15 14:28:42', service: 'TikTok', eventType: 'Video Upload', status: 'success' as const, message: 'Video uploaded successfully, processing started' },
  { id: 3, timestamp: '2024-01-15 14:15:30', service: 'Facebook', eventType: 'OAuth Refresh', status: 'success' as const, message: 'Access token refreshed successfully' },
  { id: 4, timestamp: '2024-01-15 13:58:21', service: 'TikTok', eventType: 'Authentication', status: 'error' as const, message: 'Failed to authenticate: Invalid credentials' },
  { id: 5, timestamp: '2024-01-15 13:45:18', service: 'Facebook', eventType: 'Campaign Update', status: 'success' as const, message: 'Campaign settings updated successfully' },
  { id: 6, timestamp: '2024-01-15 13:30:55', service: 'TikTok', eventType: 'Rate Limit', status: 'warning' as const, message: 'Approaching rate limit: 80% capacity' },
  { id: 7, timestamp: '2024-01-15 13:12:44', service: 'Facebook', eventType: 'Post Scheduled', status: 'success' as const, message: 'Post scheduled for 2024-01-16 10:00 AM' },
  { id: 8, timestamp: '2024-01-15 12:58:33', service: 'TikTok', eventType: 'Analytics Fetch', status: 'success' as const, message: 'Successfully fetched video analytics' },
  { id: 9, timestamp: '2024-01-15 12:42:20', service: 'Facebook', eventType: 'Token Refresh', status: 'success' as const, message: 'Page access token refreshed' },
  { id: 10, timestamp: '2024-01-15 12:25:15', service: 'TikTok', eventType: 'Video Published', status: 'success' as const, message: 'Video published successfully to feed' },
  { id: 11, timestamp: '2024-01-15 12:08:40', service: 'Facebook', eventType: 'Ad Campaign', status: 'success' as const, message: 'New ad campaign created and activated' },
  { id: 12, timestamp: '2024-01-15 11:55:28', service: 'TikTok', eventType: 'Upload Failed', status: 'error' as const, message: 'Video upload failed: File size exceeds limit' },
  { id: 13, timestamp: '2024-01-15 11:38:12', service: 'Facebook', eventType: 'Comment Reply', status: 'success' as const, message: 'Successfully replied to 5 comments' },
  { id: 14, timestamp: '2024-01-15 11:20:55', service: 'TikTok', eventType: 'Profile Update', status: 'success' as const, message: 'Profile information updated successfully' },
  { id: 15, timestamp: '2024-01-15 11:02:30', service: 'Facebook', eventType: 'Page Insights', status: 'success' as const, message: 'Page insights data retrieved' },
  { id: 16, timestamp: '2024-01-15 10:45:18', service: 'TikTok', eventType: 'API Error', status: 'error' as const, message: 'API request failed: Server timeout' },
  { id: 17, timestamp: '2024-01-15 10:28:44', service: 'Facebook', eventType: 'Media Upload', status: 'success' as const, message: 'Media files uploaded to library' },
  { id: 18, timestamp: '2024-01-15 10:12:33', service: 'TikTok', eventType: 'Hashtag Check', status: 'warning' as const, message: 'Some hashtags may be restricted' },
  { id: 19, timestamp: '2024-01-15 09:58:20', service: 'Facebook', eventType: 'Audience Sync', status: 'success' as const, message: 'Custom audience synced successfully' },
  { id: 20, timestamp: '2024-01-15 09:42:15', service: 'TikTok', eventType: 'Content Check', status: 'warning' as const, message: 'Content flagged for manual review' },
  { id: 21, timestamp: '2024-01-15 09:25:10', service: 'Facebook', eventType: 'Post Deleted', status: 'success' as const, message: 'Post deleted successfully' },
  { id: 22, timestamp: '2024-01-15 09:08:44', service: 'TikTok', eventType: 'Video Processing', status: 'success' as const, message: 'Video processing completed' },
  { id: 23, timestamp: '2024-01-15 08:52:30', service: 'Facebook', eventType: 'API Request', status: 'success' as const, message: 'API request completed successfully' },
  { id: 24, timestamp: '2024-01-15 08:35:18', service: 'TikTok', eventType: 'Token Expired', status: 'error' as const, message: 'Access token expired, re-authentication required' },
  { id: 25, timestamp: '2024-01-15 08:18:55', service: 'Facebook', eventType: 'Event Created', status: 'success' as const, message: 'New event created on page' },
]

const LogsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedService, setSelectedService] = useState('all')
  const [selectedSeverity, setSelectedSeverity] = useState('all')

  return (
    <Container>
      <Title>Activity Logs</Title>

      <FilterToolbar>
        <FilterRow>
          <SearchBox>
            <SearchIcon>
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </SearchIcon>
            <SearchInput
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </SearchBox>

          <FilterSelect value={selectedService} onChange={(e) => setSelectedService(e.target.value)}>
            <option value="all">All Services</option>
            <option value="facebook">Facebook</option>
            <option value="tiktok">TikTok</option>
          </FilterSelect>

          <FilterSelect value={selectedSeverity} onChange={(e) => setSelectedSeverity(e.target.value)}>
            <option value="all">All Statuses</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </FilterSelect>
        </FilterRow>
      </FilterToolbar>

      <LogsTableSection>
        <TableWrapper>
          <LogsTable>
            <TableHeader>
              <tr>
                <TableHeaderCell>Timestamp</TableHeaderCell>
                <TableHeaderCell>Service</TableHeaderCell>
                <TableHeaderCell>Event Type</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Message</TableHeaderCell>
              </tr>
            </TableHeader>
            <TableBody>
              {mockLogs.map(log => (
                <TableRow key={log.id}>
                  <TableCell>
                    <Timestamp>{log.timestamp}</Timestamp>
                  </TableCell>
                  <TableCell>
                    <ServiceLabel>{log.service}</ServiceLabel>
                  </TableCell>
                  <TableCell>
                    <EventType>{log.eventType}</EventType>
                  </TableCell>
                  <TableCell>
                    <StatusBadge $status={log.status}>
                      {log.status}
                    </StatusBadge>
                  </TableCell>
                  <TableCell>
                    <Message title={log.message}>{log.message}</Message>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </LogsTable>
        </TableWrapper>
      </LogsTableSection>

      <PaginationSection>
        <PageInfo>Showing 1-25 of 250 logs</PageInfo>
        <PaginationButtons>
          <PageButton disabled>Previous</PageButton>
          <PageButton $active>1</PageButton>
          <PageButton>2</PageButton>
          <PageButton>3</PageButton>
          <PageButton>...</PageButton>
          <PageButton>10</PageButton>
          <PageButton>Next</PageButton>
        </PaginationButtons>
      </PaginationSection>
    </Container>
  )
}

export default LogsPage
