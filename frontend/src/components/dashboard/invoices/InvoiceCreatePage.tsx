import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useInvoices } from '../../../hooks/useInvoices'
import { InvoiceForm } from '../../invoice'
import { InvoiceCreate, InvoiceUpdate, CustomerCreate } from '../../../types/invoice'

const Container = styled.div`
  max-width: 900px;
  margin: 0 auto;
`

const Header = styled.div`
  margin-bottom: 2rem;
`

const BackLink = styled.button`
  background: none;
  border: none;
  color: #4a90e2;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    text-decoration: underline;
  }
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

const ErrorMessage = styled.div`
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
`

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`

const ModalContent = styled.div`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
`

const ModalTitle = styled.h3`
  margin: 0 0 1.5rem 0;
  color: #1f2937;
  font-size: 1.25rem;
`

const FormGroup = styled.div`
  margin-bottom: 1rem;
`

const Label = styled.label`
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
`

const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  min-height: 80px;
  resize: vertical;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => props.$variant === 'primary' ? `
    background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
    color: white;
    border: none;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
  ` : `
    background: white;
    color: #6b7280;
    border: 1px solid #e5e7eb;

    &:hover {
      background: #f9fafb;
    }
  `}
`

const InvoiceCreatePage: React.FC = () => {
  const navigate = useNavigate()
  const {
    customers,
    registeredClients,
    error,
    saving,
    fetchCustomers,
    fetchRegisteredClients,
    createInvoice,
    createCustomer,
    clearError
  } = useInvoices()

  const [showCustomerModal, setShowCustomerModal] = useState(false)
  const [newCustomer, setNewCustomer] = useState<CustomerCreate>({
    name: '',
    email: '',
    phone: '',
    address: '',
    company: ''
  })

  useEffect(() => {
    fetchCustomers()
    fetchRegisteredClients()
  }, [fetchCustomers, fetchRegisteredClients])

  const handleSubmit = async (data: InvoiceCreate | InvoiceUpdate) => {
    // In create page, data will always be InvoiceCreate
    const invoice = await createInvoice(data as InvoiceCreate)
    navigate(`/dashboard/invoices/${invoice.id}`)
  }

  const handleCancel = () => {
    navigate('/dashboard/invoices')
  }

  const handleCreateCustomer = async () => {
    if (!newCustomer.name.trim()) return

    try {
      await createCustomer(newCustomer)
      setShowCustomerModal(false)
      setNewCustomer({ name: '', email: '', phone: '', address: '', company: '' })
    } catch (err) {
      // Error handled by hook
    }
  }

  return (
    <Container>
      <Header>
        <BackLink onClick={() => navigate('/dashboard/invoices')}>
          ← Back to Invoices
        </BackLink>
        <Title>Create Invoice</Title>
      </Header>

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={clearError} style={{ marginLeft: '1rem' }}>Dismiss</button>
        </ErrorMessage>
      )}

      <InvoiceForm
        customers={customers}
        registeredClients={registeredClients}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        onCreateCustomer={() => setShowCustomerModal(true)}
        onFetchRegisteredClients={fetchRegisteredClients}
        loading={saving}
      />

      {showCustomerModal && (
        <Modal onClick={() => setShowCustomerModal(false)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalTitle>Create New Customer</ModalTitle>

            <FormGroup>
              <Label>Name *</Label>
              <Input
                type="text"
                value={newCustomer.name}
                onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                placeholder="Customer name"
              />
            </FormGroup>

            <FormGroup>
              <Label>Email</Label>
              <Input
                type="email"
                value={newCustomer.email}
                onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                placeholder="customer@example.com"
              />
            </FormGroup>

            <FormGroup>
              <Label>Phone</Label>
              <Input
                type="tel"
                value={newCustomer.phone}
                onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
              />
            </FormGroup>

            <FormGroup>
              <Label>Company</Label>
              <Input
                type="text"
                value={newCustomer.company}
                onChange={(e) => setNewCustomer({ ...newCustomer, company: e.target.value })}
                placeholder="Company name"
              />
            </FormGroup>

            <FormGroup>
              <Label>Address</Label>
              <TextArea
                value={newCustomer.address}
                onChange={(e) => setNewCustomer({ ...newCustomer, address: e.target.value })}
                placeholder="Full address"
              />
            </FormGroup>

            <ModalActions>
              <Button onClick={() => setShowCustomerModal(false)}>Cancel</Button>
              <Button
                $variant="primary"
                onClick={handleCreateCustomer}
                disabled={!newCustomer.name.trim() || saving}
              >
                {saving ? 'Creating...' : 'Create Customer'}
              </Button>
            </ModalActions>
          </ModalContent>
        </Modal>
      )}
    </Container>
  )
}

export default InvoiceCreatePage
