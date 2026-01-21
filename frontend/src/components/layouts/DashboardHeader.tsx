import React, { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'
import { useTenants } from '../../hooks/useAuth'
import { authService } from '../../services/api'
import { useTheme } from '../../contexts/ThemeContext'
import LanguageSwitcher from './LanguageSwitcher'

interface DashboardHeaderProps {
  onMenuClick: () => void
}

const HeaderContainer = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 2rem;
  background: ${props => props.theme.card};
  border-bottom: 1px solid ${props => props.theme.border};
  transition: background-color 0.3s ease, border-color 0.3s ease;

  @media (max-width: 768px) {
    padding: 0 1rem;
  }
`

const LeftSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`

const HamburgerButton = styled.button`
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  color: ${props => props.theme.textSecondary};
  width: 32px;
  height: 32px;

  &:hover {
    color: ${props => props.theme.accent};
  }

  @media (max-width: 768px) {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
  }
`

const HamburgerLine = styled.span`
  display: block;
  width: 20px;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
`

const Logo = styled.div`
  font-family: 'Roboto', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(180deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  cursor: pointer;
`

const PageTitle = styled.h1`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0;
  transition: color 0.3s ease;

  @media (max-width: 480px) {
    font-size: 1rem;
  }
`

const RightSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1.5rem;

  @media (max-width: 480px) {
    gap: 1rem;
  }
`

const WorkspaceSelector = styled.div`
  position: relative;
`

const WorkspaceButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${props => props.theme.accent};
    box-shadow: 0 2px 8px ${props => props.theme.shadowColor};
  }

  @media (max-width: 480px) {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }
`

const Dropdown = styled.div<{ isOpen: boolean }>`
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  box-shadow: 0 10px 25px ${props => props.theme.shadowColor};
  min-width: 200px;
  opacity: ${props => props.isOpen ? 1 : 0};
  visibility: ${props => props.isOpen ? 'visible' : 'hidden'};
  transform: ${props => props.isOpen ? 'translateY(0)' : 'translateY(-10px)'};
  transition: all 0.2s ease;
  z-index: 200;
`

const DropdownItem = styled.button`
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  font-size: 0.875rem;
  color: ${props => props.theme.textPrimary};
  cursor: pointer;
  text-align: left;
  transition: background 0.2s ease;

  &:hover {
    background: ${props => props.theme.cardHover};
  }

  &:first-child {
    border-radius: 8px 8px 0 0;
  }

  &:last-child {
    border-radius: 0 0 8px 8px;
  }
`

const UserAvatar = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
  }
`

const Divider = styled.div`
  height: 1px;
  background: ${props => props.theme.border};
  margin: 0.25rem 0;
`

const ThemeToggle = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid ${props => props.theme.border};
  background: ${props => props.theme.card};
  color: ${props => props.theme.textSecondary};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${props => props.theme.accent};
    color: ${props => props.theme.accent};
    background: ${props => props.theme.accentLight};
  }

  svg {
    width: 18px;
    height: 18px;
  }
`

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ onMenuClick }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const { tenants } = useTenants()
  const { mode, toggleTheme } = useTheme()
  const [workspaceOpen, setWorkspaceOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const workspaceRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)

  // Get current tenant from localStorage or use first tenant
  const currentTenantId = localStorage.getItem('selectedTenantId') || (tenants[0]?.id || '')
  const currentTenant = tenants.find(t => t.id === currentTenantId) || tenants[0]

  // Get page title from current route
  const getPageTitle = () => {
    const path = location.pathname
    if (path === '/dashboard') return 'Overview'
    if (path.includes('/usage')) return 'Usage'
    if (path.includes('/logs')) return 'Logs'
    // Integration sub-pages
    if (path === '/dashboard/integrations/facebook') return 'Facebook Integration'
    if (path === '/dashboard/integrations/tiktok') return 'TikTok Integration'
    if (path === '/dashboard/integrations/telegram') return 'Telegram Integration'
    if (path === '/dashboard/integrations/invoice') return 'Invoice Generator'
    if (path === '/dashboard/integrations/stripe') return 'Stripe Payments'
    if (path.includes('/integrations')) return 'Integrations'
    if (path.includes('/invoices')) return 'Invoices'
    if (path.includes('/settings')) return 'Settings'
    return 'Dashboard'
  }

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (workspaceRef.current && !workspaceRef.current.contains(event.target as Node)) {
        setWorkspaceOpen(false)
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleTenantSwitch = (tenantId: string) => {
    localStorage.setItem('selectedTenantId', tenantId)
    setWorkspaceOpen(false)
    window.location.reload() // Reload to refresh auth status with new tenant
  }

  const handleLogout = async () => {
    await authService.logout()
    navigate('/login')
  }

  return (
    <HeaderContainer>
      <LeftSection>
        <HamburgerButton onClick={onMenuClick}>
          <HamburgerLine />
          <HamburgerLine />
          <HamburgerLine />
        </HamburgerButton>
        <Logo onClick={() => navigate('/')}>KS</Logo>
        <PageTitle>{getPageTitle()}</PageTitle>
      </LeftSection>

      <RightSection>
        <ThemeToggle onClick={toggleTheme} title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
          {mode === 'dark' ? (
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </ThemeToggle>

        <LanguageSwitcher />

        <WorkspaceSelector ref={workspaceRef}>
          <WorkspaceButton onClick={() => setWorkspaceOpen(!workspaceOpen)}>
            <span>{currentTenant?.name || t('header.selectWorkspace')}</span>
            <span style={{ fontSize: '0.625rem' }}>{workspaceOpen ? '\u25B2' : '\u25BC'}</span>
          </WorkspaceButton>
          <Dropdown isOpen={workspaceOpen}>
            {tenants.map(tenant => (
              <DropdownItem
                key={tenant.id}
                onClick={() => handleTenantSwitch(tenant.id)}
              >
                {tenant.name}
                {tenant.id === currentTenantId && <span style={{ marginLeft: 'auto', color: '#4a90e2' }}>&#10003;</span>}
              </DropdownItem>
            ))}
          </Dropdown>
        </WorkspaceSelector>

        <WorkspaceSelector ref={userMenuRef}>
          <UserAvatar onClick={() => setUserMenuOpen(!userMenuOpen)}>
            U
          </UserAvatar>
          <Dropdown isOpen={userMenuOpen}>
            <DropdownItem onClick={() => navigate('/dashboard/settings')}>
              {t('header.settings')}
            </DropdownItem>
            <Divider />
            <DropdownItem onClick={handleLogout}>
              {t('header.logout')}
            </DropdownItem>
          </Dropdown>
        </WorkspaceSelector>
      </RightSection>
    </HeaderContainer>
  )
}

export default DashboardHeader
