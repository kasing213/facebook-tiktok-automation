import React, { useEffect, useState, useCallback } from 'react'
import styled from 'styled-components'
import { inventoryService } from '../../../services/inventoryApi'
import { Product, ProductCreate, ProductUpdate } from '../../../types/inventory'
import { fadeInDown, scaleIn, shake, easings, reduceMotion } from '../../../styles/animations'
import { useStaggeredAnimation } from '../../../hooks/useScrollAnimation'
import { ProductImageUploader } from './ProductImageUploader'

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

const HeaderActions = styled.div`
  display: flex;
  gap: 0.75rem;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ${easings.easeOutCubic},
              box-shadow 0.2s ${easings.easeOutCubic},
              background 0.2s ease;

  ${props => props.$variant === 'primary' ? `
    background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
    color: white;
    border: none;

    &:hover:not(:disabled) {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 4px 12px rgba(74, 144, 226, 0.35);
    }

    &:active:not(:disabled) {
      transform: translateY(0) scale(0.98);
    }
  ` : props.$variant === 'danger' ? `
    background: #dc3545;
    color: white;
    border: none;

    &:hover:not(:disabled) {
      background: #c82333;
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
    }

    &:active:not(:disabled) {
      transform: translateY(0) scale(0.98);
    }
  ` : `
    background: ${props.theme.card};
    color: ${props.theme.textSecondary};
    border: 1px solid ${props.theme.border};

    &:hover:not(:disabled) {
      background: ${props.theme.backgroundTertiary};
      border-color: ${props.theme.textMuted};
    }
  `}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  ${reduceMotion}
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`

const StatCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.25rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(15px)'};
  transition: opacity 0.4s ${easings.easeOutCubic},
              transform 0.4s ${easings.easeOutCubic},
              box-shadow 0.2s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
  }

  ${reduceMotion}
`

const StatLabel = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
`

const StatValue = styled.div<{ $color?: string }>`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.$color || props.theme.textPrimary};
`

const FilterToolbar = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
`

const SearchBox = styled.div`
  flex: 1;
  min-width: 200px;
  position: relative;
`

const SearchIcon = styled.span`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: ${props => props.theme.textMuted};
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
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};

  &::placeholder {
    color: ${props => props.theme.textMuted};
  }

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
  }
`

const FilterCheckbox = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: ${props => props.theme.textSecondary};
  cursor: pointer;

  input {
    width: 1rem;
    height: 1rem;
    cursor: pointer;
  }
`

const TableSection = styled.section`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  overflow: hidden;
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`

const TableHeader = styled.thead`
  background: ${props => props.theme.backgroundTertiary};
`

const TableHeaderCell = styled.th`
  text-align: left;
  padding: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid ${props => props.theme.border};
`

const TableBody = styled.tbody``

const TableRow = styled.tr<{ $isVisible?: boolean; $delay?: number }>`
  border-bottom: 1px solid ${props => props.theme.border};
  opacity: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 1 : 0) : 1};
  transform: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 'translateX(0)' : 'translateX(-10px)') : 'translateX(0)'};
  transition: opacity 0.3s ${easings.easeOutCubic},
              transform 0.3s ${easings.easeOutCubic},
              background 0.15s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: ${props => props.theme.backgroundTertiary};
  }

  ${reduceMotion}
`

const TableCell = styled.td`
  padding: 1rem;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  vertical-align: middle;
`

const ProductName = styled.div`
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
`

const ProductSku = styled.div`
  font-size: 0.75rem;
  color: ${props => props.theme.textSecondary};
`

const StockBadge = styled.span<{ $isLow: boolean }>`
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  background: ${props => props.$isLow ? '#fef2f2' : '#f0fdf4'};
  color: ${props => props.$isLow ? '#dc2626' : '#16a34a'};
`

const StatusText = styled.span<{ $active?: boolean }>`
  color: ${props => props.$active ? props.theme.success : props.theme.textSecondary};
`

