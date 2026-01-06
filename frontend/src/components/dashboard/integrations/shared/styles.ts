import styled from 'styled-components'

export const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
`

export const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
`

export const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

export const BackButton = styled.button`
  background: transparent;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    background: #f3f4f6;
    color: #1f2937;
  }
`

export const IntegrationCard = styled.div<{ connected?: boolean }>`
  border: 2px solid ${props => props.connected ? '#28a745' : '#e5e7eb'};
  border-radius: 12px;
  padding: 2rem;
  background: ${props => props.connected ? '#f8fff9' : 'white'};
  transition: all 0.3s ease;
`

export const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.875rem;
  margin-bottom: 1rem;
`

export const PlatformName = styled.h3`
  margin: 0;
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  flex: 1;
`

export const StatusBadge = styled.span<{ connected: boolean }>`
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;

  ${props => props.connected ? `
    background: #28a745;
    color: white;
  ` : `
    background: #dc3545;
    color: white;
  `}
`

export const Description = styled.p`
  margin: 0 0 1.5rem 0;
  color: #6b7280;
  font-size: 1rem;
  line-height: 1.6;
`

export const TokensList = styled.div`
  margin: 1rem 0;
`

export const TokenItem = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.875rem;
  margin-bottom: 0.625rem;
  font-size: 0.9375rem;

  &:last-child {
    margin-bottom: 0;
  }
`

export const TokenMeta = styled.div`
  color: #6b7280;
  font-size: 0.8125rem;
  margin-top: 0.375rem;
`

export const ConnectButton = styled.button<{ platform: 'facebook' | 'tiktok' }>`
  ${props => props.platform === 'facebook' ? `
    background: linear-gradient(135deg, #4267b2 0%, #365899 100%);
  ` : `
    background: linear-gradient(135deg, #000 0%, #333 100%);
  `}
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
`

export const TelegramButton = styled.button`
  background: linear-gradient(135deg, #0088cc 0%, #229ED9 100%);
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 136, 204, 0.3);
  }
`

export const DisconnectButton = styled.button`
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    background: #c82333;
  }
`

export const LinkCodeBox = styled.div`
  background: #f0f9ff;
  border: 1px solid #0088cc;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  text-align: center;
`

export const LinkCode = styled.code`
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #0088cc;
  letter-spacing: 0.15em;
  margin: 0.75rem 0;
`

export const DeepLinkButton = styled.a`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #0088cc;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  margin-top: 0.75rem;
  transition: all 0.2s ease;

  &:hover {
    background: #006699;
    transform: translateY(-1px);
  }
`

export const ExpiryText = styled.p`
  font-size: 0.8125rem;
  color: #6b7280;
  margin-top: 0.75rem;
`

export const ErrorText = styled.div`
  margin-top: 0.625rem;
  color: #dc3545;
  font-size: 0.8125rem;
`

export const SuccessMessage = styled.div`
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  color: #155724;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:before {
    content: "\\2713";
    font-size: 1.125rem;
    font-weight: 700;
    color: #28a745;
  }
`

export const TierBadge = styled.span<{ tier: 'free' | 'pro' }>`
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;
  ${props => props.tier === 'pro' ? `
    background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
    color: #1f2937;
  ` : `
    background: #e5e7eb;
    color: #6b7280;
  `}
`

export const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 1.5rem 0;
`

export const FeatureItem = styled.li<{ available: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  font-size: 1rem;
  color: ${props => props.available ? '#1f2937' : '#9ca3af'};

  &:before {
    content: "${props => props.available ? '✓' : '✗'}";
    color: ${props => props.available ? '#28a745' : '#dc3545'};
    font-weight: 700;
  }
`

export const UpgradeButton = styled.button`
  background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
  color: #1f2937;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3);
  }
`

export const OpenButton = styled.button`
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 0.75rem;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
`

export const PricingOptions = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
`

export const PriceButton = styled.button<{ recommended?: boolean }>`
  flex: 1;
  padding: 1rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;

  ${props => props.recommended ? `
    background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
    color: white;
    border: none;
  ` : `
    background: white;
    color: #4a90e2;
    border: 2px solid #4a90e2;
  `}

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  small {
    display: block;
    font-weight: 400;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    opacity: 0.8;
  }
`

export const SubscriptionInfo = styled.div`
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
`

export const SubscriptionDetail = styled.p`
  margin: 0.25rem 0;
  font-size: 0.9375rem;
  color: #6b7280;
`

export const ManageButton = styled.button`
  background: white;
  color: #4a90e2;
  border: 2px solid #4a90e2;
  padding: 0.625rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1rem;

  &:hover:not(:disabled) {
    background: #f0f7ff;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

export const InfoText = styled.p`
  margin: 0 0 0.5rem 0;
  font-size: 0.9375rem;
  color: #6b7280;
  font-weight: 500;
`
