import React, { useState, useEffect, useRef } from 'react'
import styled from 'styled-components'
import { RegisteredClient } from '../../types/invoice'

interface RegisteredClientSelectProps {
  clients: RegisteredClient[]
  selectedId?: string
  onSelect: (client: RegisteredClient | null) => void
  loading?: boolean
  disabled?: boolean
}

const Container = styled.div`
  position: relative;
`

const Label = styled.label`
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
`

const SelectButton = styled.button<{ $disabled?: boolean }>`
  width: 100%;
  padding: 0.75rem 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  text-align: left;
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  display: flex;
  justify-content: space-between;
  align-items: center;
  opacity: ${props => props.$disabled ? 0.6 : 1};

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const Dropdown = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.25rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
`

const SearchInput = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
  }

  &::placeholder {
    color: #9ca3af;
  }
`

const ClientList = styled.div`
  max-height: 200px;
  overflow-y: auto;
`

const ClientOption = styled.div<{ $selected?: boolean }>`
  padding: 0.75rem 1rem;
  cursor: pointer;
  background: ${props => props.$selected ? '#f3f4f6' : 'white'};
  border-left: 3px solid ${props => props.$selected ? '#4a90e2' : 'transparent'};

  &:hover {
    background: #f9fafb;
  }
`

const ClientName = styled.div`
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const ClientDetails = styled.div`
  font-size: 0.75rem;
  color: #6b7280;
`

const TelegramBadge = styled.span<{ $linked?: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: ${props => props.$linked ? '#e8f5e9' : '#fff3e0'};
  color: ${props => props.$linked ? '#2e7d32' : '#e65100'};
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.6875rem;
  font-weight: 500;
`

const NoResults = styled.div`
  padding: 1rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
`

const ClearButton = styled.button`
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  border: none;
  border-radius: 4px;
  color: #6b7280;
  font-size: 0.75rem;
  cursor: pointer;

  &:hover {
    background: #e5e7eb;
  }
`

const EmptyState = styled.div`
  padding: 1.5rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;

  p {
    margin: 0 0 0.5rem 0;
  }

  small {
    display: block;
    color: #9ca3af;
    font-size: 0.75rem;
  }
`

export const RegisteredClientSelect: React.FC<RegisteredClientSelectProps> = ({
  clients,
  selectedId,
  onSelect,
  loading = false,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedClient = clients.find(c => c.id === selectedId)

  const filteredClients = clients.filter(client => {
    const searchLower = search.toLowerCase()
    return (
      client.name.toLowerCase().includes(searchLower) ||
      client.telegram_username?.toLowerCase().includes(searchLower) ||
      client.email?.toLowerCase().includes(searchLower)
    )
  })

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (client: RegisteredClient) => {
    onSelect(client)
    setIsOpen(false)
    setSearch('')
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onSelect(null)
  }

  return (
    <Container ref={containerRef}>
      <Label>
        Registered Client *
        <span style={{ color: '#6b7280', fontWeight: 400, marginLeft: '0.5rem', fontSize: '0.75rem' }}>
          (from Telegram bot)
        </span>
      </Label>
      <SelectButton
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        $disabled={disabled}
      >
        <span>
          {loading ? 'Loading...' : selectedClient ? (
            <>
              {selectedClient.name}
              {selectedClient.telegram_linked && (
                <TelegramBadge $linked style={{ marginLeft: '0.5rem' }}>
                  Telegram
                </TelegramBadge>
              )}
            </>
          ) : 'Select a registered client...'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {selectedClient && !disabled && (
            <ClearButton onClick={handleClear}>Clear</ClearButton>
          )}
          <span>{isOpen ? '^' : 'v'}</span>
        </div>
      </SelectButton>

      {isOpen && !disabled && (
        <Dropdown>
          <SearchInput
            type="text"
            placeholder="Search clients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
          <ClientList>
            {clients.length === 0 ? (
              <EmptyState>
                <p>No registered clients yet</p>
                <small>Use /register_client in Telegram bot to add clients</small>
              </EmptyState>
            ) : filteredClients.length === 0 ? (
              <NoResults>No clients found matching "{search}"</NoResults>
            ) : (
              filteredClients.map(client => (
                <ClientOption
                  key={client.id}
                  $selected={client.id === selectedId}
                  onClick={() => handleSelect(client)}
                >
                  <ClientName>
                    {client.name}
                    <TelegramBadge $linked={client.telegram_linked}>
                      {client.telegram_linked ? 'Linked' : 'Pending'}
                    </TelegramBadge>
                  </ClientName>
                  <ClientDetails>
                    {client.telegram_username && `@${client.telegram_username}`}
                    {client.telegram_username && client.email && ' | '}
                    {client.email}
                  </ClientDetails>
                </ClientOption>
              ))
            )}
          </ClientList>
        </Dropdown>
      )}
    </Container>
  )
}

export default RegisteredClientSelect
