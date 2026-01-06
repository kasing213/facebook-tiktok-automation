import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { Invoice, InvoiceCreate, InvoiceUpdate, Customer, LineItem, InvoiceStatus } from '../../types/invoice'
import { LineItemsEditor } from './LineItemsEditor'
import { CustomerSelect } from './CustomerSelect'
import { InvoiceStatusBadge } from './InvoiceStatusBadge'

interface InvoiceFormProps {
  invoice?: Invoice
  customers: Customer[]
  onSubmit: (data: InvoiceCreate | InvoiceUpdate) => Promise<void>
  onCancel: () => void
  onCreateCustomer?: () => void
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

export const InvoiceForm: React.FC<InvoiceFormProps> = ({
  invoice,
  customers,
  onSubmit,
  onCancel,
  onCreateCustomer,
  loading = false,
  isEdit = false
}) => {
  const [customerId, setCustomerId] = useState(invoice?.customer_id || '')
  const [items, setItems] = useState<LineItem[]>(invoice?.items || [])
  const [dueDate, setDueDate] = useState(invoice?.due_date?.split('T')[0] || '')
  const [notes, setNotes] = useState(invoice?.notes || '')
  const [discount, setDiscount] = useState(invoice?.discount || 0)
  const [status, setStatus] = useState<InvoiceStatus>(invoice?.status || 'draft')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (invoice) {
      setCustomerId(invoice.customer_id)
      setItems(invoice.items)
      setDueDate(invoice.due_date?.split('T')[0] || '')
      setNotes(invoice.notes || '')
      setDiscount(invoice.discount || 0)
      setStatus(invoice.status)
    }
  }, [invoice])

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
          status
        }
        await onSubmit(updateData)
      } else {
        const createData: InvoiceCreate = {
          customer_id: customerId,
          items,
          due_date: dueDate || undefined,
          notes: notes || undefined,
          discount: discount || undefined
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

  return (
    <Form onSubmit={handleSubmit}>
      <FormSection>
        <SectionTitle>Customer Information</SectionTitle>
        <CustomerSelect
          customers={customers}
          selectedId={customerId}
          onSelect={handleCustomerSelect}
          onCreateNew={onCreateCustomer}
          disabled={isEdit}
        />
      </FormSection>

      <FormSection>
        <LineItemsEditor
          items={items}
          onChange={setItems}
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
