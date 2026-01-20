import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled, { css } from 'styled-components'
import {
  fadeInUp,
  fadeInDown,
  easings,
  buttonHoverEffect,
  reduceMotion,
  glowPulse
} from '../styles/animations'
import { useScrollAnimation } from '../hooks/useScrollAnimation'

// Modern landing page with blue color scheme
// Colors: #4a90e2 (primary blue), #2a5298 (dark blue), #e8f4fd (light blue bg)

const PageWrapper = styled.div`
  min-height: 100vh;
  background: #ffffff;
  color: #1f2937;
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
`

// Navigation
const Nav = styled.nav`
  position: fixed;
  width: 100%;
  z-index: 50;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #f3f4f6;
`

const NavContainer = styled.div`
  max-width: 72rem;
  margin: 0 auto;
  padding: 0 1.5rem;
`

const NavInner = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 4rem;
`

const LogoWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
`

const LogoIcon = styled.div`
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.5rem;
  background: #4a90e2;
  display: flex;
  align-items: center;
  justify-content: center;
`

const LogoText = styled.span`
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.025em;
`

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;

  @media (max-width: 768px) {
    display: none;
  }
`

const NavLink = styled.a`
  font-size: 0.875rem;
  color: #6b7280;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #1f2937;
  }
`

const NavActions = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;

  @media (max-width: 768px) {
    display: none;
  }
`

const SignInLink = styled.a`
  font-size: 0.875rem;
  color: #6b7280;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #1f2937;
  }
`

const GetStartedButton = styled.button`
  font-size: 0.875rem;
  background: #4a90e2;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  ${buttonHoverEffect}

  &:hover {
    background: #2a5298;
  }
`

const MobileMenuButton = styled.button`
  display: none;
  padding: 0.5rem;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;

  @media (max-width: 768px) {
    display: block;
  }
`

const MobileMenu = styled.div`
  display: none;
  background: white;
  border-top: 1px solid #f3f4f6;
  padding: 1rem 1.5rem;

  @media (max-width: 768px) {
    display: block;
  }
`

const MobileNavLink = styled.a`
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  padding: 0.5rem 0;
  text-decoration: none;
  cursor: pointer;
`

const MobileGetStartedButton = styled.button`
  width: 100%;
  font-size: 0.875rem;
  background: #4a90e2;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  margin-top: 0.5rem;
`

// Hero Section
const HeroSection = styled.section`
  padding: 8rem 1.5rem 5rem;

  @media (max-width: 768px) {
    padding: 6rem 1.5rem 3rem;
  }
`

const HeroContainer = styled.div`
  max-width: 72rem;
  margin: 0 auto;
`

const HeroContent = styled.div`
  text-align: center;
  max-width: 48rem;
  margin: 0 auto;
`

const Badge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #e8f4fd;
  border: 1px solid #d1e7f8;
  color: #2a5298;
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 2rem;
  opacity: 0;
  animation: ${fadeInDown} 0.5s ${easings.easeOutCubic} forwards;
  ${reduceMotion}
`

const BadgeDot = styled.span`
  width: 0.375rem;
  height: 0.375rem;
  background: #4a90e2;
  border-radius: 9999px;
`

const HeroTitle = styled.h1`
  font-size: 3.75rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.1;
  margin: 0 0 1.5rem 0;
  color: #1f2937;
  opacity: 0;
  animation: ${fadeInUp} 0.6s ${easings.easeOutCubic} 0.1s forwards;
  ${reduceMotion}

  @media (max-width: 1024px) {
    font-size: 3rem;
  }

  @media (max-width: 640px) {
    font-size: 2.25rem;
  }
`

const HeroTitleHighlight = styled.span`
  display: block;
  color: #4a90e2;
`

const HeroSubtitle = styled.p`
  font-size: 1.125rem;
  color: #6b7280;
  margin: 0 0 2.5rem 0;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.7;
  opacity: 0;
  animation: ${fadeInUp} 0.6s ${easings.easeOutCubic} 0.2s forwards;
  ${reduceMotion}
`

const HeroButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  justify-content: center;
  align-items: center;
  opacity: 0;
  animation: ${fadeInUp} 0.6s ${easings.easeOutCubic} 0.3s forwards;
  ${reduceMotion}

  @media (min-width: 640px) {
    flex-direction: row;
  }
`

const PrimaryButton = styled.button`
  background: #4a90e2;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  box-shadow: 0 10px 15px -3px rgba(74, 144, 226, 0.25);
  ${buttonHoverEffect}

  &:hover {
    background: #2a5298;
  }
`

const SecondaryButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: white;
  border: 2px solid #e5e7eb;
  color: #374151;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.875rem;
  transition: transform 0.2s ${easings.easeOutCubic},
              box-shadow 0.2s ${easings.easeOutCubic},
              border-color 0.2s ease,
              background-color 0.2s ease;

  &:hover {
    border-color: #4a90e2;
    background: #f8fafc;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  ${reduceMotion}
`

const HeroNote = styled.p`
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #9ca3af;
`

// Dashboard Preview
const PreviewWrapper = styled.div<{ $isVisible?: boolean }>`
  margin-top: 4rem;
  position: relative;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(40px)'};
  transition: opacity 0.8s ${easings.easeOutCubic},
              transform 0.8s ${easings.easeOutCubic};
  transition-delay: 0.4s;
  ${reduceMotion}
`

const PreviewGradient = styled.div`
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, white, transparent, transparent);
  z-index: 10;
  pointer-events: none;
`

const PreviewContainer = styled.div`
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
`

const BrowserChrome = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f3f4f6;
`

const BrowserDots = styled.div`
  display: flex;
  gap: 0.375rem;
`

const BrowserDot = styled.div<{ color: string }>`
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 9999px;
  background: ${props => props.color};
`

const BrowserUrl = styled.div`
  flex: 1;
  display: flex;
  justify-content: center;
`

const BrowserUrlBar = styled.div`
  background: white;
  border-radius: 0.375rem;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  color: #9ca3af;
  border: 1px solid #e5e7eb;
`

const DashboardContent = styled.div`
  padding: 1.5rem;
  background: white;
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
`

const StatCard = styled.div`
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid #f3f4f6;
`

const StatLabel = styled.p`
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0 0 0.25rem 0;
`

const StatValue = styled.p`
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const StatChange = styled.p<{ positive?: boolean }>`
  font-size: 0.75rem;
  color: ${props => props.positive ? '#4a90e2' : '#9ca3af'};
  margin: 0.25rem 0 0 0;
`

const TableWrapper = styled.div`
  background: #f9fafb;
  border-radius: 0.75rem;
  border: 1px solid #f3f4f6;
  overflow: hidden;
`

const TableHeader = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  color: #9ca3af;
  border-bottom: 1px solid #f3f4f6;
  background: rgba(243, 244, 246, 0.5);
`

const TableRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  border-bottom: 1px solid #f3f4f6;
  background: white;

  &:last-child {
    border-bottom: none;
  }
`

const TableCell = styled.span<{ mono?: boolean; muted?: boolean }>`
  color: ${props => props.muted ? '#9ca3af' : '#374151'};
  font-family: ${props => props.mono ? 'monospace' : 'inherit'};
`

const StatusBadge = styled.span<{ status: 'paid' | 'pending' | 'verifying' }>`
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  background: ${props => {
    switch (props.status) {
      case 'paid': return '#e8f4fd'
      case 'pending': return '#fef3c7'
      case 'verifying': return '#e0f2fe'
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'paid': return '#2a5298'
      case 'pending': return '#92400e'
      case 'verifying': return '#0369a1'
    }
  }};
`

const StatusDot = styled.span<{ status: 'paid' | 'pending' | 'verifying' }>`
  width: 0.25rem;
  height: 0.25rem;
  border-radius: 9999px;
  background: ${props => {
    switch (props.status) {
      case 'paid': return '#4a90e2'
      case 'pending': return '#f59e0b'
      case 'verifying': return '#0ea5e9'
    }
  }};
`

// Features Section
const FeaturesSection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #f9fafb;
`

// Social Media Features Section (white background for contrast)
const SocialFeaturesSection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #ffffff;
`

const SectionContainer = styled.div`
  max-width: 72rem;
  margin: 0 auto;
`

const SectionHeader = styled.div`
  text-align: center;
  margin-bottom: 4rem;
`

const SectionTitle = styled.h2`
  font-size: 1.875rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  margin: 0 0 1rem 0;
  color: #1f2937;
`

const SectionSubtitle = styled.p`
  color: #6b7280;
  max-width: 32rem;
  margin: 0 auto;
`

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const FeatureCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: white;
  border-radius: 1rem;
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(30px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              border-color 0.3s ease,
              box-shadow 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    border-color: #d1e7f8;
    box-shadow: 0 20px 25px -5px rgba(74, 144, 226, 0.15);
    transform: translateY(-4px);
  }

  ${reduceMotion}
`

const FeatureIcon = styled.div`
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  background: #e8f4fd;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
`

const FeatureTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 0.5rem 0;
  color: #1f2937;
`

const FeatureDescription = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
`

const FeatureDemo = styled.div`
  margin-top: 1.5rem;
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid #f3f4f6;
`

const TelegramDemo = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
`

const TelegramIcon = styled.div`
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  background: #0088cc;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`

const TelegramContent = styled.div`
  flex: 1;
`

