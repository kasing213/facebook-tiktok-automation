import React, { useState, useRef, useCallback } from 'react'
import styled from 'styled-components'
import { inventoryService } from '../../../services/inventoryApi'

// Maximum file size: 50MB
const MAX_FILE_SIZE_MB = 50
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

// Allowed MIME types
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

interface ProductImageUploaderProps {
  productId?: string
  currentImageUrl?: string
  onImageSelected?: (file: File) => void  // For new products (before creation)
  onImageUploaded?: (imageUrl: string) => void
  onImageDeleted?: () => void
  disabled?: boolean
}

const Container = styled.div`
  width: 100%;
`

const DropZone = styled.div<{ $isDragging: boolean; $hasImage: boolean; $disabled?: boolean }>`
  position: relative;
  width: 120px;
  height: 120px;
  border: 2px dashed ${props => props.$isDragging ? props.theme.accent : props.theme.border};
  border-radius: 8px;
  background: ${props => props.$hasImage ? 'transparent' : props.theme.backgroundSecondary};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.2s ease;
  overflow: hidden;
  opacity: ${props => props.$disabled ? 0.6 : 1};

  &:hover {
    border-color: ${props => !props.$disabled && props.theme.accent};
    background: ${props => !props.$disabled && !props.$hasImage && props.theme.backgroundTertiary};
  }
`

const ImagePreview = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const Placeholder = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: ${props => props.theme.textSecondary};
  font-size: 11px;
  text-align: center;
  padding: 8px;
`

const PlaceholderIcon = styled.div`
  font-size: 24px;
  margin-bottom: 4px;
`

const Overlay = styled.div<{ $visible: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: ${props => props.$visible ? 1 : 0};
  transition: opacity 0.2s ease;

  ${DropZone}:hover & {
    opacity: 1;
  }
`

const OverlayButton = styled.button`
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;

  &:hover {
    background: white;
  }
`

const DeleteButton = styled(OverlayButton)`
  color: #e53e3e;
`

const ChangeButton = styled(OverlayButton)`
  color: #3182ce;
`

const HiddenInput = styled.input`
  display: none;
`

const ErrorMessage = styled.div`
  color: ${props => props.theme.error};
  font-size: 12px;
  margin-top: 4px;
`

const ProgressBar = styled.div<{ $progress: number }>`
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  width: ${props => props.$progress}%;
  background: ${props => props.theme.accent};
  transition: width 0.3s ease;
`

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
`

const FileSizeHint = styled.div`
  font-size: 10px;
  color: ${props => props.theme.textMuted};
  margin-top: 4px;
`

export const ProductImageUploader: React.FC<ProductImageUploaderProps> = ({
  productId,
  currentImageUrl,
  onImageSelected,
  onImageUploaded,
  onImageDeleted,
  disabled = false
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // Display URL: current from server, or local preview
  const displayUrl = previewUrl || currentImageUrl

  const validateFile = useCallback((file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File type not allowed. Supported: JPEG, PNG, WebP, GIF`
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size exceeds ${MAX_FILE_SIZE_MB}MB limit`
    }
    return null
  }, [])

  const handleFile = useCallback(async (file: File) => {
    setError(null)

    // Validate
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    // Create preview
    const objectUrl = URL.createObjectURL(file)
    setPreviewUrl(objectUrl)

    // If no productId, just notify parent (for new product flow)
    if (!productId) {
      onImageSelected?.(file)
      return
    }

    // Upload to server
    setIsUploading(true)
    setProgress(10)

    try {
      setProgress(30)
      const result = await inventoryService.uploadProductImage(productId, file)
      setProgress(100)

      // Clean up preview
      URL.revokeObjectURL(objectUrl)
      setPreviewUrl(null)

      onImageUploaded?.(result.image_url)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
      URL.revokeObjectURL(objectUrl)
      setPreviewUrl(null)
    } finally {
      setIsUploading(false)
      setProgress(0)
    }
  }, [productId, onImageSelected, onImageUploaded, validateFile])

  const handleDelete = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation()

    if (!productId || !currentImageUrl) {
      // Just clear local preview
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
        setPreviewUrl(null)
      }
      return
    }

    setIsDeleting(true)
    setError(null)

    try {
      await inventoryService.deleteProductImage(productId)
      onImageDeleted?.()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Delete failed')
    } finally {
      setIsDeleting(false)
    }
  }, [productId, currentImageUrl, previewUrl, onImageDeleted])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    if (disabled) return

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFile(file)
    }
  }, [disabled, handleFile])

  const handleClick = useCallback(() => {
    if (!disabled && !isUploading && !isDeleting) {
      fileInputRef.current?.click()
    }
  }, [disabled, isUploading, isDeleting])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
    // Reset input so same file can be selected again
    e.target.value = ''
  }, [handleFile])

  return (
    <Container>
      <DropZone
        $isDragging={isDragging}
        $hasImage={!!displayUrl}
        $disabled={disabled || isUploading || isDeleting}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {displayUrl ? (
          <>
            <ImagePreview src={displayUrl} alt="Product image" />
            <Overlay $visible={false}>
              <ChangeButton onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}>
                Change
              </ChangeButton>
              <DeleteButton onClick={handleDelete}>
                Delete
              </DeleteButton>
            </Overlay>
          </>
        ) : (
          <Placeholder>
            <PlaceholderIcon>📷</PlaceholderIcon>
            <span>Click or drag</span>
            <span>to upload</span>
          </Placeholder>
        )}

        {isUploading && (
          <>
            <LoadingOverlay>Uploading...</LoadingOverlay>
            <ProgressBar $progress={progress} />
          </>
        )}

        {isDeleting && (
          <LoadingOverlay>Deleting...</LoadingOverlay>
        )}

        <HiddenInput
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          onChange={handleInputChange}
          disabled={disabled || isUploading || isDeleting}
        />
      </DropZone>

      <FileSizeHint>Max {MAX_FILE_SIZE_MB}MB (JPEG, PNG, WebP, GIF)</FileSizeHint>

      {error && <ErrorMessage>{error}</ErrorMessage>}
    </Container>
  )
}

export default ProductImageUploader
