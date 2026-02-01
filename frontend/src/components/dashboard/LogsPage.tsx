import React, { useState } from 'react'
import styled from 'styled-components'
import { useTranslation } from 'react-i18next'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  background: linear-gradient(135deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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

const EmptyState = styled.div`
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
`

const EmptyIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
`

const EmptyTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
`

const EmptyDescription = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
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

// Empty logs - will be populated when activity log API is implemented
const logs: Array<{
  id: number
  timestamp: string
  service: string
  eventType: string
  status: 'success' | 'error' | 'warning'
  message: string
}> = []

const LogsPage: React.FC = () => {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedService, setSelectedService] = useState('all')
  const [selectedSeverity, setSelectedSeverity] = useState('all')

  return (
    <Container>
      <Title>{t('logs.title')}</Title>

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
              placeholder={t('logs.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </SearchBox>

          <FilterSelect value={selectedService} onChange={(e) => setSelectedService(e.target.value)}>
            <option value="all">{t('logs.allServices')}</option>
            <option value="facebook">{t('logs.facebook')}</option>
            <option value="tiktok">{t('logs.tiktok')}</option>
          </FilterSelect>

          <FilterSelect value={selectedSeverity} onChange={(e) => setSelectedSeverity(e.target.value)}>
            <option value="all">{t('logs.allStatuses')}</option>
            <option value="success">{t('logs.success')}</option>
            <option value="warning">{t('logs.warning')}</option>
            <option value="error">{t('logs.error')}</option>
          </FilterSelect>
        </FilterRow>
      </FilterToolbar>

      <LogsTableSection>
        {logs.length === 0 ? (
          <EmptyState>
            <EmptyIcon>📋</EmptyIcon>
            <EmptyTitle>{t('logs.noLogs', 'No Activity Logs')}</EmptyTitle>
            <EmptyDescription>
              {t('logs.noLogsDescription', 'Activity logs will appear here when you start using Facebook and TikTok integrations.')}
            </EmptyDescription>
          </EmptyState>
        ) : (
          <TableWrapper>
            <LogsTable>
              <TableHeader>
                <tr>
                  <TableHeaderCell>{t('logs.timestamp')}</TableHeaderCell>
                  <TableHeaderCell>{t('logs.service')}</TableHeaderCell>
                  <TableHeaderCell>{t('logs.eventType')}</TableHeaderCell>
                  <TableHeaderCell>{t('logs.status')}</TableHeaderCell>
                  <TableHeaderCell>{t('logs.message')}</TableHeaderCell>
                </tr>
              </TableHeader>
              <TableBody>
                {logs.map(log => (
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
        )}
      </LogsTableSection>

      {logs.length > 0 && (
        <PaginationSection>
          <PageInfo>{t('logs.showing', { start: 1, end: logs.length, total: logs.length })}</PageInfo>
          <PaginationButtons>
            <PageButton disabled>{t('logs.previous')}</PageButton>
            <PageButton $active>1</PageButton>
            <PageButton>{t('logs.next')}</PageButton>
          </PaginationButtons>
        </PaginationSection>
      )}
    </Container>
  )
}

export default LogsPage
