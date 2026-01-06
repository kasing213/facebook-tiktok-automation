import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../../../hooks/useTelegram'
import { LoadingSpinner } from '../../LoadingSpinner'
import {
  Container,
  Header,
  BackButton,
  IntegrationCard,
  CardHeader,
  PlatformName,
  StatusBadge,
  Description,
  TokenMeta,
  TelegramButton,
  DisconnectButton,
  LinkCodeBox,
  LinkCode,
  DeepLinkButton,
  ExpiryText,
  ErrorText,
  SuccessMessage,
  InfoText
} from './shared/styles'

const TelegramIntegrationPage: React.FC = () => {
  const navigate = useNavigate()
  const [successMessage, setSuccessMessage] = useState<string>('')

  const {
    status: telegramStatus,
    linkCode,
    generating: telegramGenerating,
    disconnecting: telegramDisconnecting,
    error: telegramError,
    generateLinkCode,
    disconnect: disconnectTelegram,
    clearError: clearTelegramError
  } = useTelegram()

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  const handleConnectTelegram = async () => {
    clearTelegramError()
    try {
      await generateLinkCode()
    } catch (error) {
      console.error('Failed to generate Telegram link code:', error)
    }
  }

  const handleDisconnectTelegram = async () => {
    clearTelegramError()
    try {
      await disconnectTelegram()
      setSuccessMessage('Telegram account disconnected successfully!')
    } catch (error) {
      console.error('Failed to disconnect Telegram:', error)
    }
  }

  const isConnected = telegramStatus?.connected || false

  return (
    <Container>
      <Header>
        <BackButton onClick={() => navigate('/dashboard/integrations')}>
          ← Back to Integrations
        </BackButton>
      </Header>

      {successMessage && <SuccessMessage>{successMessage}</SuccessMessage>}

      <IntegrationCard connected={isConnected}>
        <CardHeader>
          <PlatformName>Telegram Integration</PlatformName>
          <StatusBadge connected={isConnected}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </StatusBadge>
        </CardHeader>

        <Description>
          Connect your Telegram account to receive notifications, run commands, and interact with the platform via bot.
          Get instant alerts for important events and manage your automations directly from Telegram.
        </Description>

        {isConnected && telegramStatus && (
          <div>
            <InfoText>
              Connected as @{telegramStatus.telegram_username || telegramStatus.telegram_user_id}
            </InfoText>
            {telegramStatus.linked_at && (
              <TokenMeta>
                Linked: {new Date(telegramStatus.linked_at).toLocaleDateString()}
              </TokenMeta>
            )}
            <DisconnectButton
              onClick={handleDisconnectTelegram}
              disabled={telegramDisconnecting}
            >
              {telegramDisconnecting ? 'Disconnecting...' : 'Disconnect Telegram'}
            </DisconnectButton>
          </div>
        )}

        {!isConnected && !linkCode && (
          <TelegramButton
            onClick={handleConnectTelegram}
            disabled={telegramGenerating}
          >
            {telegramGenerating ? (
              <>
                <LoadingSpinner size="small" />
                Generating...
              </>
            ) : (
              'Connect Telegram'
            )}
          </TelegramButton>
        )}

        {!isConnected && linkCode && (
          <LinkCodeBox>
            <p style={{ margin: 0, fontSize: '0.9375rem', color: '#6b7280' }}>
              Click the button below or send this code to the bot:
            </p>
            <LinkCode>{linkCode.code}</LinkCode>
            <DeepLinkButton
              href={linkCode.deep_link}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open Telegram Bot
            </DeepLinkButton>
            <ExpiryText>
              Code expires: {new Date(linkCode.expires_at).toLocaleTimeString()}
            </ExpiryText>
          </LinkCodeBox>
        )}

        {telegramError && (
          <ErrorText>Error: {telegramError}</ErrorText>
        )}
      </IntegrationCard>
    </Container>
  )
}

export default TelegramIntegrationPage
