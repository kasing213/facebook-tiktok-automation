import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { Invoice, InvoiceCreate, InvoiceUpdate, Customer, LineItem, InvoiceStatus, Currency, RegisteredClient } from '../../types/invoice'
import { LineItemsEditor } from './LineItemsEditor'
import { CustomerSelect } from './CustomerSelect'
import { InvoiceStatusBadge } from './InvoiceStatusBadge'
import { RegisteredClientSelect } from './RegisteredClientSelect'

interface InvoiceFormProps {
  invoice?: Invoice
  customers: Customer[]
  registeredClients?: RegisteredClient[]
  onSubmit: (data: InvoiceCreate | InvoiceUpdate) => Promise<void>
  onCancel: () => void
  onCreateCustomer?: () => void
  onFetchRegisteredClients?: () => void
  loading?: boolean
  isEdit?: boolean
}

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`

const FormSection = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
`

const SectionTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
`

const FormRow = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
`

const Label = styled.label`
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
`

const Input = styled.input`
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }

  &:read-only {
    background: #f9fafb;
    cursor: default;
  }
`

const TextArea = styled.textarea`
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  min-height: 100px;
  resize: vertical;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const Select = styled.select`
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  background: white;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const ButtonRow = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
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

const StatusSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
`

const StatusLabel = styled.span`
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
`

const ErrorMessage = styled.div`
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
`

const CustomerTypeTabs = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
`

const CustomerTypeTab = styled.button<{ $active?: boolean }>`
  padding: 0.5rem 1rem;
  border: 1px solid ${props => props.$active ? '#4a90e2' : '#e5e7eb'};
  border-radius: 6px;
  background: ${props => props.$active ? '#eef6ff' : 'white'};
  color: ${props => props.$active ? '#4a90e2' : '#6b7280'};
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #4a90e2;
    color: #4a90e2;
  }
`

const TelegramBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-left: 0.5rem;
`

const OptionalLabel = styled.span`
  color: #9ca3af;
  font-weight: 400;
  font-size: 0.75rem;
  margin-left: 0.25rem;
