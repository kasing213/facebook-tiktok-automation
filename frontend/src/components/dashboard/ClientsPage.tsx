import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'
import { useTelegram } from '../../hooks/useTelegram'
import { invoiceService } from '../../services/invoiceApi'
import { RegisteredClient, ClientLinkCodeResponse } from '../../types/invoice'
import QRCodeModal from './clients/QRCodeModal'

// Styled Components
const Container = styled.div`
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;

  @media (max-width: 768px) {
    padding: 1rem;
  }
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 1rem;
  }
`

const TitleSection = styled.div``

const Title = styled.h1`
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
`

const Subtitle = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

const AddButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: #059669;
  }
`

// Telegram Warning Banner
const WarningBanner = styled.div`
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
`

const WarningHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
`

const WarningIcon = styled.span`
  font-size: 1.5rem;
`

const WarningTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #92400e;
  margin: 0;
`

const WarningDescription = styled.p`
  font-size: 0.875rem;
  color: #92400e;
  margin: 0 0 0.75rem 0;
`

const WarningList = styled.ul`
  margin: 0 0 1rem 0;
  padding-left: 1.5rem;
`

const WarningListItem = styled.li`
  font-size: 0.875rem;
  color: #92400e;
  margin-bottom: 0.25rem;
`

const ConnectButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: #d97706;
  }
`

// Stats Cards
const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.25rem;
`

const StatHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
`

const StatLabel = styled.span`
  font-size: 0.875rem;
  color: #6b7280;
`

const StatBadge = styled.span`
  font-size: 0.75rem;
  color: #10b981;
  background: #d1fae5;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
`

const StatValue = styled.p`
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

// Instructions Card
const InstructionsCard = styled.div`
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
`

const InstructionsIcon = styled.div`
  width: 48px;
  height: 48px;
  background: #3b82f6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`

const InstructionsContent = styled.div`
  flex: 1;
`

const InstructionsTitle = styled.h3`
  font-size: 0.9375rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
`

const InstructionsText = styled.p`
  font-size: 0.875rem;
  color: #4b5563;
  margin: 0;
`

// Table Container
const TableContainer = styled.div`
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
`

const TableHeader = styled.div`
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  border-bottom: 1px solid #e5e7eb;
`

const SearchInput = styled.input`
  flex: 1;
  min-width: 200px;
  max-width: 400px;
  padding: 0.5rem 1rem 0.5rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  }
`

const SearchWrapper = styled.div`
  position: relative;
  flex: 1;
  max-width: 400px;
`

const SearchIcon = styled.svg`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
`

const FilterButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`

const FilterButton = styled.button<{ isActive: boolean }>`
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${props => props.isActive ? '#d1fae5' : 'transparent'};
  color: ${props => props.isActive ? '#059669' : '#6b7280'};

  &:hover {
    background: ${props => props.isActive ? '#d1fae5' : '#f3f4f6'};
  }
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`

const Th = styled.th`
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
`

const Td = styled.td`
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
`

const ClientInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

const ClientAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #d1fae5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #059669;
  font-weight: 600;
`

const ClientName = styled.p`
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  margin: 0;
`

const ClientDate = styled.p`
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
`

const TelegramStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const StatusDot = styled.span<{ status: 'linked' | 'not_linked' }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => props.status === 'linked' ? '#10b981' : '#f59e0b'};
`

const TelegramUsername = styled.span`
  font-size: 0.875rem;
  color: #1f2937;
`

const NotLinkedText = styled.span`
  font-size: 0.875rem;
  color: #9ca3af;
`

const Amount = styled.span<{ type?: 'pending' | 'paid' }>`
  font-size: 0.875rem;
  font-weight: ${props => props.type === 'pending' ? '500' : '400'};
  color: ${props => props.type === 'pending' ? '#f59e0b' : props.type === 'paid' ? '#10b981' : '#1f2937'};
`

const ActionButtons = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
`

const ActionButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 0.375rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${props => props.variant === 'primary' ? '#eff6ff' : 'transparent'};
  color: ${props => props.variant === 'primary' ? '#3b82f6' : '#10b981'};

  &:hover {
    background: ${props => props.variant === 'primary' ? '#dbeafe' : '#d1fae5'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 1rem;
`

const EmptyIcon = styled.div`
  width: 64px;
  height: 64px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
`

const EmptyText = styled.p`
  color: #6b7280;
  margin: 0;
`

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  padding: 3rem;
`

const Spinner = styled.div`
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

// Main Component
const ClientsPage: React.FC = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { status: telegramStatus, loading: telegramLoading } = useTelegram()

  const [clients, setClients] = useState<RegisteredClient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'linked' | 'not_linked'>('all')

  // QR Modal state
  const [qrModalOpen, setQrModalOpen] = useState(false)
  const [selectedClient, setSelectedClient] = useState<RegisteredClient | null>(null)
  const [linkCode, setLinkCode] = useState<ClientLinkCodeResponse | null>(null)
  const [generatingCode, setGeneratingCode] = useState(false)

  // Fetch clients
  const fetchClients = useCallback(async () => {
    try {
      setLoading(true)
      const response = await invoiceService.listRegisteredClients()
      setClients(response.clients || [])
    } catch (err: any) {
      setError(err.message || 'Failed to fetch clients')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchClients()
  }, [fetchClients])

  // Calculate stats
  const stats = {
    totalClients: clients.length,
    linkedClients: clients.filter(c => c.telegram_linked).length,
    totalReceivable: clients.reduce((sum, c) => {
      return sum + (c.pending_invoices?.reduce((invSum, inv) => invSum + (inv.amount || 0), 0) || 0)
    }, 0)
  }

  const linkedPercentage = stats.totalClients > 0
    ? Math.round((stats.linkedClients / stats.totalClients) * 100)
    : 0

  // Filter clients
  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (client.telegram_username && client.telegram_username.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (client.email && client.email.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesFilter = filterStatus === 'all' ||
      (filterStatus === 'linked' && client.telegram_linked) ||
      (filterStatus === 'not_linked' && !client.telegram_linked)

    return matchesSearch && matchesFilter
  })

  // Format currency
  const formatKHR = (amount: number) => {
    return new Intl.NumberFormat('en-US').format(amount) + ' ៛'
  }

  // Handle QR generation
  const handleGenerateQR = async (client: RegisteredClient) => {
    setSelectedClient(client)
    setQrModalOpen(true)
    setLinkCode(null)

    if (client.telegram_linked) return // Already linked, just show info

    try {
      setGeneratingCode(true)
      const response = await invoiceService.generateClientLinkCode(client.id)
      setLinkCode(response)
    } catch (err: any) {
      setError(err.message || 'Failed to generate QR code')
    } finally {
      setGeneratingCode(false)
    }
  }

  const handleCloseQRModal = () => {
    setQrModalOpen(false)
    setSelectedClient(null)
    setLinkCode(null)
  }

  const handleRegenerateCode = async () => {
    if (!selectedClient) return

    try {
      setGeneratingCode(true)
      const response = await invoiceService.generateClientLinkCode(selectedClient.id)
      setLinkCode(response)
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate QR code')
    } finally {
      setGeneratingCode(false)
    }
  }

  // Check if Telegram is connected
  const isTelegramConnected = telegramStatus?.connected

  return (
    <Container>
      <Header>
        <TitleSection>
          <Title>{t('clients.title')}</Title>
          <Subtitle>{t('clients.subtitle')}</Subtitle>
        </TitleSection>
        <AddButton disabled={!isTelegramConnected}>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {t('clients.addClient')}
        </AddButton>
      </Header>

      {/* Telegram Warning Banner */}
      {!telegramLoading && !isTelegramConnected && (
        <WarningBanner>
          <WarningHeader>
            <WarningIcon>⚠️</WarningIcon>
            <WarningTitle>{t('clients.telegramWarning.title')}</WarningTitle>
          </WarningHeader>
          <WarningDescription>{t('clients.telegramWarning.description')}</WarningDescription>
          <WarningList>
            <WarningListItem>{t('clients.telegramWarning.bullet1')}</WarningListItem>
            <WarningListItem>{t('clients.telegramWarning.bullet2')}</WarningListItem>
            <WarningListItem>{t('clients.telegramWarning.bullet3')}</WarningListItem>
          </WarningList>
          <ConnectButton onClick={() => navigate('/dashboard/integrations/telegram')}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
            </svg>
            {t('clients.telegramWarning.connectButton')} →
          </ConnectButton>
        </WarningBanner>
      )}

      {/* Stats Cards */}
      <StatsGrid>
        <StatCard>
          <StatHeader>
            <StatLabel>{t('clients.totalClients')}</StatLabel>
          </StatHeader>
          <StatValue>{stats.totalClients}</StatValue>
        </StatCard>
        <StatCard>
          <StatHeader>
            <StatLabel>{t('clients.telegramLinked')}</StatLabel>
            <StatBadge>{linkedPercentage}%</StatBadge>
          </StatHeader>
          <StatValue>{stats.linkedClients}</StatValue>
        </StatCard>
        <StatCard>
          <StatHeader>
            <StatLabel>{t('clients.totalReceivable')}</StatLabel>
          </StatHeader>
          <StatValue>{formatKHR(stats.totalReceivable)}</StatValue>
        </StatCard>
      </StatsGrid>

      {/* Instructions Card */}
      {isTelegramConnected && (
        <InstructionsCard>
          <InstructionsIcon>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
            </svg>
          </InstructionsIcon>
          <InstructionsContent>
            <InstructionsTitle>{t('clients.linkInstructions.title')}</InstructionsTitle>
            <InstructionsText>{t('clients.linkInstructions.description')}</InstructionsText>
          </InstructionsContent>
        </InstructionsCard>
      )}

      {/* Client Table */}
      <TableContainer>
        <TableHeader>
          <SearchWrapper>
            <SearchIcon fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </SearchIcon>
            <SearchInput
              type="text"
              placeholder={t('clients.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </SearchWrapper>

          <FilterButtons>
            <FilterButton
              isActive={filterStatus === 'all'}
              onClick={() => setFilterStatus('all')}
            >
              {t('common.all')}
            </FilterButton>
            <FilterButton
              isActive={filterStatus === 'linked'}
              onClick={() => setFilterStatus('linked')}
            >
              {t('clients.linked')}
            </FilterButton>
            <FilterButton
              isActive={filterStatus === 'not_linked'}
              onClick={() => setFilterStatus('not_linked')}
            >
              {t('clients.notLinked')}
            </FilterButton>
          </FilterButtons>
        </TableHeader>

        {loading ? (
          <LoadingSpinner>
            <Spinner />
          </LoadingSpinner>
        ) : filteredClients.length === 0 ? (
          <EmptyState>
            <EmptyIcon>
              <svg width="32" height="32" fill="none" stroke="#9ca3af" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </EmptyIcon>
            <EmptyText>{t('clients.noClients')}</EmptyText>
          </EmptyState>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Client</Th>
                <Th>{t('clients.telegramColumn')}</Th>
                <Th>{t('clients.invoicesColumn')}</Th>
                <Th>{t('clients.totalPaid')}</Th>
                <Th>{t('clients.pendingAmount')}</Th>
                <Th style={{ textAlign: 'right' }}>{t('common.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {filteredClients.map((client) => {
                const pendingAmount = client.pending_invoices?.reduce((sum, inv) => sum + (inv.amount || 0), 0) || 0
                const totalInvoices = client.pending_invoices?.length || 0

                return (
                  <tr key={client.id}>
                    <Td>
                      <ClientInfo>
                        <ClientAvatar>{client.name.charAt(0).toUpperCase()}</ClientAvatar>
                        <div>
                          <ClientName>{client.name}</ClientName>
                          {client.telegram_linked_at && (
                            <ClientDate>Linked {new Date(client.telegram_linked_at).toLocaleDateString()}</ClientDate>
                          )}
                        </div>
                      </ClientInfo>
                    </Td>
                    <Td>
                      <TelegramStatus>
                        <StatusDot status={client.telegram_linked ? 'linked' : 'not_linked'} />
                        {client.telegram_linked ? (
                          <TelegramUsername>@{client.telegram_username}</TelegramUsername>
                        ) : (
                          <NotLinkedText>{t('clients.notLinked')}</NotLinkedText>
                        )}
                      </TelegramStatus>
                    </Td>
                    <Td>{totalInvoices}</Td>
                    <Td><Amount>-</Amount></Td>
                    <Td>
                      {pendingAmount > 0 ? (
                        <Amount type="pending">{formatKHR(pendingAmount)}</Amount>
                      ) : (
                        <Amount type="paid">{t('clients.paid')}</Amount>
                      )}
                    </Td>
                    <Td>
                      <ActionButtons>
                        {!client.telegram_linked && (
                          <ActionButton
                            variant="primary"
                            onClick={() => handleGenerateQR(client)}
                            disabled={!isTelegramConnected}
                          >
                            {t('clients.generateQR')}
                          </ActionButton>
                        )}
                        <ActionButton
                          onClick={() => navigate(`/dashboard/invoices/new?client_id=${client.id}`)}
                          disabled={!isTelegramConnected}
                        >
                          {t('clients.newInvoice')}
                        </ActionButton>
                      </ActionButtons>
                    </Td>
                  </tr>
                )
              })}
            </tbody>
          </Table>
        )}
      </TableContainer>

      {/* QR Code Modal */}
      <QRCodeModal
        isOpen={qrModalOpen}
        onClose={handleCloseQRModal}
        client={selectedClient}
        linkCode={linkCode}
        onRegenerate={handleRegenerateCode}
        isGenerating={generatingCode}
      />

      {/* Error Toast */}
      {error && (
        <div style={{
          position: 'fixed',
          bottom: '1rem',
          right: '1rem',
          background: '#ef4444',
          color: 'white',
          padding: '1rem',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}>
          {error}
          <button
            onClick={() => setError(null)}
            style={{ marginLeft: '1rem', background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>
      )}
    </Container>
  )
}

export default ClientsPage
