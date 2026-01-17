import React, { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'
import { QRCodeSVG } from 'qrcode.react'
import { RegisteredClient, ClientLinkCodeResponse } from '../../../types/invoice'

interface QRCodeModalProps {
  isOpen: boolean
  onClose: () => void
  client: RegisteredClient | null
  linkCode: ClientLinkCodeResponse | null
  onRegenerate: () => Promise<void>
  isGenerating: boolean
}

// Styled Components
const ModalOverlay = styled.div<{ isOpen: boolean }>`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: ${props => props.isOpen ? 1 : 0};
  visibility: ${props => props.isOpen ? 'visible' : 'hidden'};
  transition: opacity 0.2s ease, visibility 0.2s ease;
`

const ModalContent = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  max-width: 420px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
`

const TitleSection = styled.div``

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
`

const Subtitle = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

const CloseButton = styled.button`
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: #9ca3af;
  transition: color 0.2s ease;

  &:hover {
    color: #1f2937;
  }
`

const ClientName = styled.div`
  text-align: center;
  margin-bottom: 1.5rem;
`

const ClientNameText = styled.span`
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  background: #f3f4f6;
  padding: 0.5rem 1rem;
  border-radius: 8px;
`

const QRContainer = styled.div`
  display: flex;
  justify-content: center;
  padding: 1.5rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 1rem;
`

const Instructions = styled.div`
  text-align: center;
  margin-bottom: 1rem;
`

const InstructionText = styled.p`
  font-size: 0.875rem;
  color: #4b5563;
  margin: 0 0 0.25rem 0;
`

const InstructionTextKm = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

const ExpiryContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
`

const ExpiryLabel = styled.span`
  font-size: 0.75rem;
  color: #6b7280;
`

const ExpiryTime = styled.span<{ isExpired?: boolean }>`
  font-size: 0.875rem;
  font-weight: 600;
  color: ${props => props.isExpired ? '#ef4444' : '#f59e0b'};
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.75rem;
`

const ActionButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${props => props.variant === 'primary' ? '#4a90e2' : '#f3f4f6'};
  color: ${props => props.variant === 'primary' ? 'white' : '#1f2937'};

  &:hover {
    background: ${props => props.variant === 'primary' ? '#2a5298' : '#e5e7eb'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const CopiedBadge = styled.span`
  font-size: 0.75rem;
  color: #10b981;
  background: #d1fae5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
`

const StepsContainer = styled.div`
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
`

const StepsTitle = styled.h4`
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.75rem 0;
`

const StepsList = styled.ol`
  margin: 0;
  padding-left: 1.25rem;
`

const Step = styled.li`
  font-size: 0.875rem;
  color: #4b5563;
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
`

const Spinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

const LoadingText = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

const AlreadyLinked = styled.div`
  text-align: center;
  padding: 2rem 1rem;
`

const LinkedIcon = styled.div`
  width: 64px;
  height: 64px;
  background: #d1fae5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: #10b981;
`

const LinkedText = styled.p`
  font-size: 1rem;
  font-weight: 500;
  color: #10b981;
  margin: 0 0 0.5rem 0;
`

const LinkedUsername = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

const QRCodeModal: React.FC<QRCodeModalProps> = ({
  isOpen,
  onClose,
  client,
  linkCode,
  onRegenerate,
  isGenerating
}) => {
  const { t } = useTranslation()
  const qrRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState<string | null>(null)
  const [isExpired, setIsExpired] = useState(false)

  // Calculate time remaining
  useEffect(() => {
    if (!linkCode?.expires_at) {
      setTimeRemaining(null)
      return
    }

    const updateTimer = () => {
      const now = new Date().getTime()
      const expiry = new Date(linkCode.expires_at!).getTime()
      const diff = expiry - now

      if (diff <= 0) {
        setTimeRemaining(null)
        setIsExpired(true)
        return
      }

      setIsExpired(false)
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((diff % (1000 * 60)) / 1000)

      if (hours > 0) {
        setTimeRemaining(`${hours}h ${minutes}m`)
      } else if (minutes > 0) {
        setTimeRemaining(`${minutes}m ${seconds}s`)
      } else {
        setTimeRemaining(`${seconds}s`)
      }
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)
    return () => clearInterval(interval)
  }, [linkCode?.expires_at])

  // Copy link to clipboard
  const copyToClipboard = async () => {
    if (!linkCode?.link) return

    try {
      await navigator.clipboard.writeText(linkCode.link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Download QR code as PNG
  const downloadQR = () => {
    if (!qrRef.current || !client) return

    const svg = qrRef.current.querySelector('svg')
    if (!svg) return

    const svgData = new XMLSerializer().serializeToString(svg)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      canvas.width = 400
      canvas.height = 400
      ctx?.drawImage(img, 0, 0, 400, 400)

      const pngFile = canvas.toDataURL('image/png')
      const downloadLink = document.createElement('a')
      downloadLink.download = `qr-${client.name.replace(/\s+/g, '-')}.png`
      downloadLink.href = pngFile
      downloadLink.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  // Close on escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  if (!client) return null

  // If client is already linked
  if (client.telegram_linked) {
    return (
      <ModalOverlay isOpen={isOpen} onClick={onClose}>
        <ModalContent onClick={e => e.stopPropagation()}>
          <Header>
            <TitleSection>
              <Title>{t('qrModal.title')}</Title>
            </TitleSection>
            <CloseButton onClick={onClose}>
              <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </CloseButton>
          </Header>

          <AlreadyLinked>
            <LinkedIcon>
              <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </LinkedIcon>
            <LinkedText>Already Connected</LinkedText>
            <LinkedUsername>@{client.telegram_username}</LinkedUsername>
          </AlreadyLinked>
        </ModalContent>
      </ModalOverlay>
    )
  }

  return (
    <ModalOverlay isOpen={isOpen} onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <Header>
          <TitleSection>
            <Title>{t('qrModal.title')}</Title>
            <Subtitle>{t('qrModal.subtitle')}</Subtitle>
          </TitleSection>
          <CloseButton onClick={onClose}>
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </CloseButton>
        </Header>

        <ClientName>
          <ClientNameText>{client.name}</ClientNameText>
        </ClientName>

        {isGenerating ? (
          <LoadingContainer>
            <Spinner />
            <LoadingText>{t('qrModal.generating')}</LoadingText>
          </LoadingContainer>
        ) : linkCode ? (
          <>
            <QRContainer ref={qrRef}>
              <QRCodeSVG
                value={linkCode.link}
                size={200}
                level="H"
                includeMargin={true}
              />
            </QRContainer>

            <Instructions>
              <InstructionText>{t('qrModal.scanInstructions')}</InstructionText>
              <InstructionTextKm>{t('qrModal.scanInstructionsKm')}</InstructionTextKm>
            </Instructions>

            <ExpiryContainer>
              <ExpiryLabel>{isExpired ? t('qrModal.expired') : t('qrModal.expiresIn')}:</ExpiryLabel>
              {isExpired ? (
                <ExpiryTime isExpired>-</ExpiryTime>
              ) : (
                <ExpiryTime>{timeRemaining}</ExpiryTime>
              )}
            </ExpiryContainer>

            <ButtonGroup>
              <ActionButton onClick={downloadQR}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {t('qrModal.downloadQR')}
              </ActionButton>
              <ActionButton onClick={copyToClipboard}>
                {copied ? (
                  <CopiedBadge>{t('common.copied')}</CopiedBadge>
                ) : (
                  <>
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    {t('qrModal.copyLink')}
                  </>
                )}
              </ActionButton>
            </ButtonGroup>

            {isExpired && (
              <ActionButton
                variant="primary"
                onClick={onRegenerate}
                disabled={isGenerating}
                style={{ marginTop: '0.75rem', width: '100%' }}
              >
                {t('qrModal.regenerate')}
              </ActionButton>
            )}

            <StepsContainer>
              <StepsTitle>How to link</StepsTitle>
              <StepsList>
                <Step>{t('qrModal.instructions.step1')}</Step>
                <Step>{t('qrModal.instructions.step2')}</Step>
                <Step>{t('qrModal.instructions.step3')}</Step>
                <Step>{t('qrModal.instructions.step4')}</Step>
              </StepsList>
            </StepsContainer>
          </>
        ) : (
          <LoadingContainer>
            <LoadingText>Loading...</LoadingText>
          </LoadingContainer>
        )}
      </ModalContent>
    </ModalOverlay>
  )
}

export default QRCodeModal
