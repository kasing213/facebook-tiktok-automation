import React, { useState, useEffect, useCallback, useRef } from 'react'
import styled from 'styled-components'
import { invoiceProductService } from '../../services/inventoryApi'

interface Product {
  id: string
  name: string
  sku?: string
  unit_price: number
  currency: string
  current_stock: number
  track_stock: boolean
}

interface ProductPickerProps {
  onSelect: (product: Product) => void
  disabled?: boolean
}

const Container = styled.div`
  position: relative;
  display: inline-block;
`

const PickerButton = styled.button`
  padding: 0.5rem 1rem;
  background: #f0f9ff;
  color: #0369a1;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    background: #e0f2fe;
    border-color: #7dd3fc;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const Dropdown = styled.div<{ $isOpen: boolean }>`
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 360px;
  max-height: 400px;
  overflow: hidden;
  z-index: 100;
  display: ${props => props.$isOpen ? 'flex' : 'none'};
  flex-direction: column;
`

const SearchBox = styled.div`
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
`

const SearchInput = styled.input`
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const ProductList = styled.div`
  overflow-y: auto;
  max-height: 300px;
`

const ProductItem = styled.div<{ $outOfStock?: boolean }>`
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  cursor: ${props => props.$outOfStock ? 'not-allowed' : 'pointer'};
  transition: background 0.15s ease;
  opacity: ${props => props.$outOfStock ? 0.5 : 1};

  &:hover {
    background: ${props => props.$outOfStock ? 'transparent' : '#f9fafb'};
  }

  &:last-child {
    border-bottom: none;
  }
`

const ProductName = styled.div`
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
`

const ProductMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #6b7280;
`

const ProductPrice = styled.span`
  color: #0369a1;
  font-weight: 500;
`

const StockBadge = styled.span<{ $isLow?: boolean }>`
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  background: ${props => props.$isLow ? '#fef2f2' : '#f0fdf4'};
  color: ${props => props.$isLow ? '#dc2626' : '#16a34a'};
`

const EmptyState = styled.div`
  padding: 2rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
`

const LoadingState = styled.div`
  padding: 2rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
`

const ErrorState = styled.div`
  padding: 1rem;
  text-align: center;
  color: #dc2626;
  font-size: 0.875rem;
  background: #fef2f2;
`

export const ProductPicker: React.FC<ProductPickerProps> = ({ onSelect, disabled }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  const fetchProducts = useCallback(async (search?: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await invoiceProductService.getProductsForInvoice(search)
      setProducts(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load products')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      fetchProducts(searchQuery || undefined)
      // Focus search input when dropdown opens
      setTimeout(() => searchInputRef.current?.focus(), 100)
    }
  }, [isOpen, fetchProducts])

  // Debounced search
  useEffect(() => {
    if (!isOpen) return

    const timer = setTimeout(() => {
      fetchProducts(searchQuery || undefined)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery, isOpen, fetchProducts])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (product: Product) => {
    if (product.track_stock && product.current_stock <= 0) {
      return // Don't select out-of-stock items
    }
    onSelect(product)
    setIsOpen(false)
    setSearchQuery('')
  }

  const formatCurrency = (amount: number, currency: string): string => {
    if (currency === 'KHR') {
      return new Intl.NumberFormat('km-KH', {
        style: 'currency',
        currency: 'KHR',
        minimumFractionDigits: 0
      }).format(amount)
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <Container ref={containerRef}>
      <PickerButton
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
      >
        📦 Select Product
      </PickerButton>

      <Dropdown $isOpen={isOpen}>
        <SearchBox>
          <SearchInput
            ref={searchInputRef}
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </SearchBox>

        <ProductList>
          {loading ? (
            <LoadingState>Loading products...</LoadingState>
          ) : error ? (
            <ErrorState>{error}</ErrorState>
          ) : products.length === 0 ? (
            <EmptyState>
              {searchQuery ? 'No products found' : 'No products available'}
            </EmptyState>
          ) : (
            products.map(product => {
              const isOutOfStock = product.track_stock && product.current_stock <= 0
              const isLowStock = product.track_stock && product.current_stock > 0 && product.current_stock <= 10

              return (
                <ProductItem
                  key={product.id}
                  $outOfStock={isOutOfStock}
                  onClick={() => handleSelect(product)}
                >
                  <ProductName>
                    {product.name}
                    {product.sku && <span style={{ color: '#6b7280', fontWeight: 400 }}> ({product.sku})</span>}
                  </ProductName>
                  <ProductMeta>
                    <ProductPrice>{formatCurrency(product.unit_price, product.currency)}</ProductPrice>
                    {product.track_stock ? (
                      isOutOfStock ? (
                        <StockBadge $isLow>Out of stock</StockBadge>
                      ) : (
                        <StockBadge $isLow={isLowStock}>
                          {product.current_stock} in stock
                        </StockBadge>
                      )
                    ) : (
                      <span style={{ fontSize: '0.6875rem' }}>Stock not tracked</span>
                    )}
                  </ProductMeta>
                </ProductItem>
              )
            })
          )}
        </ProductList>
      </Dropdown>
    </Container>
  )
}

export default ProductPicker
