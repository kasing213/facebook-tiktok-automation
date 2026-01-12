import React, { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { useTenants } from '../../hooks/useAuth'
import { authService } from '../../services/api'

interface DashboardHeaderProps {
  onMenuClick: () => void
}

const HeaderContainer = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 2rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;

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
  color: #6b7280;
  width: 32px;
  height: 32px;

  &:hover {
    color: #4a90e2;
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
  background: linear-gradient(180deg, #4a90e2 0%, #2a5298 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  cursor: pointer;
`

const PageTitle = styled.h1`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;

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
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #4a90e2;
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.1);
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
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
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
  color: #1f2937;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s ease;

  &:hover {
    background: #f3f4f6;
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
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
`

const Divider = styled.div`
  height: 1px;
  background: #e5e7eb;
  margin: 0.25rem 0;
`

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ onMenuClick }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { tenants } = useTenants()
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
        <WorkspaceSelector ref={workspaceRef}>
          <WorkspaceButton onClick={() => setWorkspaceOpen(!workspaceOpen)}>
            <span>{currentTenant?.name || 'Select Workspace'}</span>
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
              Settings
            </DropdownItem>
            <Divider />
            <DropdownItem onClick={handleLogout}>
              Logout
            </DropdownItem>
          </Dropdown>
        </WorkspaceSelector>
      </RightSection>
    </HeaderContainer>
  )
}

export default DashboardHeader
