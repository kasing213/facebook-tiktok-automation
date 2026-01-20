import React, { useState, useEffect, useRef } from 'react'
import styled from 'styled-components'
import { QRCodeSVG } from 'qrcode.react'
import { BatchCodeResponse } from '../../../services/invoiceApi'

interface BatchQRModalProps {
  isOpen: boolean
  onClose: () => void
  onGenerate: (data: {
    batch_name?: string
    max_uses?: number | null
    expires_days?: number | null
  }) => Promise<BatchCodeResponse>
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
  max-width: 480px;
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

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
`

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`

const Label = styled.label`
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
`

const Input = styled.input`
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #1f2937;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  }

  &::placeholder {
    color: #9ca3af;
  }
`

const Select = styled.select`
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #1f2937;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  }
`

const InfoBox = styled.div`
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: #eff6ff;
  border-radius: 8px;
  border: 1px solid #bfdbfe;
`

const InfoIcon = styled.div`
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: #3b82f6;
`

const InfoText = styled.p`
  font-size: 0.8125rem;
  color: #1e40af;
  margin: 0;
  line-height: 1.5;
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
`

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
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

// Result View Components
const QRContainer = styled.div`
  display: flex;
  justify-content: center;
  padding: 1.5rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 1rem;
`

const ResultInfo = styled.div`
  text-align: center;
  margin-bottom: 1.5rem;
`

const BatchName = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  background: #f3f4f6;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  display: inline-block;
  margin-bottom: 0.5rem;
`

const UsageInfo = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`

const ExpiryInfo = styled.div`
  font-size: 0.8125rem;
  color: #9ca3af;
  margin-top: 0.25rem;
`

const CopiedBadge = styled.span`
  font-size: 0.75rem;
  color: #10b981;
  background: #d1fae5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
`

const FeaturesBox = styled.div`
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
`

const FeaturesTitle = styled.h4`
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.75rem 0;
`

const FeaturesList = styled.ul`
  margin: 0;
  padding-left: 1.25rem;
`

const Feature = styled.li`
  font-size: 0.875rem;
  color: #4b5563;
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const Spinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

const BatchQRModal: React.FC<BatchQRModalProps> = ({
  isOpen,
  onClose,
  onGenerate,
  isGenerating
}) => {
  const qrRef = useRef<HTMLDivElement>(null)
  const [step, setStep] = useState<'form' | 'result'>('form')
  const [batchName, setBatchName] = useState('')
  const [maxUses, setMaxUses] = useState('')
  const [expiresDays, setExpiresDays] = useState('30')
  const [generatedCode, setGeneratedCode] = useState<BatchCodeResponse | null>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setStep('form')
      setBatchName('')
      setMaxUses('')
      setExpiresDays('30')
      setGeneratedCode(null)
      setError(null)
    }
  }, [isOpen])

  // Close on escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    try {
      const result = await onGenerate({
        batch_name: batchName || undefined,
        max_uses: maxUses ? parseInt(maxUses) : null,
        expires_days: expiresDays === 'never' ? null : parseInt(expiresDays)
      })
      setGeneratedCode(result)
      setStep('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate batch code')
    }
  }

  const copyToClipboard = async () => {
    if (!generatedCode?.link) return

    try {
      await navigator.clipboard.writeText(generatedCode.link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadQR = () => {
    if (!qrRef.current) return

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
      const filename = generatedCode?.batch_name
        ? `batch-qr-${generatedCode.batch_name.replace(/\s+/g, '-')}.png`
        : 'batch-qr-registration.png'
      downloadLink.download = filename
      downloadLink.href = pngFile
      downloadLink.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  const formatExpiry = (expiresAt: string | null | undefined): string => {
    if (!expiresAt) return 'Never'
    const date = new Date(expiresAt)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <ModalOverlay isOpen={isOpen} onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <Header>
          <TitleSection>
            <Title>
              {step === 'form' ? 'Generate Batch QR Code' : 'Batch QR Generated!'}
            </Title>
            <Subtitle>
              {step === 'form'
                ? 'Create a reusable registration link for multiple clients'
                : 'Share this QR code with your clients'}
            </Subtitle>
          </TitleSection>
          <CloseButton onClick={onClose}>
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </CloseButton>
        </Header>

        {step === 'form' ? (
          <Form onSubmit={handleSubmit}>
            <FormGroup>
              <Label>Batch Name (optional)</Label>
              <Input
                type="text"
                value={batchName}
                onChange={e => setBatchName(e.target.value)}
                placeholder="e.g., Store Front QR, Event Signup"
              />
            </FormGroup>

            <FormGroup>
              <Label>Maximum Uses (optional)</Label>
              <Input
                type="number"
                min="1"
                value={maxUses}
                onChange={e => setMaxUses(e.target.value)}
                placeholder="Leave empty for unlimited"
              />
            </FormGroup>

            <FormGroup>
              <Label>Expires In</Label>
              <Select
                value={expiresDays}
                onChange={e => setExpiresDays(e.target.value)}
              >
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="365">1 year</option>
                <option value="never">Never</option>
              </Select>
            </FormGroup>

            <InfoBox>
              <InfoIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </InfoIcon>
              <InfoText>
                Clients scanning this QR will be auto-registered with IDs like
                Client-00001, Client-00002, etc. You can rename them later from the Clients page.
              </InfoText>
            </InfoBox>

            {error && (
              <InfoBox style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
                <InfoIcon style={{ color: '#ef4444' }}>
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </InfoIcon>
                <InfoText style={{ color: '#991b1b' }}>{error}</InfoText>
              </InfoBox>
            )}

            <ButtonGroup>
              <Button type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={isGenerating}>
                {isGenerating ? (
                  <>
                    <Spinner />
                    Generating...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                    </svg>
                    Generate QR
                  </>
                )}
              </Button>
            </ButtonGroup>
          </Form>
        ) : generatedCode && (
          <>
            <ResultInfo>
              <BatchName>
                {generatedCode.batch_name || 'Default Batch'}
              </BatchName>
              <UsageInfo>
                {generatedCode.max_uses
                  ? `0 / ${generatedCode.max_uses} uses`
                  : 'Unlimited uses'}
              </UsageInfo>
              <ExpiryInfo>
                Expires: {formatExpiry(generatedCode.expires_at)}
              </ExpiryInfo>
            </ResultInfo>

            <QRContainer ref={qrRef}>
              <QRCodeSVG
                value={generatedCode.link}
                size={200}
                level="H"
                includeMargin={true}
              />
            </QRContainer>

            <ButtonGroup>
              <Button onClick={downloadQR}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download QR
              </Button>
              <Button onClick={copyToClipboard}>
                {copied ? (
                  <CopiedBadge>Copied!</CopiedBadge>
                ) : (
                  <>
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy Link
                  </>
                )}
              </Button>
            </ButtonGroup>

            <FeaturesBox>
              <FeaturesTitle>Features</FeaturesTitle>
              <FeaturesList>
                <Feature>Multiple clients can scan this QR code</Feature>
                <Feature>Each client gets an auto-generated ID (Client-00001, etc.)</Feature>
                <Feature>Clients can immediately receive invoices after scanning</Feature>
                <Feature>View all batch codes in your Clients page</Feature>
              </FeaturesList>
            </FeaturesBox>

            <ButtonGroup style={{ marginTop: '1.5rem' }}>
              <Button onClick={() => setStep('form')}>
                Generate Another
              </Button>
              <Button variant="primary" onClick={onClose}>
                Done
              </Button>
            </ButtonGroup>
          </>
        )}
      </ModalContent>
    </ModalOverlay>
  )
}

export default BatchQRModal
