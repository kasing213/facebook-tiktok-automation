import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'
import { useAuth, useOAuth } from '../../hooks/useAuth'
import { LoadingSpinner } from '../LoadingSpinner'
import { easings, reduceMotion } from '../../styles/animations'
import { useStaggeredAnimation } from '../../hooks/useScrollAnimation'

// Import platform logos
import facebookLogo from '../../assets/images/social/facebook-logo.png'
import tiktokLogo from '../../assets/images/social/tiktok-logo.png'

// Styled Components
const Container = styled.div`
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
`

const Header = styled.div`
  margin-bottom: 2rem;
`

const Title = styled.h1`
  font-size: 1.5rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 0.5rem 0;
`

const Subtitle = styled.p`
  font-size: 0.875rem;
  color: ${props => props.theme.textSecondary};
  margin: 0;
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`

const StatCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card || 'white'};
  border-radius: 12px;
  border: 1px solid ${props => props.theme.border || '#e5e7eb'};
  padding: 1.25rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor || 'rgba(0, 0, 0, 0.1)'};
  }

  ${reduceMotion}
`

const StatLabel = styled.p`
  font-size: 0.75rem;
  font-weight: 500;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.5rem 0;
`

const StatValue = styled.p`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const PlatformsSection = styled.section`
  margin-bottom: 2rem;
`

const SectionTitle = styled.h2`
  font-size: 1rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const PlatformsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1rem;
`

const PlatformCard = styled.div<{ $connected: boolean; $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card || 'white'};
  border-radius: 12px;
  border: 1px solid ${props => props.$connected ? '#d1fae5' : (props.theme.border || '#e5e7eb')};
  padding: 1.5rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              box-shadow 0.2s ease,
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  ${reduceMotion}
`

const PlatformHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
`

const PlatformLogo = styled.img`
  width: 48px;
  height: 48px;
  border-radius: 10px;
  object-fit: contain;
`

const PlatformInfo = styled.div`
  flex: 1;
`

const PlatformName = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 0.25rem 0;
`

const PlatformStatus = styled.span<{ $connected: boolean }>`
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: ${props => props.$connected ? '#d1fae5' : '#fee2e2'};
  color: ${props => props.$connected ? '#059669' : '#dc2626'};
`

const AccountsList = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid ${props => props.theme.border};
`

const AccountItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 8px;
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const AccountInfo = styled.div``

const AccountName = styled.p`
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const AccountMeta = styled.p`
  font-size: 0.75rem;
  color: ${props => props.theme.textSecondary};
  margin: 0.25rem 0 0 0;
`

const AccountBadge = styled.span<{ $valid: boolean }>`
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  background: ${props => props.$valid ? '#d1fae5' : '#fef3c7'};
  color: ${props => props.$valid ? '#059669' : '#d97706'};
`

const ConnectButton = styled.button<{ $platform: 'facebook' | 'tiktok' }>`
  width: 100%;
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
  background: ${props => props.$platform === 'facebook' ? '#1877f2' : '#000000'};
  color: white;

  &:hover {
    background: ${props => props.$platform === 'facebook' ? '#166fe5' : '#333333'};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const ManageButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  background: ${props => props.theme.card};
  color: ${props => props.theme.textPrimary};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.theme.backgroundTertiary};
    border-color: ${props => props.theme.border};
  }
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
`

const FeaturesSection = styled.section`
  margin-top: 2rem;
`

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
`

const FeatureCard = styled.div`
  background: ${props => props.theme.backgroundSecondary};
  border: 1px dashed ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
`

const FeatureIcon = styled.div`
  width: 48px;
  height: 48px;
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: ${props => props.theme.textSecondary};
`

const FeatureTitle = styled.h4`
  font-size: 0.9375rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 0.5rem 0;
`

const FeatureDescription = styled.p`
  font-size: 0.8125rem;
  color: ${props => props.theme.textSecondary};
  margin: 0;
`

const ComingSoonBadge = styled.span`
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: #e0e7ff;
  color: #4f46e5;
  margin-top: 0.75rem;
`

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
`

const ErrorMessage = styled.div`
  background: ${props => props.theme.mode === 'dark' ? 'rgba(220, 38, 38, 0.1)' : '#fef2f2'};
  border: 1px solid ${props => props.theme.mode === 'dark' ? 'rgba(220, 38, 38, 0.3)' : '#fecaca'};
  border-radius: 8px;
  padding: 1rem;
  color: ${props => props.theme.error};
  margin-bottom: 1rem;
