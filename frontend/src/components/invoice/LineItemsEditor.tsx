import React from 'react'
import styled from 'styled-components'
import { LineItem } from '../../types/invoice'

interface LineItemsEditorProps {
  items: LineItem[]
  onChange: (items: LineItem[]) => void
  readOnly?: boolean
}

const Container = styled.div`
  margin-bottom: 1.5rem;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`

const Label = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const AddButton = styled.button`
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  }
`

const ItemsTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
`

const TableHeader = styled.thead`
  background: #f9fafb;
`

const HeaderCell = styled.th`
  text-align: left;
  padding: 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;

  &:last-child {
    text-align: right;
  }
`

const TableBody = styled.tbody``

const TableRow = styled.tr`
  border-bottom: 1px solid #e5e7eb;

  &:last-child {
    border-bottom: none;
  }
`

const TableCell = styled.td`
  padding: 0.75rem;
  vertical-align: middle;

  &:last-child {
    text-align: right;
  }
`

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.875rem;
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

const NumberInput = styled(Input)`
  width: 100px;
  text-align: right;
`

const DeleteButton = styled.button`
  padding: 0.375rem 0.75rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: #c82333;
  }
`

const ItemTotal = styled.span`
  font-weight: 600;
  color: #1f2937;
`

const TotalsSection = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
`

const TotalRow = styled.div`
  display: flex;
  justify-content: space-between;
  width: 200px;
  font-size: 0.875rem;
  color: #6b7280;
`

const GrandTotalRow = styled(TotalRow)`
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  border-top: 2px solid #e5e7eb;
  padding-top: 0.5rem;
  margin-top: 0.5rem;
`

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-size: 0.875rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 2px dashed #e5e7eb;
`

export const LineItemsEditor: React.FC<LineItemsEditorProps> = ({
  items,
  onChange,
  readOnly = false
}) => {
  const addItem = () => {
    const newItem: LineItem = {
      description: '',
      quantity: 1,
      unit_price: 0,
      tax_rate: 0
    }
    onChange([...items, newItem])
  }

  const updateItem = (index: number, field: keyof LineItem, value: string | number) => {
    const updated = items.map((item, i) => {
      if (i === index) {
        return { ...item, [field]: value }
      }
      return item
    })
    onChange(updated)
  }

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index))
  }

  const calculateItemTotal = (item: LineItem): number => {
    const subtotal = item.quantity * item.unit_price
    const tax = subtotal * ((item.tax_rate || 0) / 100)
    return subtotal + tax
  }

  const calculateSubtotal = (): number => {
    return items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0)
  }

  const calculateTax = (): number => {
    return items.reduce((sum, item) => {
      const subtotal = item.quantity * item.unit_price
      return sum + (subtotal * ((item.tax_rate || 0) / 100))
    }, 0)
  }

  const calculateTotal = (): number => {
    return calculateSubtotal() + calculateTax()
  }

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <Container>
      <Header>
        <Label>Line Items</Label>
        {!readOnly && <AddButton onClick={addItem}>+ Add Item</AddButton>}
      </Header>

      {items.length === 0 ? (
        <EmptyState>
          No items added yet. Click "Add Item" to add line items to this invoice.
        </EmptyState>
      ) : (
        <>
          <ItemsTable>
            <TableHeader>
              <tr>
                <HeaderCell>Description</HeaderCell>
                <HeaderCell>Qty</HeaderCell>
                <HeaderCell>Unit Price</HeaderCell>
                <HeaderCell>Tax %</HeaderCell>
                <HeaderCell>Total</HeaderCell>
                {!readOnly && <HeaderCell></HeaderCell>}
              </tr>
            </TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Input
                      type="text"
                      value={item.description}
                      onChange={(e) => updateItem(index, 'description', e.target.value)}
                      placeholder="Item description"
                      readOnly={readOnly}
                    />
                  </TableCell>
                  <TableCell>
                    <NumberInput
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                      readOnly={readOnly}
                    />
                  </TableCell>
                  <TableCell>
                    <NumberInput
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.unit_price}
                      onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                      readOnly={readOnly}
                    />
                  </TableCell>
                  <TableCell>
                    <NumberInput
                      type="number"
                      min="0"
                      max="100"
                      value={item.tax_rate || 0}
                      onChange={(e) => updateItem(index, 'tax_rate', parseFloat(e.target.value) || 0)}
                      readOnly={readOnly}
                    />
                  </TableCell>
                  <TableCell>
                    <ItemTotal>{formatCurrency(calculateItemTotal(item))}</ItemTotal>
                  </TableCell>
                  {!readOnly && (
                    <TableCell>
                      <DeleteButton onClick={() => removeItem(index)}>Remove</DeleteButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </ItemsTable>

          <TotalsSection>
            <TotalRow>
              <span>Subtotal:</span>
              <span>{formatCurrency(calculateSubtotal())}</span>
            </TotalRow>
            <TotalRow>
              <span>Tax:</span>
              <span>{formatCurrency(calculateTax())}</span>
            </TotalRow>
            <GrandTotalRow>
              <span>Total:</span>
              <span>{formatCurrency(calculateTotal())}</span>
            </GrandTotalRow>
          </TotalsSection>
        </>
      )}
    </Container>
  )
}

export default LineItemsEditor
