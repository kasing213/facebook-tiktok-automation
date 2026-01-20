// frontend/src/components/dashboard/ads-alert/MediaUploader.tsx
import React, { useState, useCallback, useRef } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'

interface MediaUploaderProps {
  folderId?: string
  onUploadComplete?: (files: UploadedFile[]) => void
  onUploadError?: (error: string) => void
  maxFiles?: number
  maxFileSize?: number // in MB
}

interface UploadedFile {
  id: string
  filename: string
  url: string
  fileType: string
  fileSize: number
}

interface FilePreview {
  file: File
  preview: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  result?: UploadedFile
}

const Container = styled.div`
  width: 100%;
`

const DropZone = styled.div<{ $isDragActive: boolean; $hasFiles: boolean }>`
  border: 2px dashed ${props => props.$isDragActive ? '#4A90E2' : '#d1d5db'};
  border-radius: 12px;
  padding: ${props => props.$hasFiles ? '16px' : '40px'};
  text-align: center;
  background: ${props => props.$isDragActive ? 'rgba(74, 144, 226, 0.05)' : '#fafafa'};
  transition: all 0.2s ease;
  cursor: pointer;
  min-height: ${props => props.$hasFiles ? 'auto' : '200px'};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  &:hover {
    border-color: #4A90E2;
    background: rgba(74, 144, 226, 0.02);
  }
`

const DropIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
  color: #9ca3af;
`

const DropText = styled.p`
  color: #6b7280;
  font-size: 16px;
  margin: 0 0 8px 0;
`

const DropSubtext = styled.p`
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
`

const BrowseButton = styled.button`
  margin-top: 16px;
  padding: 10px 24px;
  background: #4A90E2;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #357ABD;
  }
`

const HiddenInput = styled.input`
  display: none;
`

const PreviewList = styled.div`
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
`

const PreviewItem = styled.div`
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: #f3f4f6;
  aspect-ratio: 1;
`

const PreviewImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const PreviewVideo = styled.video`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const PreviewDocument = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
`

const DocumentIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  color: #6b7280;

  svg {
    width: 32px;
    height: 32px;
  }
`

const DocumentName = styled.span`
  font-size: 10px;
  color: #6b7280;
  text-align: center;
  word-break: break-word;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`

const ProgressOverlay = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px;
`

const ProgressBar = styled.div<{ $progress: number }>`
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;

  &::after {
    content: '';
    display: block;
    height: 100%;
    width: ${props => props.$progress}%;
    background: #4A90E2;
    transition: width 0.3s ease;
  }
`

const StatusBadge = styled.div<{ $status: string }>`
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.$status) {
      case 'success': return '#10b981'
      case 'error': return '#ef4444'
      case 'uploading': return '#4A90E2'
      default: return '#9ca3af'
    }
  }};
  color: white;

  svg {
    width: 12px;
    height: 12px;
  }
`

const RemoveButton = styled.button`
  position: absolute;
  top: 4px;
  left: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;

  ${PreviewItem}:hover & {
    opacity: 1;
  }

  &:hover {
    background: rgba(239, 68, 68, 0.8);
  }
`

const ErrorMessage = styled.div`
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
`

const UploadActions = styled.div`
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
`

const ActionButton = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  ${props => props.$variant === 'primary' ? `
    background: #4A90E2;
    color: white;
    border: none;

    &:hover:not(:disabled) {
      background: #357ABD;
    }

    &:disabled {
      background: #9ca3af;
      cursor: not-allowed;
    }
  ` : `
    background: white;
    color: #6b7280;
    border: 1px solid #d1d5db;

    &:hover {
      background: #f3f4f6;
    }
  `}
`

