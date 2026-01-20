// frontend/src/components/dashboard/ads-alert/PromotionForm.tsx
import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import {
  Promotion, PromotionCreate, PromotionUpdate,
  Chat, MediaFile
} from '../../../types/adsAlert'
import MediaBrowser from './MediaBrowser'
import MediaUploader from './MediaUploader'

interface PromotionFormProps {
  promotion?: Promotion
  onSave?: (promotion: Promotion) => void
  onCancel?: () => void
}

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px;
`

const FormSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const Label = styled.label`
  font-weight: 600;
  font-size: 14px;
  color: #374151;
`

const Input = styled.input`
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: #4A90E2;
    box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
  }
`

const TextArea = styled.textarea`
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  min-height: 120px;
  resize: vertical;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #4A90E2;
    box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
  }
`

const TabContainer = styled.div`
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 16px;
`

const Tab = styled.button<{ $active: boolean }>`
  padding: 10px 20px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: ${props => props.$active ? '#4A90E2' : '#6b7280'};
  border-bottom: 2px solid ${props => props.$active ? '#4A90E2' : 'transparent'};
  margin-bottom: -1px;
  transition: all 0.2s;

  &:hover {
    color: #4A90E2;
  }
`

const SelectedMedia = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
`

const MediaChip = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 20px;
  font-size: 13px;
  color: #4b5563;
`

const MediaChipImage = styled.img`
  width: 24px;
  height: 24px;
  border-radius: 4px;
  object-fit: cover;
`

const MediaChipIcon = styled.span`
  font-size: 14px;
`

const RemoveMediaButton = styled.button`
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  padding: 2px;
  font-size: 14px;
  line-height: 1;

  &:hover {
    color: #ef4444;
  }
`

const RadioGroup = styled.div`
  display: flex;
  gap: 24px;
`

const RadioLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
`

const RadioInput = styled.input`
  width: 18px;
  height: 18px;
  accent-color: #4A90E2;
`

const ChatSelector = styled.div`
  border: 1px solid #d1d5db;
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
`

const ChatItem = styled.label`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #e5e7eb;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #f9fafb;
  }
`

const Checkbox = styled.input`
  width: 18px;
  height: 18px;
  accent-color: #4A90E2;
`

const ChatInfo = styled.div`
  flex: 1;
`

const ChatName = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: #374151;
`

const ChatId = styled.div`
  font-size: 12px;
  color: #9ca3af;
`

const ScheduleContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

const DateTimeInput = styled.input`
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: #4A90E2;
  }

  &:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }
`

const Actions = styled.div`
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  ${props => {
    switch (props.$variant) {
      case 'primary':
        return `
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
        `
      case 'danger':
        return `
          background: #ef4444;
          color: white;
          border: none;

          &:hover:not(:disabled) {
            background: #dc2626;
          }
        `
      default:
        return `
          background: white;
          color: #6b7280;
          border: 1px solid #d1d5db;

          &:hover {
            background: #f3f4f6;
          }
        `
    }
  }}
`

const ErrorMessage = styled.div`
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
`

const SuccessMessage = styled.div`
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #16a34a;
  font-size: 14px;