const TelegramStatus = styled.p`
  font-size: 0.75rem;
  color: #4a90e2;
  font-weight: 500;
  margin: 0 0 0.25rem 0;
`

const TelegramDetail = styled.p`
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
`

const InventoryItem = styled.div`
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 0.75rem;
  border: 1px solid #f3f4f6;
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const InventoryHeader = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
`

const InventoryName = styled.span`
  color: #374151;
`

const InventoryStock = styled.span<{ low?: boolean }>`
  color: ${props => props.low ? '#f59e0b' : '#4a90e2'};
`

const ProgressBar = styled.div`
  height: 0.375rem;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
`

const ProgressFill = styled.div<{ percent: number; color: string }>`
  height: 100%;
  border-radius: 9999px;
  background: ${props => props.color};
  width: ${props => props.percent}%;
`

const InvoiceDemo = styled.div``

const InvoiceHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
`

const InvoiceNumber = styled.span`
  font-size: 0.75rem;
  font-family: monospace;
  color: #6b7280;
`

const InvoiceStatus = styled.span`
  font-size: 0.75rem;
  color: #4a90e2;
  font-weight: 500;
`

const InvoiceLine = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  padding: 0.25rem 0;
`

const InvoiceLabel = styled.span`
  color: #9ca3af;
`

const InvoiceValue = styled.span`
  color: #374151;
`

const InvoiceTotal = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
  margin-top: 0.5rem;
`

const InvoiceTotalLabel = styled.span`
  color: #374151;
  font-weight: 500;
`

const InvoiceTotalValue = styled.span`
  color: #1f2937;
  font-weight: 600;
`

// Stats Section
const StatsSection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
`

const StatsContainer = styled.div`
  max-width: 72rem;
  margin: 0 auto;
`

const StatsGridLarge = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
`

const StatItemLarge = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  text-align: center;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic};
  transition-delay: ${props => props.$delay || 0}ms;
  ${reduceMotion}
`

const StatValueLarge = styled.p`
  font-size: 2.25rem;
  font-weight: 600;
  color: #4a90e2;
  margin: 0 0 0.5rem 0;

  @media (max-width: 768px) {
    font-size: 1.875rem;
  }
`

const StatLabelLarge = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
`

// Pricing Section
const PricingSection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #f9fafb;
`

const PricingGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  max-width: 48rem;
  margin: 0 auto;
  align-items: stretch;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const PricingCard = styled.div<{ highlighted?: boolean; $isVisible?: boolean; $delay?: number }>`
  border-radius: 1rem;
  padding: 1.5rem;
  background: ${props => props.highlighted ? '#4a90e2' : 'white'};
  color: ${props => props.highlighted ? 'white' : '#1f2937'};
  box-shadow: ${props => props.highlighted ? '0 25px 50px -12px rgba(74, 144, 226, 0.25)' : 'none'};
  border: ${props => props.highlighted ? 'none' : '1px solid #e5e7eb'};
  display: flex;
  flex-direction: column;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(30px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.3s ${easings.easeOutCubic},
              box-shadow 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    transform: translateY(-4px);
    box-shadow: ${props => props.highlighted
      ? '0 30px 60px -12px rgba(74, 144, 226, 0.35)'
      : '0 20px 40px -12px rgba(0, 0, 0, 0.1)'};
  }

  ${props => props.highlighted && css`
    animation: ${glowPulse} 3s ease-in-out infinite;
  `}

  ${reduceMotion}
`

const PopularBadge = styled.span`
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(42, 82, 152, 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  margin-bottom: 1rem;
`

const PlanName = styled.h3<{ highlighted?: boolean }>`
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 0.25rem 0;
  color: ${props => props.highlighted ? 'white' : '#1f2937'};
`

const PlanDescription = styled.p<{ highlighted?: boolean }>`
  font-size: 0.875rem;
  margin: 0 0 1rem 0;
  color: ${props => props.highlighted ? 'rgba(255, 255, 255, 0.8)' : '#6b7280'};
`

const PlanPrice = styled.div`
  margin-bottom: 1.5rem;
`

const PriceValue = styled.span<{ highlighted?: boolean }>`
  font-size: 1.875rem;
  font-weight: 600;
  color: ${props => props.highlighted ? 'white' : '#1f2937'};
`

const PricePeriod = styled.span<{ highlighted?: boolean }>`
  color: ${props => props.highlighted ? 'rgba(255, 255, 255, 0.8)' : '#6b7280'};
`

const PlanFeatures = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
  flex: 1;
`

const PlanFeature = styled.li<{ highlighted?: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: ${props => props.highlighted ? 'rgba(255, 255, 255, 0.9)' : '#4b5563'};
  padding: 0.375rem 0;
`