const MutedText = styled.span`
  color: ${props => props.theme.textSecondary};
`

const ProductThumbnail = styled.img`
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid ${props => props.theme.border};
`

const NoImagePlaceholder = styled.div`
  width: 48px;
  height: 48px;
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: ${props => props.theme.textMuted};
  border: 1px dashed ${props => props.theme.border};
`

const ModalDescription = styled.p`
  color: ${props => props.theme.textSecondary};
  margin-bottom: 1.5rem;
`

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`

const IconButton = styled.button`
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${props => props.theme.textMuted};
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: ${props => props.theme.accent};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 18px;
    height: 18px;
  }
`

const ErrorMessage = styled.div`
  background: ${props => props.theme.mode === 'dark' ? 'rgba(220, 53, 69, 0.15)' : '#f8d7da'};
  color: ${props => props.theme.error};
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  animation: ${shake} 0.4s ease, ${fadeInDown} 0.3s ${easings.easeOutCubic};

  ${reduceMotion}
`

const SuccessMessage = styled.div`
  background: ${props => props.theme.mode === 'dark' ? 'rgba(40, 167, 69, 0.15)' : '#d4edda'};
  color: ${props => props.theme.success};
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  animation: ${fadeInDown} 0.3s ${easings.easeOutCubic};

  ${reduceMotion}
`

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};

  h3 {
    color: ${props => props.theme.textPrimary};
    margin-bottom: 0.5rem;
  }
`

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  padding: 3rem;
`

// Modal Components
const ModalOverlay = styled.div`
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
  animation: fadeIn 0.2s ${easings.easeOutCubic};

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  ${reduceMotion}
`

const ModalContent = styled.div`
  background: ${props => props.theme.card};
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: ${scaleIn} 0.3s ${easings.easeOutCubic};

  h2 {
    margin: 0 0 1.5rem 0;
    color: ${props => props.theme.textPrimary};
    font-size: 1.5rem;
  }

  ${reduceMotion}
`

const FormGroup = styled.div`
  margin-bottom: 1rem;
`

const FormLabel = styled.label`
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  margin-bottom: 0.5rem;
`

const FormInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};

  &::placeholder {
    color: ${props => props.theme.textMuted};
  }

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
    box-shadow: 0 0 0 2px ${props => props.theme.mode === 'dark' ? 'rgba(62, 207, 142, 0.1)' : 'rgba(74, 144, 226, 0.1)'};
  }
`

const FormTextarea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};
  min-height: 80px;
  resize: vertical;

  &::placeholder {
    color: ${props => props.theme.textMuted};
  }

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
    box-shadow: 0 0 0 2px ${props => props.theme.mode === 'dark' ? 'rgba(62, 207, 142, 0.1)' : 'rgba(74, 144, 226, 0.1)'};
  }
`

const FormSelect = styled.select`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
  }
`

const FormCheckbox = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  cursor: pointer;

  input {
    width: 1.125rem;
    height: 1.125rem;
    cursor: pointer;
  }
`

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
`

const FormRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
`

const InventoryListPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)

  // Animation hooks
  const statsVisible = useStaggeredAnimation(4, 80) // 4 stat cards
  const rowsVisible = useStaggeredAnimation(products.length, 40)

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showStockModal, setShowStockModal] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)

  // Form states
  const [formData, setFormData] = useState<ProductCreate>({
    name: '',
    sku: '',
    description: '',
    unit_price: 0,
    cost_price: 0,
    currency: 'USD',
    current_stock: 0,
    low_stock_threshold: 10,
    track_stock: true
  })
  const [newStockLevel, setNewStockLevel] = useState(0)
  const [stockNotes, setStockNotes] = useState('')
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null)

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true)
      const data = await inventoryService.listProducts({
        search: searchQuery || undefined,
        low_stock_only: showLowStockOnly || undefined
      })
      setProducts(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch products')
    } finally {
      setLoading(false)
    }
  }, [searchQuery, showLowStockOnly])

  useEffect(() => {
    fetchProducts()
  }, [fetchProducts])

  const formatCurrency = (amount: number, currency: string = 'USD'): string => {
    if (amount === null || amount === undefined || isNaN(amount)) {
      return currency === 'KHR' ? 'KHR 0' : '$0.00'
    }
    if (currency === 'KHR') {
      return new Intl.NumberFormat('km-KH', {
        style: 'currency',
        currency: 'KHR',
        minimumFractionDigits: 0
      }).format(amount)
    }
    // USD is stored in cents, convert to dollars for display
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount / 100)
  }

  // Helper to extract error message from FastAPI validation errors
  const extractErrorMessage = (err: any): string => {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      return detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ')
    }
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object') {
      return detail.msg || detail.message || JSON.stringify(detail)
    }
    return err.message || 'An error occurred'
  }

  // Convert user-friendly decimal price to backend integer (cents for USD)
  const priceToBackend = (price: number, currency: string): number => {
    if (currency === 'KHR') {
      return Math.round(price) // KHR doesn't use decimals
    }
    return Math.round(price * 100) // USD: dollars to cents
  }

  // Convert backend integer price to user-friendly decimal
  const priceFromBackend = (price: number, currency: string): number => {
    if (currency === 'KHR') {
      return price
    }
    return price / 100 // USD: cents to dollars
  }

  const handleCreate = async () => {
    try {
      setSaving(true)
      // Convert prices to backend format (cents for USD)
      const currency = formData.currency || 'USD'
      const submitData: ProductCreate = {
        ...formData,
        unit_price: priceToBackend(formData.unit_price, currency),
        cost_price: formData.cost_price ? priceToBackend(formData.cost_price, currency) : undefined
      }
      const newProduct = await inventoryService.createProduct(submitData)

      // Upload image if selected
      if (pendingImageFile && newProduct.id) {
        try {
          await inventoryService.uploadProductImage(newProduct.id, pendingImageFile)
        } catch (imgErr: any) {
          console.error('Image upload failed:', imgErr)
          // Don't fail the whole operation, just warn
          setError('Product created but image upload failed: ' + extractErrorMessage(imgErr))
        }
      }

      setSuccess('Product created successfully')
      setShowCreateModal(false)
      resetForm()
      fetchProducts()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedProduct) return
    try {
      setSaving(true)
      // Convert prices to backend format (cents for USD)
      const currency = formData.currency || 'USD'
      const updateData: ProductUpdate = {
        name: formData.name,
        sku: formData.sku,
        description: formData.description,
        unit_price: priceToBackend(formData.unit_price, currency),
        cost_price: formData.cost_price ? priceToBackend(formData.cost_price, currency) : undefined,
        currency: currency,
        low_stock_threshold: formData.low_stock_threshold,
        track_stock: formData.track_stock
      }
      await inventoryService.updateProduct(selectedProduct.id, updateData)
      setSuccess('Product updated successfully')
      setShowEditModal(false)
      resetForm()
      fetchProducts()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedProduct) return
    try {
      setSaving(true)
      await inventoryService.deleteProduct(selectedProduct.id)
      setSuccess('Product deleted successfully')
      setShowDeleteModal(false)
      setSelectedProduct(null)
      fetchProducts()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleStockAdjustment = async () => {
    if (!selectedProduct) return
    try {
      setSaving(true)
      await inventoryService.adjustStock({
        product_id: selectedProduct.id,
        new_stock_level: newStockLevel,
        notes: stockNotes || undefined
      })
      setSuccess('Stock adjusted successfully')
      setShowStockModal(false)
      setSelectedProduct(null)
      setNewStockLevel(0)
      setStockNotes('')
      fetchProducts()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const openEditModal = (product: Product) => {
    setSelectedProduct(product)
    const currency = product.currency || 'USD'
    setFormData({
      name: product.name,
      sku: product.sku || '',
      description: product.description || '',
      // Convert backend prices (cents) to user-friendly format (dollars)
      unit_price: priceFromBackend(product.unit_price, currency),
      cost_price: product.cost_price ? priceFromBackend(product.cost_price, currency) : 0,
      currency: currency,
      current_stock: product.current_stock,
      low_stock_threshold: product.low_stock_threshold,
      track_stock: product.track_stock
    })
    setShowEditModal(true)
  }

  const openStockModal = (product: Product) => {
    setSelectedProduct(product)
    setNewStockLevel(product.current_stock)
    setStockNotes('')
    setShowStockModal(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      sku: '',
      description: '',
      unit_price: 0,
      cost_price: 0,
      currency: 'USD',
      current_stock: 0,
      low_stock_threshold: 10,
      track_stock: true
    })
    setSelectedProduct(null)
    setPendingImageFile(null)
  }

  // Stats calculations
  const totalProducts = products.length
  const activeProducts = products.filter(p => p.is_active).length
  const lowStockCount = products.filter(p => p.track_stock && p.current_stock <= p.low_stock_threshold).length
  // Note: unit_price is in cents for USD, so totalStockValue will also be in cents
  const totalStockValue = products.reduce((sum, p) => sum + (p.current_stock * p.unit_price), 0)

  return (
    <Container>
      <Header>
        <Title>Inventory</Title>
        <HeaderActions>
          <Button $variant="primary" onClick={() => setShowCreateModal(true)}>
            + Add Product
          </Button>
        </HeaderActions>
      </Header>

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={() => setError(null)} style={{ marginLeft: '1rem' }}>Dismiss</button>
        </ErrorMessage>
      )}

      {success && <SuccessMessage>{success}</SuccessMessage>}

      <StatsGrid>
        <StatCard $isVisible={statsVisible[0]} $delay={0}>
          <StatLabel>Total Products</StatLabel>
          <StatValue>{totalProducts}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[1]} $delay={80}>
          <StatLabel>Active Products</StatLabel>
          <StatValue $color="#28a745">{activeProducts}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[2]} $delay={160}>
          <StatLabel>Low Stock</StatLabel>
          <StatValue $color={lowStockCount > 0 ? '#dc3545' : '#28a745'}>{lowStockCount}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[3]} $delay={240}>
          <StatLabel>Total Stock Value</StatLabel>
          <StatValue $color="#4a90e2">{formatCurrency(totalStockValue)}</StatValue>
        </StatCard>
      </StatsGrid>

      <FilterToolbar>
        <SearchBox>
          <SearchIcon>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </SearchIcon>
          <SearchInput
            type="text"
            placeholder="Search products by name or SKU..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </SearchBox>
        <FilterCheckbox>
          <input
            type="checkbox"
            checked={showLowStockOnly}
            onChange={(e) => setShowLowStockOnly(e.target.checked)}
          />
          Low Stock Only
        </FilterCheckbox>
      </FilterToolbar>

      <TableSection>
        {loading ? (
          <LoadingSpinner>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </LoadingSpinner>
        ) : products.length === 0 ? (
          <EmptyState>
            <h3>No products found</h3>
            <p>Create your first product to start tracking inventory.</p>
            <Button $variant="primary" onClick={() => setShowCreateModal(true)} style={{ marginTop: '1rem' }}>
              + Add Product
            </Button>
          </EmptyState>
        ) : (
          <Table>
            <TableHeader>
              <tr>
                <TableHeaderCell style={{ width: '60px' }}>Image</TableHeaderCell>
                <TableHeaderCell>Product</TableHeaderCell>
                <TableHeaderCell>Price</TableHeaderCell>
                <TableHeaderCell>Stock</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </tr>
            </TableHeader>
            <TableBody>
              {products.map((product, index) => {
                const isLowStock = product.track_stock && product.current_stock <= product.low_stock_threshold
                return (
                  <TableRow key={product.id} $isVisible={rowsVisible[index]} $delay={index * 40}>
                    <TableCell>
                      {product.image_url ? (
                        <ProductThumbnail src={product.image_url} alt={product.name} />
                      ) : (
                        <NoImagePlaceholder>📦</NoImagePlaceholder>
                      )}
                    </TableCell>
                    <TableCell>
                      <ProductName>{product.name}</ProductName>
                      {product.sku && <ProductSku>SKU: {product.sku}</ProductSku>}
                    </TableCell>
                    <TableCell>{formatCurrency(product.unit_price, product.currency)}</TableCell>
                    <TableCell>
                      {product.track_stock ? (
                        <StockBadge $isLow={isLowStock}>
                          {product.current_stock} units
                        </StockBadge>
                      ) : (
                        <MutedText>Not tracked</MutedText>
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusText $active={product.is_active}>
                        {product.is_active ? 'Active' : 'Inactive'}
                      </StatusText>
                    </TableCell>
                    <TableCell>
                      <ActionButtons>
                        <IconButton title="Edit" onClick={() => openEditModal(product)}>
                          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </IconButton>
                        <IconButton title="Adjust Stock" onClick={() => openStockModal(product)}>
                          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                          </svg>
                        </IconButton>
                        <IconButton title="Duplicate" onClick={() => {
                          setFormData({
                            name: product.name + ' (Copy)',
                            sku: product.sku ? product.sku + '-COPY' : '',
                            description: product.description || '',
                            unit_price: priceFromBackend(product.unit_price, product.currency || 'USD'),
                            cost_price: product.cost_price ? priceFromBackend(product.cost_price, product.currency || 'USD') : 0,
                            currency: product.currency || 'USD',
                            current_stock: 0,
                            low_stock_threshold: product.low_stock_threshold,
                            track_stock: product.track_stock
                          })
                          setShowCreateModal(true)
                        }}>
                          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </IconButton>
                        <IconButton
                          title="Delete"
                          onClick={() => {
                            setSelectedProduct(product)
                            setShowDeleteModal(true)
                          }}
                        >
                          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </IconButton>
                      </ActionButtons>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </TableSection>

      {/* Create/Edit Product Modal */}
      {(showCreateModal || showEditModal) && (
        <ModalOverlay onClick={() => {
          setShowCreateModal(false)
          setShowEditModal(false)
          resetForm()
        }}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <h2>{showCreateModal ? 'Add Product' : 'Edit Product'}</h2>

            <FormGroup>
              <FormLabel>Product Image (Optional)</FormLabel>
              <ProductImageUploader
                productId={selectedProduct?.id}
                currentImageUrl={selectedProduct?.image_url}
                onImageSelected={(file) => setPendingImageFile(file)}
                onImageUploaded={() => fetchProducts()}
                onImageDeleted={() => fetchProducts()}
                disabled={saving}
              />
            </FormGroup>

            <FormGroup>
              <FormLabel>Product Name *</FormLabel>
              <FormInput
                type="text"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter product name"
              />
            </FormGroup>

            <FormRow>
              <FormGroup>
                <FormLabel>SKU</FormLabel>
                <FormInput
                  type="text"
                  value={formData.sku}
                  onChange={e => setFormData({ ...formData, sku: e.target.value })}
                  placeholder="e.g., PROD-001"
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Currency</FormLabel>
                <FormSelect
                  value={formData.currency}
                  onChange={e => setFormData({ ...formData, currency: e.target.value })}
                >
                  <option value="USD">USD</option>
                  <option value="KHR">KHR</option>
                </FormSelect>
              </FormGroup>
            </FormRow>

            <FormGroup>
              <FormLabel>Description</FormLabel>
              <FormTextarea
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
                placeholder="Product description (optional)"
              />
            </FormGroup>

            <FormRow>
              <FormGroup>
                <FormLabel>Unit Price *</FormLabel>
                <FormInput
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.unit_price}
                  onChange={e => setFormData({ ...formData, unit_price: parseFloat(e.target.value) || 0 })}
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Cost Price</FormLabel>
                <FormInput
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.cost_price}
                  onChange={e => setFormData({ ...formData, cost_price: parseFloat(e.target.value) || 0 })}
                />
              </FormGroup>
            </FormRow>

            {showCreateModal && (
              <FormGroup>
                <FormLabel>Initial Stock</FormLabel>
                <FormInput
                  type="number"
                  min="0"
                  value={formData.current_stock}
                  onChange={e => setFormData({ ...formData, current_stock: parseInt(e.target.value) || 0 })}
                />
              </FormGroup>
            )}

            <FormRow>
              <FormGroup>
                <FormLabel>Low Stock Threshold</FormLabel>
                <FormInput
                  type="number"
                  min="0"
                  value={formData.low_stock_threshold}
                  onChange={e => setFormData({ ...formData, low_stock_threshold: parseInt(e.target.value) || 0 })}
                />
              </FormGroup>
              <FormGroup style={{ display: 'flex', alignItems: 'flex-end' }}>
                <FormCheckbox>
                  <input
                    type="checkbox"
                    checked={formData.track_stock}
                    onChange={e => setFormData({ ...formData, track_stock: e.target.checked })}
                  />
                  Track Stock
                </FormCheckbox>
              </FormGroup>
            </FormRow>

            <ModalActions>
              <Button onClick={() => {
                setShowCreateModal(false)
                setShowEditModal(false)
                resetForm()
              }}>Cancel</Button>
              <Button
                $variant="primary"
                onClick={showCreateModal ? handleCreate : handleUpdate}
                disabled={saving || !formData.name}
              >
                {saving ? 'Saving...' : (showCreateModal ? 'Create Product' : 'Save Changes')}
              </Button>
            </ModalActions>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* Stock Adjustment Modal */}
      {showStockModal && selectedProduct && (
        <ModalOverlay onClick={() => {
          setShowStockModal(false)
          setSelectedProduct(null)
        }}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <h2>Adjust Stock</h2>
            <ModalDescription>
              Adjust stock level for <strong>{selectedProduct.name}</strong>
            </ModalDescription>

            <FormGroup>
              <FormLabel>Current Stock: {selectedProduct.current_stock} units</FormLabel>
            </FormGroup>

            <FormGroup>
              <FormLabel>New Stock Level *</FormLabel>
              <FormInput
                type="number"
                min="0"
                value={newStockLevel}
                onChange={e => setNewStockLevel(parseInt(e.target.value) || 0)}
              />
            </FormGroup>

            <FormGroup>
              <FormLabel>Notes</FormLabel>
              <FormTextarea
                value={stockNotes}
                onChange={e => setStockNotes(e.target.value)}
                placeholder="Reason for adjustment (optional)"
              />
            </FormGroup>

            <ModalActions>
              <Button onClick={() => {
                setShowStockModal(false)
                setSelectedProduct(null)
              }}>Cancel</Button>
              <Button
                $variant="primary"
                onClick={handleStockAdjustment}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Adjust Stock'}
              </Button>
            </ModalActions>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedProduct && (
        <ModalOverlay onClick={() => {
          setShowDeleteModal(false)
          setSelectedProduct(null)
        }}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <h2>Delete Product</h2>
            <ModalDescription>
              Are you sure you want to delete <strong>{selectedProduct.name}</strong>?
              This action cannot be undone.
            </ModalDescription>
            <ModalActions>
              <Button onClick={() => {
                setShowDeleteModal(false)
                setSelectedProduct(null)
              }}>Cancel</Button>
              <Button
                $variant="danger"
                onClick={handleDelete}
                disabled={saving}
              >
                {saving ? 'Deleting...' : 'Delete Product'}
              </Button>
            </ModalActions>
          </ModalContent>
        </ModalOverlay>
      )}
    </Container>
  )
}

export default InventoryListPage
