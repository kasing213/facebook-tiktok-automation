import React, { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import styled from 'styled-components'

interface DashboardSidebarProps {
  mobile?: boolean
  isOpen?: boolean
  onClose?: () => void
  onNavigate?: () => void
}

const SidebarContainer = styled.nav<{ $mobile?: boolean; $isOpen?: boolean }>`
  width: 250px;
  background: white;
  border-right: 1px solid #e5e7eb;
  height: calc(100vh - 60px);
  overflow-y: auto;
  padding: 1.5rem 0;

  ${props => props.$mobile && `
    position: fixed;
    top: 60px;
    left: ${props.$isOpen ? '0' : '-250px'};
    z-index: 150;
    box-shadow: ${props.$isOpen ? '2px 0 8px rgba(0, 0, 0, 0.1)' : 'none'};
    transition: left 0.3s ease;
  `}
`

const Overlay = styled.div<{ $isOpen: boolean }>`
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 140;
  opacity: ${props => props.$isOpen ? 1 : 0};
  visibility: ${props => props.$isOpen ? 'visible' : 'hidden'};
  transition: all 0.3s ease;
`

const NavList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`

const NavItem = styled(Link)<{ $active: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  text-decoration: none;
  font-size: 0.9375rem;
  font-weight: 500;
  transition: all 0.2s ease;

  color: ${props => props.$active ? 'white' : '#6b7280'};
  background: ${props => props.$active ?
    'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)' :
    'transparent'};

  &:hover {
    background: ${props => props.$active ?
      'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)' :
      '#f3f4f6'};
    color: ${props => props.$active ? 'white' : '#1f2937'};
  }
`

const NavIcon = styled.span`
  font-size: 1.125rem;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
`

const NavLabel = styled.span`
  flex: 1;
`

const menuItems = [
  { path: '/dashboard', label: 'Overview', icon: '📊' },
  { path: '/dashboard/usage', label: 'Usage', icon: '📈' },
  { path: '/dashboard/logs', label: 'Logs', icon: '📄' },
  { path: '/dashboard/integrations', label: 'Integrations', icon: '🔌' },
  { path: '/dashboard/settings', label: 'Settings', icon: '⚙️' }
]

const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  mobile = false,
  isOpen = false,
  onClose,
  onNavigate
}) => {
  const location = useLocation()

  // Close sidebar when route changes (mobile only)
  useEffect(() => {
    if (mobile && isOpen && onClose) {
      onClose()
    }
  }, [location.pathname])

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (mobile && isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [mobile, isOpen])

  const handleNavigate = () => {
    if (onNavigate) {
      onNavigate()
    }
  }

  // Don't render desktop sidebar on mobile devices
  if (!mobile) {
    return (
      <SidebarContainer>
        <NavList>
          {menuItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <li key={item.path}>
                <NavItem to={item.path} $active={isActive}>
                  <NavIcon>{item.icon}</NavIcon>
                  <NavLabel>{item.label}</NavLabel>
                </NavItem>
              </li>
            )
          })}
        </NavList>
      </SidebarContainer>
    )
  }

  // Mobile sidebar with overlay
  return (
    <>
      <Overlay $isOpen={isOpen} onClick={onClose} />
      <SidebarContainer $mobile $isOpen={isOpen}>
        <NavList>
          {menuItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <li key={item.path}>
                <NavItem
                  to={item.path}
                  $active={isActive}
                  onClick={handleNavigate}
                >
                  <NavIcon>{item.icon}</NavIcon>
                  <NavLabel>{item.label}</NavLabel>
                </NavItem>
              </li>
            )
          })}
        </NavList>
      </SidebarContainer>
    </>
  )
}

export default DashboardSidebar
