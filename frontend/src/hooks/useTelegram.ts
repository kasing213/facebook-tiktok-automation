import { useState, useEffect, useCallback } from 'react'
import { telegramService } from '../services/api'

interface TelegramStatus {
  connected: boolean
  telegram_user_id?: string
  telegram_username?: string
  linked_at?: string
}

interface LinkCodeData {
  code: string
  expires_at: string
  bot_url: string
  deep_link: string
}

export function useTelegram() {
  const [status, setStatus] = useState<TelegramStatus | null>(null)
  const [linkCode, setLinkCode] = useState<LinkCodeData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  // Fetch Telegram status
  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await telegramService.getStatus()
      setStatus(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch Telegram status')
    } finally {
      setLoading(false)
    }
  }, [])

  // Generate link code
  const generateLinkCode = useCallback(async () => {
    setGenerating(true)
    setError(null)
    try {
      const data = await telegramService.generateLinkCode()
      setLinkCode(data)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to generate link code')
      throw err
    } finally {
      setGenerating(false)
    }
  }, [])

  // Disconnect Telegram
  const disconnect = useCallback(async () => {
    setDisconnecting(true)
    setError(null)
    try {
      await telegramService.disconnect()
      setStatus({ connected: false })
      setLinkCode(null)
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect Telegram')
      throw err
    } finally {
      setDisconnecting(false)
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Fetch status on mount
  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  return {
    status,
    linkCode,
    loading,
    error,
    generating,
    disconnecting,
    fetchStatus,
    generateLinkCode,
    disconnect,
    clearError,
  }
}

export default useTelegram