const CheckIcon = styled.svg<{ highlighted?: boolean }>`
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: ${props => props.highlighted ? 'rgba(255, 255, 255, 0.7)' : '#4a90e2'};
`

const PlanButton = styled.button<{ highlighted?: boolean }>`
  width: 100%;
  padding: 0.625rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto;

  background: ${props => props.highlighted ? 'white' : '#f3f4f6'};
  color: ${props => props.highlighted ? '#4a90e2' : '#374151'};
  border: ${props => props.highlighted ? 'none' : '1px solid #e5e7eb'};

  &:hover {
    background: ${props => props.highlighted ? '#f0f7ff' : '#e5e7eb'};
  }
`

// FAQ Section
const FAQSection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
`

const FAQContainer = styled.div`
  max-width: 42rem;
  margin: 0 auto;
`

const FAQList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`

const FAQItem = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
`

const FAQButton = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f9fafb;
  }
`

const FAQQuestion = styled.span`
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
`

const FAQIcon = styled.svg<{ open?: boolean }>`
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
  transition: transform 0.2s;
  transform: ${props => props.open ? 'rotate(180deg)' : 'rotate(0)'};
`

const FAQAnswer = styled.div<{ $isOpen: boolean }>`
  max-height: ${props => props.$isOpen ? '200px' : '0'};
  opacity: ${props => props.$isOpen ? 1 : 0};
  padding: ${props => props.$isOpen ? '0 1rem 1rem' : '0 1rem'};
  overflow: hidden;
  transition: max-height 0.3s ${easings.easeOutCubic},
              opacity 0.25s ${easings.easeOutCubic},
              padding 0.3s ${easings.easeOutCubic};
  ${reduceMotion}
`

const FAQAnswerText = styled.p`
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
`

// CTA Section
const CTASection = styled.section`
  padding: 5rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #f9fafb;
`

const CTAContainer = styled.div`
  max-width: 42rem;
  margin: 0 auto;
  text-align: center;
`

const CTATitle = styled.h2`
  font-size: 1.875rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  margin: 0 0 1rem 0;
  color: #1f2937;
`

const CTASubtitle = styled.p`
  color: #6b7280;
  margin: 0 0 2rem 0;
`

const CTAButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  justify-content: center;
  align-items: center;

  @media (min-width: 640px) {
    flex-direction: row;
  }
`

// Footer
const Footer = styled.footer`
  border-top: 1px solid #e5e7eb;
  padding: 3rem 1.5rem;
  background: white;
`

const FooterContainer = styled.div`
  max-width: 72rem;
  margin: 0 auto;
`

const FooterTop = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
  align-items: flex-start;

  @media (min-width: 768px) {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
`

const FooterLinks = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #6b7280;
`

const FooterLink = styled.a`
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #1f2937;
  }
`

const FooterBottom = styled.div`
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #f3f4f6;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;

  @media (min-width: 768px) {
    flex-direction: row;
    justify-content: space-between;
  }
`

const FooterCopyright = styled.p`
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
`

const SocialLinks = styled.div`
  display: flex;
  gap: 1rem;
`

const SocialLink = styled.a`
  color: #9ca3af;
  transition: color 0.2s;
  cursor: pointer;

  &:hover {
    color: #1f2937;
  }
`

const SocialIcon = styled.svg`
  width: 1.25rem;
  height: 1.25rem;
