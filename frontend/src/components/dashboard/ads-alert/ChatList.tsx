// frontend/src/components/dashboard/ads-alert/ChatList.tsx
import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import { adsAlertService } from '../../../services/adsAlertApi'
import { Chat, ChatCreate, ChatUpdate } from '../../../types/adsAlert'

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`

const Title = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const AddButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
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

const SearchBar = styled.input`
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  width: 100%;
  max-width: 300px;

  &:focus {
    outline: none;
    border-color: #4A90E2;
  }
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
`

const Th = styled.th`
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
`

const Td = styled.td`
  padding: 12px 16px;
  font-size: 14px;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
`

const Tr = styled.tr`
  &:hover {
    background: #f9fafb;
  }

  &:last-child td {
    border-bottom: none;
  }
`

const ChatName = styled.div`
  font-weight: 500;
  color: #1f2937;
`

const ChatId = styled.div`
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
`

const StatusBadge = styled.span<{ $subscribed: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: ${props => props.$subscribed ? '#d1fae5' : '#f3f4f6'};
  color: ${props => props.$subscribed ? '#059669' : '#6b7280'};
`

const TagList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
`

const Tag = styled.span`
  padding: 2px 8px;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 10px;
  font-size: 11px;
`

const Actions = styled.div`
  display: flex;
  gap: 8px;