`

const SocialMediaPage: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const tenantId = localStorage.getItem('selectedTenantId') || ''

  const { authStatus, loading, error } = useAuth(tenantId || null)
  const { initiating, errors: oauthErrors, clearErrors, initiateFacebookOAuth, initiateTikTokOAuth } = useOAuth()

  // Staggered animations for stats and platform cards
  const statsVisible = useStaggeredAnimation(3, 100)  // 3 stat cards
  const platformsVisible = useStaggeredAnimation(2, 150)  // 2 platform cards

  const handleConnectFacebook = async () => {
    if (!tenantId) return
    clearErrors()
    try {
      await initiateFacebookOAuth(tenantId)
    } catch (err) {
      console.error('Failed to initiate Facebook OAuth:', err)
    }
  }

  const handleConnectTikTok = async () => {
    if (!tenantId) return
    clearErrors()
    try {
      await initiateTikTokOAuth(tenantId)
    } catch (err) {
      console.error('Failed to initiate TikTok OAuth:', err)
    }
  }

  const facebookConnected = authStatus?.facebook?.connected || false
  const tiktokConnected = authStatus?.tiktok?.connected || false
  const facebookAccounts = authStatus?.facebook?.accounts || []
  const tiktokAccounts = authStatus?.tiktok?.accounts || []

  const totalConnected = (facebookConnected ? 1 : 0) + (tiktokConnected ? 1 : 0)
  const totalAccounts = facebookAccounts.length + tiktokAccounts.length

  if (!tenantId) {
    return (
      <Container>
        <ErrorMessage>
          {t('socialMedia.noWorkspace')}
        </ErrorMessage>
      </Container>
    )
  }

  return (
    <Container>
      <Header>
        <Title>{t('socialMedia.title')}</Title>
        <Subtitle>{t('socialMedia.subtitle')}</Subtitle>
      </Header>

      {/* Stats Overview */}
      <StatsGrid>
        <StatCard $isVisible={statsVisible[0]} $delay={0}>
          <StatLabel>{t('socialMedia.connectedPlatforms')}</StatLabel>
          <StatValue>{totalConnected}/2</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[1]} $delay={100}>
          <StatLabel>{t('socialMedia.linkedAccounts')}</StatLabel>
          <StatValue>{totalAccounts}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[2]} $delay={200}>
          <StatLabel>{t('socialMedia.scheduledPosts')}</StatLabel>
          <StatValue>0</StatValue>
        </StatCard>
      </StatsGrid>

      {error && (
        <ErrorMessage>{t('socialMedia.loadError')}: {error}</ErrorMessage>
      )}

      {/* Connected Platforms */}
      <PlatformsSection>
        <SectionTitle>
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {t('socialMedia.yourPlatforms')}
        </SectionTitle>

        {loading ? (
          <LoadingContainer>
            <LoadingSpinner size="large" />
            <Subtitle>{t('common.loading')}</Subtitle>
          </LoadingContainer>
        ) : (
          <PlatformsGrid>
            {/* Facebook Card */}
            <PlatformCard $connected={facebookConnected} $isVisible={platformsVisible[0]} $delay={0}>
              <PlatformHeader>
                <PlatformLogo src={facebookLogo} alt="Facebook" />
                <PlatformInfo>
                  <PlatformName>Facebook</PlatformName>
                  <PlatformStatus $connected={facebookConnected}>
                    {facebookConnected ? t('socialMedia.connected') : t('socialMedia.notConnected')}
                  </PlatformStatus>
                </PlatformInfo>
              </PlatformHeader>

              {facebookConnected && facebookAccounts.length > 0 && (
                <AccountsList>
                  {facebookAccounts.map((account, idx) => (
                    <AccountItem key={idx}>
                      <AccountInfo>
                        <AccountName>{account.account_name || account.account_ref}</AccountName>
                        <AccountMeta>
                          {account.expires_at
                            ? `${t('socialMedia.expires')}: ${new Date(account.expires_at).toLocaleDateString()}`
                            : t('socialMedia.noExpiration')
                          }
                        </AccountMeta>
                      </AccountInfo>
                      <AccountBadge $valid={account.is_valid}>
                        {account.is_valid ? t('socialMedia.valid') : t('socialMedia.expired')}
                      </AccountBadge>
                    </AccountItem>
                  ))}
                </AccountsList>
              )}

              {oauthErrors.facebook && (
                <ErrorMessage style={{ marginTop: '1rem' }}>{oauthErrors.facebook}</ErrorMessage>
              )}

              <ButtonGroup>
                {facebookConnected ? (
                  <>
                    <ManageButton onClick={() => navigate('/dashboard/integrations/facebook')}>
                      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {t('socialMedia.manage')}
                    </ManageButton>
                    <ConnectButton
                      $platform="facebook"
                      onClick={handleConnectFacebook}
                      disabled={initiating.facebook}
                    >
                      {initiating.facebook ? (
                        <LoadingSpinner size="small" />
                      ) : (
                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      )}
                      {t('socialMedia.addAccount')}
                    </ConnectButton>
                  </>
                ) : (
                  <ConnectButton
                    $platform="facebook"
                    onClick={handleConnectFacebook}
                    disabled={initiating.facebook}
                    style={{ flex: 1 }}
                  >
                    {initiating.facebook ? (
                      <>
                        <LoadingSpinner size="small" />
                        {t('socialMedia.connecting')}
                      </>
                    ) : (
                      <>
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                        {t('socialMedia.connectFacebook')}
                      </>
                    )}
                  </ConnectButton>
                )}
              </ButtonGroup>
            </PlatformCard>

            {/* TikTok Card */}
            <PlatformCard $connected={tiktokConnected} $isVisible={platformsVisible[1]} $delay={150}>
              <PlatformHeader>
                <PlatformLogo src={tiktokLogo} alt="TikTok" />
                <PlatformInfo>
                  <PlatformName>TikTok</PlatformName>
                  <PlatformStatus $connected={tiktokConnected}>
                    {tiktokConnected ? t('socialMedia.connected') : t('socialMedia.notConnected')}
                  </PlatformStatus>
                </PlatformInfo>
              </PlatformHeader>

              {tiktokConnected && tiktokAccounts.length > 0 && (
                <AccountsList>
                  {tiktokAccounts.map((account, idx) => (
                    <AccountItem key={idx}>
                      <AccountInfo>
                        <AccountName>{account.account_name || account.account_ref}</AccountName>
                        <AccountMeta>
                          {account.expires_at
                            ? `${t('socialMedia.expires')}: ${new Date(account.expires_at).toLocaleDateString()}`
                            : t('socialMedia.noExpiration')
                          }
                        </AccountMeta>
                      </AccountInfo>
                      <AccountBadge $valid={account.is_valid}>
                        {account.is_valid ? t('socialMedia.valid') : t('socialMedia.expired')}
                      </AccountBadge>
                    </AccountItem>
                  ))}
                </AccountsList>
              )}

              {oauthErrors.tiktok && (
                <ErrorMessage style={{ marginTop: '1rem' }}>{oauthErrors.tiktok}</ErrorMessage>
              )}

              <ButtonGroup>
                {tiktokConnected ? (
                  <>
                    <ManageButton onClick={() => navigate('/dashboard/integrations/tiktok')}>
                      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {t('socialMedia.manage')}
                    </ManageButton>
                    <ConnectButton
                      $platform="tiktok"
                      onClick={handleConnectTikTok}
                      disabled={initiating.tiktok}
                    >
                      {initiating.tiktok ? (
                        <LoadingSpinner size="small" />
                      ) : (
                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      )}
                      {t('socialMedia.addAccount')}
                    </ConnectButton>
                  </>
                ) : (
                  <ConnectButton
                    $platform="tiktok"
                    onClick={handleConnectTikTok}
                    disabled={initiating.tiktok}
                    style={{ flex: 1 }}
                  >
                    {initiating.tiktok ? (
                      <>
                        <LoadingSpinner size="small" />
                        {t('socialMedia.connecting')}
                      </>
                    ) : (
                      <>
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
                        </svg>
                        {t('socialMedia.connectTikTok')}
                      </>
                    )}
                  </ConnectButton>
                )}
              </ButtonGroup>
            </PlatformCard>
          </PlatformsGrid>
        )}
      </PlatformsSection>

      {/* Coming Soon Features */}
      <FeaturesSection>
        <SectionTitle>
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          {t('socialMedia.features')}
        </SectionTitle>

        <FeatureGrid>
          <FeatureCard>
            <FeatureIcon>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </FeatureIcon>
            <FeatureTitle>{t('socialMedia.featureSchedule')}</FeatureTitle>
            <FeatureDescription>{t('socialMedia.featureScheduleDesc')}</FeatureDescription>
            <ComingSoonBadge>{t('socialMedia.comingSoon')}</ComingSoonBadge>
          </FeatureCard>

          <FeatureCard>
            <FeatureIcon>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </FeatureIcon>
            <FeatureTitle>{t('socialMedia.featureAnalytics')}</FeatureTitle>
            <FeatureDescription>{t('socialMedia.featureAnalyticsDesc')}</FeatureDescription>
            <ComingSoonBadge>{t('socialMedia.comingSoon')}</ComingSoonBadge>
          </FeatureCard>

          <FeatureCard>
            <FeatureIcon>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
              </svg>
            </FeatureIcon>
            <FeatureTitle>{t('socialMedia.featureAds')}</FeatureTitle>
            <FeatureDescription>{t('socialMedia.featureAdsDesc')}</FeatureDescription>
            <ComingSoonBadge>{t('socialMedia.comingSoon')}</ComingSoonBadge>
          </FeatureCard>

          <FeatureCard>
            <FeatureIcon>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
              </svg>
            </FeatureIcon>
            <FeatureTitle>{t('socialMedia.featureInbox')}</FeatureTitle>
            <FeatureDescription>{t('socialMedia.featureInboxDesc')}</FeatureDescription>
            <ComingSoonBadge>{t('socialMedia.comingSoon')}</ComingSoonBadge>
          </FeatureCard>
        </FeatureGrid>
      </FeaturesSection>
    </Container>
  )
}

export default SocialMediaPage