`

// Main Component
const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  // Scroll animation hooks for different sections
  const previewAnimation = useScrollAnimation({ threshold: 0.1 })
  const featuresAnimation = useScrollAnimation({ threshold: 0.1 })
  const socialAnimation = useScrollAnimation({ threshold: 0.1 })
  const statsAnimation = useScrollAnimation({ threshold: 0.2 })
  const pricingAnimation = useScrollAnimation({ threshold: 0.2 })

  const faqs = [
    {
      question: "How does OCR payment verification work?",
      answer: "Simply forward payment screenshots to our Telegram bot. Our AI instantly extracts transaction details, matches them to pending invoices, and marks them as paid — all in seconds."
    },
    {
      question: "Which local payment methods are supported?",
      answer: "We support all major Cambodian banks and payment apps including ABA, ACLEDA, Wing, TrueMoney, and KHQR. More integrations are added regularly."
    },
    {
      question: "Can I manage multiple businesses?",
      answer: "Yes. Our multi-tenant architecture lets you manage unlimited businesses from a single dashboard, each with their own invoices, inventory, and settings."
    },
    {
      question: "Is there a free trial?",
      answer: "Absolutely. Start with a 14-day free trial with full access to all features. No credit card required."
    },
    {
      question: "How secure is my data?",
      answer: "Your data is encrypted at rest and in transit. We use industry-standard security practices and never share your information with third parties."
    }
  ]

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
    setMobileMenuOpen(false)
  }

  return (
    <PageWrapper>
      {/* Navigation */}
      <Nav>
        <NavContainer>
          <NavInner>
            <LogoWrapper onClick={() => navigate('/')}>
              <LogoIcon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </LogoIcon>
              <LogoText>KS Automation</LogoText>
            </LogoWrapper>

            <NavLinks>
              <NavLink onClick={() => scrollToSection('features')}>Features</NavLink>
              <NavLink onClick={() => scrollToSection('pricing')}>Pricing</NavLink>
              <NavLink onClick={() => scrollToSection('faq')}>FAQ</NavLink>
            </NavLinks>

            <NavActions>
              <SignInLink onClick={() => navigate('/login')}>Sign in</SignInLink>
              <GetStartedButton onClick={() => navigate('/register')}>Get started</GetStartedButton>
            </NavActions>

            <MobileMenuButton onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </MobileMenuButton>
          </NavInner>
        </NavContainer>

        {mobileMenuOpen && (
          <MobileMenu>
            <MobileNavLink onClick={() => scrollToSection('features')}>Features</MobileNavLink>
            <MobileNavLink onClick={() => scrollToSection('pricing')}>Pricing</MobileNavLink>
            <MobileNavLink onClick={() => scrollToSection('faq')}>FAQ</MobileNavLink>
            <MobileNavLink onClick={() => navigate('/login')}>Sign in</MobileNavLink>
            <MobileGetStartedButton onClick={() => navigate('/register')}>
              Get started
            </MobileGetStartedButton>
          </MobileMenu>
        )}
      </Nav>

      {/* Hero */}
      <HeroSection>
        <HeroContainer>
          <HeroContent>
            <Badge>
              <BadgeDot />
              Now with Telegram OCR verification
            </Badge>

            <HeroTitle>
              Invoice & inventory management
              <HeroTitleHighlight>that actually works</HeroTitleHighlight>
            </HeroTitle>

            <HeroSubtitle>
              Create invoices, track inventory, and verify payments instantly. Built for businesses that accept local payments.
            </HeroSubtitle>

            <HeroButtons>
              <PrimaryButton onClick={() => navigate('/register')}>
                Start free trial
              </PrimaryButton>
              <SecondaryButton>
                <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                Watch demo
              </SecondaryButton>
            </HeroButtons>

            <HeroNote>No credit card required</HeroNote>
          </HeroContent>

          {/* Dashboard Preview */}
          <PreviewWrapper ref={previewAnimation.ref} $isVisible={previewAnimation.isVisible}>
            <PreviewGradient />
            <PreviewContainer>
              <BrowserChrome>
                <BrowserDots>
                  <BrowserDot color="#f87171" />
                  <BrowserDot color="#fbbf24" />
                  <BrowserDot color="#34d399" />
                </BrowserDots>
                <BrowserUrl>
                  <BrowserUrlBar>app.ksautomation.io</BrowserUrlBar>
                </BrowserUrl>
              </BrowserChrome>

              <DashboardContent>
                <StatsGrid>
                  <StatCard>
                    <StatLabel>Revenue this month</StatLabel>
                    <StatValue>$12,450</StatValue>
                    <StatChange positive>↑ 18% vs last month</StatChange>
                  </StatCard>
                  <StatCard>
                    <StatLabel>Pending invoices</StatLabel>
                    <StatValue>23</StatValue>
                    <StatChange>$4,280 total</StatChange>
                  </StatCard>
                  <StatCard>
                    <StatLabel>Products in stock</StatLabel>
                    <StatValue>847</StatValue>
                    <StatChange>3 low stock alerts</StatChange>
                  </StatCard>
                  <StatCard>
                    <StatLabel>Verified today</StatLabel>
                    <StatValue>12</StatValue>
                    <StatChange positive>via Telegram</StatChange>
                  </StatCard>
                </StatsGrid>

                <TableWrapper>
                  <TableHeader>
                    <span>Invoice</span>
                    <span>Customer</span>
                    <span>Amount</span>
                    <span>Status</span>
                    <span>Date</span>
                  </TableHeader>
                  <TableRow>
                    <TableCell mono>INV-001</TableCell>
                    <TableCell muted>Sokha Trading</TableCell>
                    <TableCell>$450.00</TableCell>
                    <TableCell>
                      <StatusBadge status="paid">
                        <StatusDot status="paid" />
                        Paid
                      </StatusBadge>
                    </TableCell>
                    <TableCell muted>Jan 15, 2025</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell mono>INV-002</TableCell>
                    <TableCell muted>Vanny Electronics</TableCell>
                    <TableCell>$1,200.00</TableCell>
                    <TableCell>
                      <StatusBadge status="pending">
                        <StatusDot status="pending" />
                        Pending
                      </StatusBadge>
                    </TableCell>
                    <TableCell muted>Jan 15, 2025</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell mono>INV-003</TableCell>
                    <TableCell muted>Kim Supplies</TableCell>
                    <TableCell>$320.00</TableCell>
                    <TableCell>
                      <StatusBadge status="paid">
                        <StatusDot status="paid" />
                        Paid
                      </StatusBadge>
                    </TableCell>
                    <TableCell muted>Jan 15, 2025</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell mono>INV-004</TableCell>
                    <TableCell muted>Chen Motors</TableCell>
                    <TableCell>$890.00</TableCell>
                    <TableCell>
                      <StatusBadge status="verifying">
                        <StatusDot status="verifying" />
                        Verifying
                      </StatusBadge>
                    </TableCell>
                    <TableCell muted>Jan 15, 2025</TableCell>
                  </TableRow>
                </TableWrapper>
              </DashboardContent>
            </PreviewContainer>
          </PreviewWrapper>
        </HeroContainer>
      </HeroSection>

      {/* Invoice Features */}
      <FeaturesSection id="features" ref={featuresAnimation.ref}>
        <SectionContainer>
          <SectionHeader>
            <SectionTitle>Invoice & Payment Management</SectionTitle>
            <SectionSubtitle>Automate your billing with OCR-powered payment verification.</SectionSubtitle>
          </SectionHeader>

          <FeaturesGrid>
            {/* Telegram Verification */}
            <FeatureCard $isVisible={featuresAnimation.isVisible} $delay={0}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2a5298" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </FeatureIcon>
              <FeatureTitle>Telegram verification</FeatureTitle>
              <FeatureDescription>
                Forward payment screenshots to our bot. OCR extracts details and auto-matches invoices in seconds.
              </FeatureDescription>
              <FeatureDemo>
                <TelegramDemo>
                  <TelegramIcon>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                    </svg>
                  </TelegramIcon>
                  <TelegramContent>
                    <TelegramStatus>Payment verified ✓</TelegramStatus>
                    <TelegramDetail>INV-002 • $1,200.00 from ABA</TelegramDetail>
                  </TelegramContent>
                </TelegramDemo>
              </FeatureDemo>
            </FeatureCard>

            {/* Smart Inventory */}
            <FeatureCard $isVisible={featuresAnimation.isVisible} $delay={100}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2a5298" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </FeatureIcon>
              <FeatureTitle>Smart inventory</FeatureTitle>
              <FeatureDescription>
                Real-time stock tracking with automatic low-stock alerts. Never oversell or miss a restock.
              </FeatureDescription>
              <FeatureDemo>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>iPhone 15 Pro</InventoryName>
                    <InventoryStock>12 left</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={24} color="#4a90e2" />
                  </ProgressBar>
                </InventoryItem>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>AirPods Pro</InventoryName>
                    <InventoryStock low>3 left</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={10} color="#f59e0b" />
                  </ProgressBar>
                </InventoryItem>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>MacBook Air M3</InventoryName>
                    <InventoryStock>8 left</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={40} color="#4a90e2" />
                  </ProgressBar>
                </InventoryItem>
              </FeatureDemo>
            </FeatureCard>

            {/* Beautiful Invoices */}
            <FeatureCard $isVisible={featuresAnimation.isVisible} $delay={200}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2a5298" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </FeatureIcon>
              <FeatureTitle>Beautiful invoices</FeatureTitle>
              <FeatureDescription>
                Professional invoices in seconds. Auto-calculate taxes, send via link or PDF, track when they're viewed.
              </FeatureDescription>
              <FeatureDemo>
                <InvoiceDemo>
                  <InvoiceHeader>
                    <InvoiceNumber>INV-005</InvoiceNumber>
                    <InvoiceStatus>Draft</InvoiceStatus>
                  </InvoiceHeader>
                  <InvoiceLine>
                    <InvoiceLabel>Subtotal</InvoiceLabel>
                    <InvoiceValue>$1,500.00</InvoiceValue>
                  </InvoiceLine>
                  <InvoiceLine>
                    <InvoiceLabel>VAT (10%)</InvoiceLabel>
                    <InvoiceValue>$150.00</InvoiceValue>
                  </InvoiceLine>
                  <InvoiceTotal>
                    <InvoiceTotalLabel>Total</InvoiceTotalLabel>
                    <InvoiceTotalValue>$1,650.00</InvoiceTotalValue>
                  </InvoiceTotal>
                </InvoiceDemo>
              </FeatureDemo>
            </FeatureCard>
          </FeaturesGrid>
        </SectionContainer>
      </FeaturesSection>

      {/* Social Media Features */}
      <SocialFeaturesSection id="social" ref={socialAnimation.ref}>
        <SectionContainer>
          <SectionHeader>
            <SectionTitle>Social Media Automation</SectionTitle>
            <SectionSubtitle>Manage your social presence from one dashboard.</SectionSubtitle>
          </SectionHeader>

          <FeaturesGrid>
            {/* Facebook Automation */}
            <FeatureCard $isVisible={socialAnimation.isVisible} $delay={0}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#2a5298">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </FeatureIcon>
              <FeatureTitle>Facebook automation</FeatureTitle>
              <FeatureDescription>
                Schedule posts, manage campaigns, and automate engagement. Connect your pages and groups effortlessly.
              </FeatureDescription>
              <FeatureDemo>
                <InvoiceDemo>
                  <InvoiceHeader>
                    <InvoiceNumber>Scheduled Posts</InvoiceNumber>
                    <InvoiceStatus>3 pending</InvoiceStatus>
                  </InvoiceHeader>
                  <InvoiceLine>
                    <InvoiceLabel>Today 10:00 AM</InvoiceLabel>
                    <InvoiceValue>Product launch</InvoiceValue>
                  </InvoiceLine>
                  <InvoiceLine>
                    <InvoiceLabel>Today 2:00 PM</InvoiceLabel>
                    <InvoiceValue>Customer story</InvoiceValue>
                  </InvoiceLine>
                  <InvoiceLine>
                    <InvoiceLabel>Tomorrow 9:00 AM</InvoiceLabel>
                    <InvoiceValue>Weekly promo</InvoiceValue>
                  </InvoiceLine>
                </InvoiceDemo>
              </FeatureDemo>
            </FeatureCard>

            {/* TikTok Automation */}
            <FeatureCard $isVisible={socialAnimation.isVisible} $delay={100}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#2a5298">
                  <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
                </svg>
              </FeatureIcon>
              <FeatureTitle>TikTok automation</FeatureTitle>
              <FeatureDescription>
                Schedule videos, track analytics, and grow your audience. Leverage TikTok's algorithm with smart timing.
              </FeatureDescription>
              <FeatureDemo>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>Video Views</InventoryName>
                    <InventoryStock>12.4K</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={75} color="#4a90e2" />
                  </ProgressBar>
                </InventoryItem>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>Engagement Rate</InventoryName>
                    <InventoryStock>8.2%</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={82} color="#4a90e2" />
                  </ProgressBar>
                </InventoryItem>
                <InventoryItem>
                  <InventoryHeader>
                    <InventoryName>New Followers</InventoryName>
                    <InventoryStock>+847</InventoryStock>
                  </InventoryHeader>
                  <ProgressBar>
                    <ProgressFill percent={60} color="#4a90e2" />
                  </ProgressBar>
                </InventoryItem>
              </FeatureDemo>
            </FeatureCard>

            {/* Cross-platform Dashboard */}
            <FeatureCard $isVisible={socialAnimation.isVisible} $delay={200}>
              <FeatureIcon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2a5298" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
              </FeatureIcon>
              <FeatureTitle>Unified dashboard</FeatureTitle>
              <FeatureDescription>
                Manage all your social accounts in one place. Schedule, analyze, and optimize across platforms.
              </FeatureDescription>
              <FeatureDemo>
                <TelegramDemo>
                  <TelegramIcon style={{ background: '#4a90e2' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                  </TelegramIcon>
                  <TelegramContent>
                    <TelegramStatus>All accounts synced</TelegramStatus>
                    <TelegramDetail>2 Facebook • 1 TikTok connected</TelegramDetail>
                  </TelegramContent>
                </TelegramDemo>
              </FeatureDemo>
            </FeatureCard>
          </FeaturesGrid>
        </SectionContainer>
      </SocialFeaturesSection>

      {/* Stats */}
      <StatsSection ref={statsAnimation.ref}>
        <StatsContainer>
          <StatsGridLarge>
            <StatItemLarge $isVisible={statsAnimation.isVisible} $delay={0}>
              <StatValueLarge>300ms</StatValueLarge>
              <StatLabelLarge>OCR processing time</StatLabelLarge>
            </StatItemLarge>
            <StatItemLarge $isVisible={statsAnimation.isVisible} $delay={100}>
              <StatValueLarge>99.2%</StatValueLarge>
              <StatLabelLarge>Recognition accuracy</StatLabelLarge>
            </StatItemLarge>
            <StatItemLarge $isVisible={statsAnimation.isVisible} $delay={200}>
              <StatValueLarge>10+</StatValueLarge>
              <StatLabelLarge>Payment methods</StatLabelLarge>
            </StatItemLarge>
            <StatItemLarge $isVisible={statsAnimation.isVisible} $delay={300}>
              <StatValueLarge>24/7</StatValueLarge>
              <StatLabelLarge>Telegram bot uptime</StatLabelLarge>
            </StatItemLarge>
          </StatsGridLarge>
        </StatsContainer>
      </StatsSection>

      {/* Pricing */}
      <PricingSection id="pricing" ref={pricingAnimation.ref}>
        <SectionContainer>
          <SectionHeader>
            <SectionTitle>Simple pricing</SectionTitle>
            <SectionSubtitle>Start free, upgrade when you're ready.</SectionSubtitle>
          </SectionHeader>

          <PricingGrid>
            {/* Free Plan */}
            <PricingCard $isVisible={pricingAnimation.isVisible} $delay={0}>
              <PlanName>Starter</PlanName>
              <PlanDescription>For small businesses getting started</PlanDescription>
              <PlanPrice>
                <PriceValue>Free</PriceValue>
              </PlanPrice>
              <PlanFeatures>
                <PlanFeature>
                  <CheckIcon viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  50 invoices/month
                </PlanFeature>
                <PlanFeature>
                  <CheckIcon viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Basic inventory
                </PlanFeature>
                <PlanFeature>
                  <CheckIcon viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  1 social account
                </PlanFeature>
                <PlanFeature>
                  <CheckIcon viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  1 user
                </PlanFeature>
              </PlanFeatures>
              <PlanButton onClick={() => navigate('/register')}>
                Get started
              </PlanButton>
            </PricingCard>

            {/* Pro Plan */}
            <PricingCard highlighted $isVisible={pricingAnimation.isVisible} $delay={100}>
              <PopularBadge>Most popular</PopularBadge>
              <PlanName highlighted>Pro</PlanName>
              <PlanDescription highlighted>For growing businesses</PlanDescription>
              <PlanPrice>
                <PriceValue highlighted>$10</PriceValue>
                <PricePeriod highlighted>/month</PricePeriod>
              </PlanPrice>
              <PlanFeatures>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Unlimited invoices
                </PlanFeature>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Telegram verification
                </PlanFeature>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Unlimited social accounts
                </PlanFeature>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Advanced scheduling
                </PlanFeature>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  5 users
                </PlanFeature>
                <PlanFeature highlighted>
                  <CheckIcon highlighted viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </CheckIcon>
                  Priority support
                </PlanFeature>
              </PlanFeatures>
              <PlanButton highlighted onClick={() => navigate('/register')}>
                Start free trial
              </PlanButton>
            </PricingCard>
          </PricingGrid>
        </SectionContainer>
      </PricingSection>

      {/* FAQ */}
      <FAQSection id="faq">
        <FAQContainer>
          <SectionHeader>
            <SectionTitle>Frequently asked questions</SectionTitle>
          </SectionHeader>

          <FAQList>
            {faqs.map((faq, i) => (
              <FAQItem key={i}>
                <FAQButton onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                  <FAQQuestion>{faq.question}</FAQQuestion>
                  <FAQIcon open={openFaq === i} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </FAQIcon>
                </FAQButton>
                <FAQAnswer $isOpen={openFaq === i}>
                  <FAQAnswerText>{faq.answer}</FAQAnswerText>
                </FAQAnswer>
              </FAQItem>
            ))}
          </FAQList>
        </FAQContainer>
      </FAQSection>

      {/* CTA */}
      <CTASection>
        <CTAContainer>
          <CTATitle>Ready to streamline your business?</CTATitle>
          <CTASubtitle>Join hundreds of businesses already using KS Automation.</CTASubtitle>
          <CTAButtons>
            <PrimaryButton onClick={() => navigate('/register')}>
              Start free trial
            </PrimaryButton>
            <SecondaryButton>
              Contact sales
            </SecondaryButton>
          </CTAButtons>
        </CTAContainer>
      </CTASection>

      {/* Footer */}
      <Footer>
        <FooterContainer>
          <FooterTop>
            <LogoWrapper>
              <LogoIcon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </LogoIcon>
              <LogoText>KS Automation</LogoText>
            </LogoWrapper>

            <FooterLinks>
              <FooterLink onClick={() => navigate('/privacy-policy')}>Privacy</FooterLink>
              <FooterLink onClick={() => navigate('/terms-of-service')}>Terms</FooterLink>
              <FooterLink>Support</FooterLink>
              <FooterLink>Contact</FooterLink>
            </FooterLinks>
          </FooterTop>

          <FooterBottom>
            <FooterCopyright>© 2025 KS Automation. All rights reserved.</FooterCopyright>
            <SocialLinks>
              <SocialLink>
                <SocialIcon viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                </SocialIcon>
              </SocialLink>
              <SocialLink>
                <SocialIcon viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </SocialIcon>
              </SocialLink>
            </SocialLinks>
          </FooterBottom>
        </FooterContainer>
      </Footer>
    </PageWrapper>
  )
}

export default HomePage