`

export const InvoiceForm: React.FC<InvoiceFormProps> = ({
  invoice,
  customers,
  registeredClients = [],
  onSubmit,
  onCancel,
  onCreateCustomer,
  onFetchRegisteredClients,
  loading = false,
  isEdit = false
}) => {
  const [customerType, setCustomerType] = useState<'manual' | 'registered'>('manual')
  const [customerId, setCustomerId] = useState(invoice?.customer_id || '')
  const [items, setItems] = useState<LineItem[]>(invoice?.items || [])
  const [dueDate, setDueDate] = useState(invoice?.due_date?.split('T')[0] || '')
  const [notes, setNotes] = useState(invoice?.notes || '')
  const [discount, setDiscount] = useState(invoice?.discount || 0)
  const [status, setStatus] = useState<InvoiceStatus>(invoice?.status || 'draft')
  const [error, setError] = useState<string | null>(null)

  // Line items currency settings
  const [lineItemsCurrency, setLineItemsCurrency] = useState<Currency>(invoice?.line_items_currency || 'USD')
  const [exchangeRate, setExchangeRate] = useState(invoice?.exchange_rate || 4100)

  // Payment verification fields (optional)
  const [bank, setBank] = useState(invoice?.bank || '')
  const [expectedAccount, setExpectedAccount] = useState(invoice?.expected_account || '')
  const [recipientName, setRecipientName] = useState(invoice?.recipient_name || '')
  const [currency, setCurrency] = useState<Currency>(invoice?.currency || 'KHR')

  useEffect(() => {
    if (invoice) {
      setCustomerId(invoice.customer_id)
      setItems(invoice.items)
      setDueDate(invoice.due_date?.split('T')[0] || '')
      setNotes(invoice.notes || '')
      setDiscount(invoice.discount || 0)
      setStatus(invoice.status)
      setLineItemsCurrency(invoice.line_items_currency || 'USD')
      setExchangeRate(invoice.exchange_rate || 4100)
      setBank(invoice.bank || '')
      setExpectedAccount(invoice.expected_account || '')
      setRecipientName(invoice.recipient_name || '')
      setCurrency(invoice.currency || 'KHR')
    }
  }, [invoice])

  // Fetch registered clients when switching to that tab
  useEffect(() => {
    if (customerType === 'registered' && onFetchRegisteredClients) {
      onFetchRegisteredClients()
    }
  }, [customerType, onFetchRegisteredClients])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!customerId) {
      setError('Please select a customer')
      return
    }

    if (items.length === 0) {
      setError('Please add at least one line item')
      return
    }

    if (items.some(item => !item.description.trim())) {
      setError('All line items must have a description')
      return
    }

    try {
      if (isEdit) {
        const updateData: InvoiceUpdate = {
          items,
          due_date: dueDate || undefined,
          notes: notes || undefined,
          discount: discount || undefined,
          status,
          line_items_currency: lineItemsCurrency,
          exchange_rate: exchangeRate,
          bank: bank || undefined,
          expected_account: expectedAccount || undefined,
          recipient_name: recipientName || undefined,
          currency: currency || undefined
        }
        await onSubmit(updateData)
      } else {
        const createData: InvoiceCreate = {
          customer_id: customerId,
          items,
          due_date: dueDate || undefined,
          notes: notes || undefined,
          discount: discount || undefined,
          line_items_currency: lineItemsCurrency,
          exchange_rate: exchangeRate,
          bank: bank || undefined,
          expected_account: expectedAccount || undefined,
          recipient_name: recipientName || undefined,
          currency: currency || undefined
        }
        await onSubmit(createData)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save invoice')
    }
  }

  const handleCustomerSelect = (customer: Customer | null) => {
    setCustomerId(customer?.id || '')
  }

  const handleRegisteredClientSelect = (client: RegisteredClient | null) => {
    setCustomerId(client?.id || '')
  }

  // Check if selected client has Telegram linked
  const selectedRegisteredClient = registeredClients.find(c => c.id === customerId)
  const hasTelegramLinked = selectedRegisteredClient?.telegram_linked || false

  return (
    <Form onSubmit={handleSubmit}>
      <FormSection>
        <SectionTitle>Customer Information</SectionTitle>

        {!isEdit && (
          <CustomerTypeTabs>
            <CustomerTypeTab
              type="button"
              $active={customerType === 'manual'}
              onClick={() => { setCustomerType('manual'); setCustomerId('') }}
            >
              Manual Entry
            </CustomerTypeTab>
            <CustomerTypeTab
              type="button"
              $active={customerType === 'registered'}
              onClick={() => { setCustomerType('registered'); setCustomerId('') }}
            >
              Registered Clients
              {registeredClients.length > 0 && (
                <TelegramBadge>{registeredClients.length}</TelegramBadge>
              )}
            </CustomerTypeTab>
          </CustomerTypeTabs>
        )}

        {customerType === 'manual' ? (
          <CustomerSelect
            customers={customers}
            selectedId={customerId}
            onSelect={handleCustomerSelect}
            onCreateNew={onCreateCustomer}
            disabled={isEdit}
          />
        ) : (
          <RegisteredClientSelect
            clients={registeredClients}
            selectedId={customerId}
            onSelect={handleRegisteredClientSelect}
            disabled={isEdit}
          />
        )}

        {hasTelegramLinked && (
          <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: '#e8f5e9', borderRadius: '6px', fontSize: '0.875rem', color: '#2e7d32' }}>
            [Telegram] Invoice will be auto-sent to client via Telegram
          </div>
        )}
      </FormSection>

      <FormSection>
        <LineItemsEditor
          items={items}
          onChange={setItems}
          currency={lineItemsCurrency}
          onCurrencyChange={setLineItemsCurrency}
          exchangeRate={exchangeRate}
          onExchangeRateChange={setExchangeRate}
        />
      </FormSection>

      <FormSection>
        <SectionTitle>Invoice Details</SectionTitle>

        {isEdit && (
          <StatusSection>
            <StatusLabel>Status:</StatusLabel>
            <Select
              value={status}
              onChange={(e) => setStatus(e.target.value as InvoiceStatus)}
            >
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </Select>
            <InvoiceStatusBadge status={status} />
          </StatusSection>
        )}

        <FormRow>
          <FormGroup>
            <Label>Due Date</Label>
            <Input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </FormGroup>
          <FormGroup>
            <Label>Discount (%)</Label>
            <Input
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={discount}
              onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
            />
          </FormGroup>
        </FormRow>

        <FormGroup>
          <Label>Notes</Label>
          <TextArea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional notes for this invoice..."
          />
        </FormGroup>
      </FormSection>

      {/* Payment Verification Section (Optional) */}
      <FormSection>
        <SectionTitle>
          Payment Verification
          <OptionalLabel>(Optional - for Telegram payment verification)</OptionalLabel>
        </SectionTitle>

        <FormRow>
          <FormGroup>
            <Label>Currency</Label>
            <Select
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
            >
              <option value="KHR">KHR (Cambodian Riel)</option>
              <option value="USD">USD (US Dollar)</option>
            </Select>
          </FormGroup>
          <FormGroup>
            <Label>Bank<OptionalLabel>(optional)</OptionalLabel></Label>
            <Input
              type="text"
              value={bank}
              onChange={(e) => setBank(e.target.value)}
              placeholder="e.g., ABA Bank, ACLEDA"
            />
          </FormGroup>
        </FormRow>

        <FormRow>
          <FormGroup>
            <Label>Expected Account Number<OptionalLabel>(optional)</OptionalLabel></Label>
            <Input
              type="text"
              value={expectedAccount}
              onChange={(e) => setExpectedAccount(e.target.value)}
              placeholder="e.g., 000 123 456"
            />
          </FormGroup>
          <FormGroup>
            <Label>Recipient Name<OptionalLabel>(optional)</OptionalLabel></Label>
            <Input
              type="text"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              placeholder="Account holder name (e.g., John Doe)"
            />
          </FormGroup>
        </FormRow>
      </FormSection>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <ButtonRow>
        <Button type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" $variant="primary" disabled={loading}>
          {loading ? 'Saving...' : isEdit ? 'Update Invoice' : 'Create Invoice'}
        </Button>
      </ButtonRow>
    </Form>
  )
}

export default InvoiceForm
