import React, { useState, useEffect, useRef } from 'react'
import styled from 'styled-components'
import { Customer } from '../../types/invoice'

interface CustomerSelectProps {
  customers: Customer[]
  selectedId?: string
  onSelect: (customer: Customer | null) => void
  onCreateNew?: () => void
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

const CustomerList = styled.div`
  max-height: 200px;
  overflow-y: auto;
`

const CustomerOption = styled.div<{ $selected?: boolean }>`
  padding: 0.75rem 1rem;
  cursor: pointer;
  background: ${props => props.$selected ? '#f3f4f6' : 'white'};
  border-left: 3px solid ${props => props.$selected ? '#4a90e2' : 'transparent'};

  &:hover {
    background: #f9fafb;
  }
`

const CustomerName = styled.div`
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
`

const CustomerDetails = styled.div`
  font-size: 0.75rem;
  color: #6b7280;
`

const CreateNewButton = styled.button`
  width: 100%;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border: none;
  border-top: 1px solid #e5e7eb;
  color: #4a90e2;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    background: #f3f4f6;
  }
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

export const CustomerSelect: React.FC<CustomerSelectProps> = ({
  customers,
  selectedId,
  onSelect,
  onCreateNew,
  loading = false,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedCustomer = customers.find(c => c.id === selectedId)

  const filteredCustomers = customers.filter(customer => {
    const searchLower = search.toLowerCase()
    return (
      customer.name.toLowerCase().includes(searchLower) ||
      customer.email?.toLowerCase().includes(searchLower) ||
      customer.company?.toLowerCase().includes(searchLower)
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

  const handleSelect = (customer: Customer) => {
    onSelect(customer)
    setIsOpen(false)
    setSearch('')
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onSelect(null)
  }

  return (
    <Container ref={containerRef}>
      <Label>Customer *</Label>
      <SelectButton
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        $disabled={disabled}
      >
        <span>
          {loading ? 'Loading...' : selectedCustomer?.name || 'Select a customer...'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {selectedCustomer && !disabled && (
            <ClearButton onClick={handleClear}>Clear</ClearButton>
          )}
          <span>{isOpen ? '▲' : '▼'}</span>
        </div>
      </SelectButton>

      {isOpen && !disabled && (
        <Dropdown>
          <SearchInput
            type="text"
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
          <CustomerList>
            {filteredCustomers.length === 0 ? (
              <NoResults>No customers found</NoResults>
            ) : (
              filteredCustomers.map(customer => (
                <CustomerOption
                  key={customer.id}
                  $selected={customer.id === selectedId}
                  onClick={() => handleSelect(customer)}
                >
                  <CustomerName>{customer.name}</CustomerName>
                  <CustomerDetails>
                    {[customer.email, customer.company].filter(Boolean).join(' • ')}
                  </CustomerDetails>
                </CustomerOption>
              ))
            )}
          </CustomerList>
          {onCreateNew && (
            <CreateNewButton onClick={onCreateNew}>
              + Create New Customer
            </CreateNewButton>
          )}
        </Dropdown>
      )}
    </Container>
  )
}

export default CustomerSelect