const ALLOWED_TYPES = [
  'image/jpeg', 'image/png', 'image/gif', 'image/webp',
  'video/mp4', 'video/webm', 'video/quicktime',
  'application/pdf', 'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

const MediaUploader: React.FC<MediaUploaderProps> = ({
  folderId,
  onUploadComplete,
  onUploadError,
  maxFiles = 10,
  maxFileSize = 50 // 50MB default
}) => {
  const [files, setFiles] = useState<FilePreview[]>([])
  const [isDragActive, setIsDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback((file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File type "${file.type}" is not supported`
    }
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size exceeds ${maxFileSize}MB limit`
    }
    return null
  }, [maxFileSize])

  const createPreview = useCallback((file: File): string => {
    if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
      return URL.createObjectURL(file)
    }
    return ''
  }, [])

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    setError(null)
    const fileArray = Array.from(newFiles)

    // Check max files limit
    if (files.length + fileArray.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`)
      return
    }

    const validFiles: FilePreview[] = []
    const errors: string[] = []

    fileArray.forEach(file => {
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(`${file.name}: ${validationError}`)
      } else {
        validFiles.push({
          file,
          preview: createPreview(file),
          progress: 0,
          status: 'pending'
        })
      }
    })

    if (errors.length > 0) {
      setError(errors.join('\n'))
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles])
    }
  }, [files.length, maxFiles, validateFile, createPreview])

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files)
    }
  }, [addFiles])

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files)
    }
    // Reset input so same file can be selected again
    e.target.value = ''
  }, [addFiles])

  const removeFile = useCallback((index: number) => {
    setFiles(prev => {
      const newFiles = [...prev]
      // Revoke object URL to prevent memory leak
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview)
      }
      newFiles.splice(index, 1)
      return newFiles
    })
  }, [])

  const clearAll = useCallback(() => {
    files.forEach(f => {
      if (f.preview) {
        URL.revokeObjectURL(f.preview)
      }
    })
    setFiles([])
    setError(null)
  }, [files])

  const uploadFiles = useCallback(async () => {
    if (files.length === 0) return

    setIsUploading(true)
    setError(null)
    const uploadedFiles: UploadedFile[] = []
    const errors: string[] = []

    for (let i = 0; i < files.length; i++) {
      const filePreview = files[i]
      if (filePreview.status === 'success') {
        if (filePreview.result) {
          uploadedFiles.push(filePreview.result)
        }
        continue
      }

      // Update status to uploading
      setFiles(prev => {
        const newFiles = [...prev]
        newFiles[i] = { ...newFiles[i], status: 'uploading', progress: 0 }
        return newFiles
      })

      try {
        // Simulate progress (actual progress tracking would require XMLHttpRequest)
        const progressInterval = setInterval(() => {
          setFiles(prev => {
            const newFiles = [...prev]
            if (newFiles[i] && newFiles[i].status === 'uploading' && newFiles[i].progress < 90) {
              newFiles[i] = { ...newFiles[i], progress: newFiles[i].progress + 10 }
            }
            return newFiles
          })
        }, 200)

        const result = await adsAlertService.uploadMedia(filePreview.file, folderId)
        clearInterval(progressInterval)

        const uploaded: UploadedFile = {
          id: result.id,
          filename: result.filename,
          url: result.url,
          fileType: result.file_type,
          fileSize: result.file_size
        }

        uploadedFiles.push(uploaded)

        setFiles(prev => {
          const newFiles = [...prev]
          newFiles[i] = {
            ...newFiles[i],
            status: 'success',
            progress: 100,
            result: uploaded
          }
          return newFiles
        })
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Upload failed'
        errors.push(`${filePreview.file.name}: ${errorMessage}`)

        setFiles(prev => {
          const newFiles = [...prev]
          newFiles[i] = {
            ...newFiles[i],
            status: 'error',
            progress: 0,
            error: errorMessage
          }
          return newFiles
        })
      }
    }

    setIsUploading(false)

    if (uploadedFiles.length > 0) {
      onUploadComplete?.(uploadedFiles)
    }

    if (errors.length > 0) {
      const errorMessage = errors.join('\n')
      setError(errorMessage)
      onUploadError?.(errorMessage)
    }
  }, [files, folderId, onUploadComplete, onUploadError])

  const getFileIcon = (type: string): React.ReactNode => {
    if (type.startsWith('image/')) return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    )
    if (type.startsWith('video/')) return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    )
    if (type.includes('pdf')) return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
    )
    if (type.includes('word') || type.includes('document')) return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    )
    return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
    )
  }

  const getStatusIcon = (status: string): React.ReactNode => {
    switch (status) {
      case 'success': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
      case 'error': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      )
      case 'uploading': return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )
      default: return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" strokeWidth={2} />
        </svg>
      )
    }
  }

  const pendingCount = files.filter(f => f.status === 'pending').length
  const uploadingCount = files.filter(f => f.status === 'uploading').length
  const hasFilesToUpload = pendingCount > 0 || uploadingCount > 0

  return (
    <Container>
      <DropZone
        $isDragActive={isDragActive}
        $hasFiles={files.length > 0}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={files.length === 0 ? handleClick : undefined}
      >
        {files.length === 0 ? (
          <>
            <DropIcon>📁</DropIcon>
            <DropText>Drop files here or click to browse</DropText>
            <DropSubtext>
              Supports images (JPG, PNG, GIF, WebP), videos (MP4, WebM), and documents (PDF, DOCX)
            </DropSubtext>
            <DropSubtext>
              Max {maxFileSize}MB per file, up to {maxFiles} files
            </DropSubtext>
            <BrowseButton type="button">
              Browse Files
            </BrowseButton>
          </>
        ) : (
          <PreviewList onClick={e => e.stopPropagation()}>
            {files.map((filePreview, index) => (
              <PreviewItem key={`${filePreview.file.name}-${index}`}>
                {filePreview.file.type.startsWith('image/') ? (
                  <PreviewImage src={filePreview.preview} alt={filePreview.file.name} />
                ) : filePreview.file.type.startsWith('video/') ? (
                  <PreviewVideo src={filePreview.preview} muted />
                ) : (
                  <PreviewDocument>
                    <DocumentIcon>{getFileIcon(filePreview.file.type)}</DocumentIcon>
                    <DocumentName>{filePreview.file.name}</DocumentName>
                  </PreviewDocument>
                )}

                <RemoveButton
                  type="button"
                  onClick={() => removeFile(index)}
                  disabled={filePreview.status === 'uploading'}
                >
                  ✕
                </RemoveButton>

                <StatusBadge $status={filePreview.status}>
                  {getStatusIcon(filePreview.status)}
                </StatusBadge>

                {filePreview.status === 'uploading' && (
                  <ProgressOverlay>
                    <ProgressBar $progress={filePreview.progress} />
                  </ProgressOverlay>
                )}
              </PreviewItem>
            ))}

            {/* Add more button */}
            {files.length < maxFiles && (
              <PreviewItem
                as="button"
                type="button"
                onClick={handleClick}
                style={{
                  border: '2px dashed #d1d5db',
                  background: 'transparent',
                  cursor: 'pointer'
                }}
              >
                <PreviewDocument>
                  <DocumentIcon style={{ color: '#9ca3af' }}>+</DocumentIcon>
                  <DocumentName style={{ color: '#9ca3af' }}>Add more</DocumentName>
                </PreviewDocument>
              </PreviewItem>
            )}
          </PreviewList>
        )}
      </DropZone>

      <HiddenInput
        ref={fileInputRef}
        type="file"
        multiple
        accept={ALLOWED_TYPES.join(',')}
        onChange={handleFileSelect}
      />

      {error && (
        <ErrorMessage>
          {error.split('\n').map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </ErrorMessage>
      )}

      {files.length > 0 && (
        <UploadActions>
          <ActionButton
            type="button"
            $variant="secondary"
            onClick={clearAll}
            disabled={isUploading}
          >
            Clear All
          </ActionButton>
          <ActionButton
            type="button"
            $variant="primary"
            onClick={uploadFiles}
            disabled={!hasFilesToUpload || isUploading}
          >
            {isUploading
              ? `Uploading (${uploadingCount}/${files.length})...`
              : `Upload ${pendingCount} File${pendingCount !== 1 ? 's' : ''}`
            }
          </ActionButton>
        </UploadActions>
      )}
    </Container>
  )
}

export default MediaUploader