`

const ActionButton = styled.button<{ $variant?: 'danger' }>`
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;

  ${props => props.$variant === 'danger' ? `
    background: white;
    color: #dc2626;
    border: 1px solid #fecaca;

    &:hover {
      background: #fef2f2;
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

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px;
  color: #9ca3af;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
`

const EmptyIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
`

const EmptyText = styled.p`
  font-size: 14px;
  margin: 0;
`

// Modal styles
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
  padding: 24px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
`

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`

const ModalTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const CloseButton = styled.button`
  background: transparent;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;

  &:hover {
    color: #6b7280;
  }
`

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 16px;
`

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`

const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
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
  }
`

const TagInput = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  min-height: 42px;

  &:focus-within {
    border-color: #4A90E2;
  }
`

const TagInputField = styled.input`
  border: none;
  outline: none;
  flex: 1;
  min-width: 100px;
  font-size: 14px;
`

const RemovableTag = styled.span`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 10px;
  font-size: 12px;
`

const RemoveTagButton = styled.button`
  background: transparent;
  border: none;
  padding: 0;
  color: #6366f1;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;

  &:hover {
    color: #4338ca;
  }
`

const Checkbox = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
`

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
`

const Button = styled.button<{ $variant?: 'primary' }>`
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

interface ChatFormData {
  chat_id: string
  chat_name: string
  customer_name: string
  tags: string[]
  subscribed: boolean
}

const ChatList: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingChat, setEditingChat] = useState<Chat | null>(null)
  const [formData, setFormData] = useState<ChatFormData>({
    chat_id: '',
    chat_name: '',
    customer_name: '',
    tags: [],
    subscribed: true
  })
  const [tagInput, setTagInput] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    setLoading(true)
    try {
      const data = await adsAlertService.listChats()
      setChats(data)
    } catch (error) {
      console.error('Failed to load chats:', error)
    } finally {
      setLoading(false)
    }
  }

  const openAddModal = () => {
    setEditingChat(null)
    setFormData({
      chat_id: '',
      chat_name: '',
      customer_name: '',
      tags: [],
      subscribed: true
    })
    setTagInput('')
    setShowModal(true)
  }

  const openEditModal = (chat: Chat) => {
    setEditingChat(chat)
    setFormData({
      chat_id: chat.chat_id,
      chat_name: chat.chat_name || '',
      customer_name: chat.customer_name || '',
      tags: chat.tags || [],
      subscribed: chat.subscribed
    })
    setTagInput('')
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingChat(null)
  }

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const tag = tagInput.trim()
      if (tag && !formData.tags.includes(tag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, tag]
        }))
      }
      setTagInput('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tagToRemove)
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.chat_id.trim()) return

    setSaving(true)
    try {
      if (editingChat) {
        const updateData: ChatUpdate = {
          chat_name: formData.chat_name || undefined,
          customer_name: formData.customer_name || undefined,
          tags: formData.tags,
          subscribed: formData.subscribed
        }
        await adsAlertService.updateChat(editingChat.id, updateData)
      } else {
        const createData: ChatCreate = {
          platform: 'telegram',
          chat_id: formData.chat_id,
          chat_name: formData.chat_name || undefined,
          customer_name: formData.customer_name || undefined,
          tags: formData.tags
        }
        await adsAlertService.createChat(createData)
      }
      closeModal()
      loadChats()
    } catch (error) {
      console.error('Failed to save chat:', error)
      alert('Failed to save chat')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (chat: Chat) => {
    if (!confirm(`Delete chat "${chat.customer_name || chat.chat_name || chat.chat_id}"?`)) return

    try {
      await adsAlertService.deleteChat(chat.id)
      loadChats()
    } catch (error) {
      console.error('Failed to delete chat:', error)
      alert('Failed to delete chat')
    }
  }

  const toggleSubscription = async (chat: Chat) => {
    try {
      await adsAlertService.updateChat(chat.id, { subscribed: !chat.subscribed })
      loadChats()
    } catch (error) {
      console.error('Failed to update subscription:', error)
    }
  }

  const filteredChats = searchQuery
    ? chats.filter(chat =>
        (chat.customer_name?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (chat.chat_name?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        chat.chat_id.includes(searchQuery)
      )
    : chats

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <Container>
      <Header>
        <Title>Registered Chats ({chats.length})</Title>
        <div style={{ display: 'flex', gap: '12px' }}>
          <SearchBar
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <AddButton onClick={openAddModal}>
            + Add Chat
          </AddButton>
        </div>
      </Header>

      {loading ? (
        <EmptyState>
          <EmptyText>Loading chats...</EmptyText>
        </EmptyState>
      ) : filteredChats.length === 0 ? (
        <EmptyState>
          <EmptyIcon>💬</EmptyIcon>
          <EmptyText>
            {searchQuery ? 'No chats match your search' : 'No chats registered yet'}
          </EmptyText>
        </EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Chat</Th>
              <Th>Customer</Th>
              <Th>Tags</Th>
              <Th>Status</Th>
              <Th>Added</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {filteredChats.map(chat => (
              <Tr key={chat.id}>
                <Td>
                  <ChatName>{chat.chat_name || 'Unnamed Chat'}</ChatName>
                  <ChatId>{chat.platform}: {chat.chat_id}</ChatId>
                </Td>
                <Td>{chat.customer_name || '-'}</Td>
                <Td>
                  {chat.tags && chat.tags.length > 0 ? (
                    <TagList>
                      {chat.tags.map(tag => (
                        <Tag key={tag}>{tag}</Tag>
                      ))}
                    </TagList>
                  ) : '-'}
                </Td>
                <Td>
                  <StatusBadge
                    $subscribed={chat.subscribed}
                    onClick={() => toggleSubscription(chat)}
                    style={{ cursor: 'pointer' }}
                  >
                    {chat.subscribed ? '✓ Subscribed' : 'Unsubscribed'}
                  </StatusBadge>
                </Td>
                <Td>{formatDate(chat.created_at)}</Td>
                <Td>
                  <Actions>
                    <ActionButton onClick={() => openEditModal(chat)}>
                      Edit
                    </ActionButton>
                    <ActionButton $variant="danger" onClick={() => handleDelete(chat)}>
                      Delete
                    </ActionButton>
                  </Actions>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}

      {showModal && (
        <Modal onClick={closeModal}>
          <ModalContent onClick={e => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>{editingChat ? 'Edit Chat' : 'Add Chat'}</ModalTitle>
              <CloseButton onClick={closeModal}>&times;</CloseButton>
            </ModalHeader>

            <Form onSubmit={handleSubmit}>
              <FormGroup>
                <Label>Telegram Chat ID *</Label>
                <Input
                  type="text"
                  value={formData.chat_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, chat_id: e.target.value }))}
                  placeholder="e.g., 123456789"
                  disabled={!!editingChat}
                  required
                />
              </FormGroup>

              <FormGroup>
                <Label>Chat Name</Label>
                <Input
                  type="text"
                  value={formData.chat_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, chat_name: e.target.value }))}
                  placeholder="e.g., Main Group"
                />
              </FormGroup>

              <FormGroup>
                <Label>Customer Name</Label>
                <Input
                  type="text"
                  value={formData.customer_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, customer_name: e.target.value }))}
                  placeholder="e.g., John Doe"
                />
              </FormGroup>

              <FormGroup>
                <Label>Tags (press Enter to add)</Label>
                <TagInput>
                  {formData.tags.map(tag => (
                    <RemovableTag key={tag}>
                      {tag}
                      <RemoveTagButton type="button" onClick={() => removeTag(tag)}>
                        &times;
                      </RemoveTagButton>
                    </RemovableTag>
                  ))}
                  <TagInputField
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleTagKeyDown}
                    placeholder="Add tags..."
                  />
                </TagInput>
              </FormGroup>

              <Checkbox>
                <input
                  type="checkbox"
                  checked={formData.subscribed}
                  onChange={(e) => setFormData(prev => ({ ...prev, subscribed: e.target.checked }))}
                />
                Subscribed to promotions
              </Checkbox>

              <ModalActions>
                <Button type="button" onClick={closeModal}>
                  Cancel
                </Button>
                <Button type="submit" $variant="primary" disabled={saving}>
                  {saving ? 'Saving...' : editingChat ? 'Update' : 'Add Chat'}
                </Button>
              </ModalActions>
            </Form>
          </ModalContent>
        </Modal>
      )}
    </Container>
  )
}

export default ChatList