`

type MediaSourceTab = 'browse' | 'upload'

const PromotionForm: React.FC<PromotionFormProps> = ({
  promotion,
  onSave,
  onCancel
}) => {
  const [title, setTitle] = useState(promotion?.title || '')
  const [content, setContent] = useState(promotion?.content || '')
  const [selectedMedia, setSelectedMedia] = useState<MediaFile[]>([])
  const [targetType, setTargetType] = useState<'all' | 'selected'>(
    promotion?.target_type || 'all'
  )
  const [selectedChatIds, setSelectedChatIds] = useState<string[]>(
    promotion?.target_chat_ids || []
  )
  const [scheduleEnabled, setScheduleEnabled] = useState(!!promotion?.scheduled_at)
  const [scheduledAt, setScheduledAt] = useState(
    promotion?.scheduled_at ? new Date(promotion.scheduled_at).toISOString().slice(0, 16) : ''
  )
  const [mediaTab, setMediaTab] = useState<MediaSourceTab>('browse')
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Load chats for targeting
  useEffect(() => {
    const loadChats = async () => {
      try {
        const loadedChats = await adsAlertService.listChats({ subscribed: true })
        setChats(loadedChats)
      } catch (err) {
        console.error('Failed to load chats:', err)
      }
    }
    loadChats()
  }, [])

  // Load existing media if editing
  useEffect(() => {
    if (promotion?.media_urls && promotion.media_urls.length > 0) {
      // Convert URLs to MediaFile objects (simplified)
      const existingMedia: MediaFile[] = promotion.media_urls.map((url, index) => ({
        id: `existing-${index}`,
        tenant_id: '',
        folder_id: null,
        filename: url.split('/').pop() || `media-${index}`,
        original_filename: null,
        storage_path: url,
        url: url,
        file_type: url.includes('.mp4') ? 'video/mp4' :
                   url.includes('.pdf') ? 'application/pdf' : 'image/jpeg',
        file_size: null,
        thumbnail_url: null,
        width: null,
        height: null,
        duration: null,
        created_by: null,
        created_at: new Date().toISOString()
      }))
      setSelectedMedia(existingMedia)
    }
  }, [promotion])

  const handleMediaSelect = (files: MediaFile[]) => {
    setSelectedMedia(prev => {
      // Add new files, avoiding duplicates
      const existingIds = new Set(prev.map(f => f.id))
      const newFiles = files.filter(f => !existingIds.has(f.id))
      return [...prev, ...newFiles]
    })
  }

  const handleUploadComplete = (files: { id: string; filename: string; url: string; fileType: string; fileSize: number }[]) => {
    const mediaFiles: MediaFile[] = files.map(f => ({
      id: f.id,
      tenant_id: '',
      folder_id: null,
      filename: f.filename,
      original_filename: f.filename,
      storage_path: f.url,
      url: f.url,
      file_type: f.fileType,
      file_size: f.fileSize,
      thumbnail_url: null,
      width: null,
      height: null,
      duration: null,
      created_by: null,
      created_at: new Date().toISOString()
    }))
    setSelectedMedia(prev => [...prev, ...mediaFiles])
  }

  const removeMedia = (id: string) => {
    setSelectedMedia(prev => prev.filter(f => f.id !== id))
  }

  const toggleChat = (chatId: string) => {
    setSelectedChatIds(prev => {
      if (prev.includes(chatId)) {
        return prev.filter(id => id !== chatId)
      }
      return [...prev, chatId]
    })
  }

  const determineMediaType = (): 'text' | 'image' | 'video' | 'document' | 'mixed' => {
    if (selectedMedia.length === 0) return 'text'

    const types = selectedMedia.map(f => adsAlertService.getMediaCategory(f.file_type))
    const uniqueTypes = [...new Set(types)]

    if (uniqueTypes.length > 1) return 'mixed'
    return uniqueTypes[0] as 'image' | 'video' | 'document'
  }

  const handleSubmit = async (action: 'save' | 'send' | 'schedule') => {
    setError(null)
    setSuccess(null)

    if (!title.trim()) {
      setError('Title is required')
      return
    }

    if (!content.trim() && selectedMedia.length === 0) {
      setError('Please add content or media')
      return
    }

    if (targetType === 'selected' && selectedChatIds.length === 0) {
      setError('Please select at least one chat')
      return
    }

    if (action === 'schedule' && !scheduledAt) {
      setError('Please select a schedule date and time')
      return
    }

    setLoading(true)

    try {
      const data: PromotionCreate | PromotionUpdate = {
        title: title.trim(),
        content: content.trim() || undefined,
        media_urls: selectedMedia.map(f => f.url),
        media_type: determineMediaType(),
        target_type: targetType,
        target_chat_ids: targetType === 'selected' ? selectedChatIds : [],
        scheduled_at: action === 'schedule' ? new Date(scheduledAt).toISOString() : undefined
      }

      let savedPromotion: Promotion

      if (promotion) {
        // Update existing
        savedPromotion = await adsAlertService.updatePromotion(promotion.id, data as PromotionUpdate)
      } else {
        // Create new
        savedPromotion = await adsAlertService.createPromotion(data as PromotionCreate)
      }

      // Handle action
      if (action === 'send') {
        const result = await adsAlertService.sendPromotion(savedPromotion.id)
        setSuccess(`Promotion sent successfully! ${result.sent} of ${result.total} messages delivered.`)
      } else if (action === 'schedule') {
        await adsAlertService.schedulePromotion(savedPromotion.id, {
          scheduled_at: new Date(scheduledAt).toISOString()
        })
        setSuccess('Promotion scheduled successfully!')
      } else {
        setSuccess('Promotion saved as draft!')
      }

      onSave?.(savedPromotion)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save promotion')
    } finally {
      setLoading(false)
    }
  }

  const getMediaIcon = (type: string): string => {
    if (type.startsWith('image/')) return '🖼️'
    if (type.startsWith('video/')) return '🎬'
    if (type.includes('pdf')) return '📄'
    return '📁'
  }

  return (
    <Form onSubmit={(e) => e.preventDefault()}>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}

      <FormSection>
        <Label>Title *</Label>
        <Input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter promotion title..."
          maxLength={255}
        />
      </FormSection>

      <FormSection>
        <Label>Content</Label>
        <TextArea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Enter promotion content..."
        />
      </FormSection>

      <FormSection>
        <Label>Media</Label>
        <TabContainer>
          <Tab
            type="button"
            $active={mediaTab === 'browse'}
            onClick={() => setMediaTab('browse')}
          >
            📁 Browse Files
          </Tab>
          <Tab
            type="button"
            $active={mediaTab === 'upload'}
            onClick={() => setMediaTab('upload')}
          >
            📤 Upload New
          </Tab>
        </TabContainer>

        {mediaTab === 'browse' ? (
          <MediaBrowser
            onSelect={handleMediaSelect}
            multiSelect
            selectedIds={selectedMedia.map(f => f.id)}
          />
        ) : (
          <MediaUploader
            onUploadComplete={handleUploadComplete}
            onUploadError={(err) => setError(err)}
          />
        )}

        {selectedMedia.length > 0 && (
          <SelectedMedia>
            {selectedMedia.map(file => (
              <MediaChip key={file.id}>
                {file.file_type.startsWith('image/') ? (
                  <MediaChipImage src={file.thumbnail_url || file.url} alt="" />
                ) : (
                  <MediaChipIcon>{getMediaIcon(file.file_type)}</MediaChipIcon>
                )}
                <span>{file.original_filename || file.filename}</span>
                <RemoveMediaButton
                  type="button"
                  onClick={() => removeMedia(file.id)}
                >
                  ✕
                </RemoveMediaButton>
              </MediaChip>
            ))}
          </SelectedMedia>
        )}
      </FormSection>

      <FormSection>
        <Label>Target Audience</Label>
        <RadioGroup>
          <RadioLabel>
            <RadioInput
              type="radio"
              name="targetType"
              checked={targetType === 'all'}
              onChange={() => setTargetType('all')}
            />
            All Subscribers
          </RadioLabel>
          <RadioLabel>
            <RadioInput
              type="radio"
              name="targetType"
              checked={targetType === 'selected'}
              onChange={() => setTargetType('selected')}
            />
            Selected Chats
          </RadioLabel>
        </RadioGroup>

        {targetType === 'selected' && (
          <ChatSelector>
            {chats.length === 0 ? (
              <ChatItem as="div">
                <span style={{ color: '#9ca3af' }}>No subscribed chats available</span>
              </ChatItem>
            ) : (
              chats.map(chat => (
                <ChatItem key={chat.id}>
                  <Checkbox
                    type="checkbox"
                    checked={selectedChatIds.includes(chat.id)}
                    onChange={() => toggleChat(chat.id)}
                  />
                  <ChatInfo>
                    <ChatName>{chat.customer_name || chat.chat_name || 'Unknown'}</ChatName>
                    <ChatId>{chat.platform}: {chat.chat_id}</ChatId>
                  </ChatInfo>
                </ChatItem>
              ))
            )}
          </ChatSelector>
        )}
      </FormSection>

      <FormSection>
        <Label>Schedule</Label>
        <ScheduleContainer>
          <RadioLabel>
            <Checkbox
              type="checkbox"
              checked={scheduleEnabled}
              onChange={(e) => setScheduleEnabled(e.target.checked)}
            />
            Schedule for later
          </RadioLabel>
          <DateTimeInput
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            disabled={!scheduleEnabled}
            min={new Date().toISOString().slice(0, 16)}
          />
        </ScheduleContainer>
      </FormSection>

      <Actions>
        {onCancel && (
          <Button type="button" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button
          type="button"
          onClick={() => handleSubmit('save')}
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save Draft'}
        </Button>
        {scheduleEnabled ? (
          <Button
            type="button"
            $variant="primary"
            onClick={() => handleSubmit('schedule')}
            disabled={loading || !scheduledAt}
          >
            {loading ? 'Scheduling...' : 'Schedule'}
          </Button>
        ) : (
          <Button
            type="button"
            $variant="primary"
            onClick={() => handleSubmit('send')}
            disabled={loading}
          >
            {loading ? 'Sending...' : 'Send Now'}
          </Button>
        )}
      </Actions>
    </Form>
  )
}

export default PromotionForm
