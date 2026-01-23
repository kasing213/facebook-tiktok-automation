import React, { useState } from 'react'
import styled from 'styled-components'
import { useTranslation } from 'react-i18next'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  background: linear-gradient(135deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`

const DateSelector = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.625rem 1rem;
`

const DateLabel = styled.span`
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
`

const DateInput = styled.input`
  border: none;
  background: transparent;
  font-size: 0.9375rem;
  color: #1f2937;
  font-weight: 500;
  cursor: pointer;

  &:focus {
    outline: none;
  }
`

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const MetricCard = styled.div`
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

const MetricHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
`

const MetricIcon = styled.div`
  font-size: 0.625rem;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  padding: 0.375rem 0.5rem;
  border-radius: 6px;
  min-width: 2rem;
  text-align: center;
`

const MetricLabel = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
`

const MetricSubtext = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
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

const TableSection = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
`

const UsageTable = styled.table`
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

const ServiceLabel = styled.span`
  font-weight: 600;
  color: #4a90e2;
`

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.25rem;
`

const ProgressFill = styled.div<{ $percentage: number }>`
  height: 100%;
  width: ${props => props.$percentage}%;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
`

// Mock data
const mockUsageData = [
  { service: 'Facebook', requests: 8542, dataProcessed: '12.5 GB', percentage: 68 },
  { service: 'TikTok', requests: 3987, dataProcessed: '5.8 GB', percentage: 32 },
]

const UsagePage: React.FC = () => {
  const { t } = useTranslation()
  const [dateRange] = useState({ start: '2024-01-01', end: '2024-01-31' })

  return (
    <Container>
      <Header>
        <Title>{t('usage.title')}</Title>
        <DateSelector>
          <DateLabel>{t('usage.period')}</DateLabel>
          <DateInput type="text" value={`${dateRange.start} - ${dateRange.end}`} readOnly />
        </DateSelector>
      </Header>

      <MetricsGrid>
        <MetricCard>
          <MetricHeader>
            <MetricIcon>API</MetricIcon>
            <MetricLabel>{t('usage.totalApiCalls')}</MetricLabel>
          </MetricHeader>
          <MetricValue>12,529</MetricValue>
          <MetricSubtext>{t('usage.thisMonth')}</MetricSubtext>
        </MetricCard>

        <MetricCard>
          <MetricHeader>
            <MetricIcon>DATA</MetricIcon>
            <MetricLabel>{t('usage.dataProcessed')}</MetricLabel>
          </MetricHeader>
          <MetricValue>18.3 GB</MetricValue>
          <MetricSubtext>{t('usage.thisMonth')}</MetricSubtext>
        </MetricCard>

        <MetricCard>
          <MetricHeader>
            <MetricIcon>TIME</MetricIcon>
            <MetricLabel>{t('usage.avgResponseTime')}</MetricLabel>
          </MetricHeader>
          <MetricValue>245ms</MetricValue>
          <MetricSubtext>{t('usage.last30Days')}</MetricSubtext>
        </MetricCard>

        <MetricCard>
          <MetricHeader>
            <MetricIcon>RATE</MetricIcon>
            <MetricLabel>{t('usage.successRate')}</MetricLabel>
          </MetricHeader>
          <MetricValue>98.5%</MetricValue>
          <MetricSubtext>{t('usage.last30Days')}</MetricSubtext>
        </MetricCard>
      </MetricsGrid>

      <ChartSection>
        <SectionTitle>{t('usage.usageComparison')}</SectionTitle>
        <PlaceholderChart>
          {t('usage.chartPlaceholder')}
        </PlaceholderChart>
      </ChartSection>

      <TableSection>
        <SectionTitle>{t('usage.usageBreakdown')}</SectionTitle>
        <UsageTable>
          <TableHeader>
            <tr>
              <TableHeaderCell>{t('usage.service')}</TableHeaderCell>
              <TableHeaderCell>{t('usage.requests')}</TableHeaderCell>
              <TableHeaderCell>{t('usage.dataProcessed')}</TableHeaderCell>
              <TableHeaderCell>{t('usage.usagePercent')}</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {mockUsageData.map((usage, index) => (
              <TableRow key={index}>
                <TableCell>
                  <ServiceLabel>{usage.service}</ServiceLabel>
                </TableCell>
                <TableCell>{usage.requests.toLocaleString()}</TableCell>
                <TableCell>{usage.dataProcessed}</TableCell>
                <TableCell>
                  <div>
                    <strong>{usage.percentage}%</strong>
                    <ProgressBar>
                      <ProgressFill $percentage={usage.percentage} />
                    </ProgressBar>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </UsageTable>
      </TableSection>
    </Container>
  )
}

export default UsagePage
