import React, { useEffect, useState } from 'react'
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



// Accordion styled components
const AccordionToggle = styled.button<{ $active: boolean; $expanded: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  width: 100%;
  border: none;
  background: ${props => props.$active ?
    'linear-gradient(135deg, rgba(74, 144, 226, 0.15) 0%, rgba(42, 82, 152, 0.15) 100%)' :
    'transparent'};
  color: ${props => props.$active ? '#4a90e2' : '#6b7280'};
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;

  &:hover {
    background: ${props => props.$active ?
      'linear-gradient(135deg, rgba(74, 144, 226, 0.2) 0%, rgba(42, 82, 152, 0.2) 100%)' :
      '#f3f4f6'};
    color: ${props => props.$active ? '#4a90e2' : '#1f2937'};
  }
`

const ChevronIcon = styled.span<{ $expanded: boolean }>`
  margin-left: auto;
  transition: transform 0.2s ease;
  transform: ${props => props.$expanded ? 'rotate(180deg)' : 'rotate(0)'};
  font-size: 0.75rem;
`

const SubMenu = styled.ul<{ $expanded: boolean }>`
  list-style: none;
  padding: 0;
  margin: 0;
  overflow: hidden;
  max-height: ${props => props.$expanded ? '500px' : '0'};
  transition: max-height 0.3s ease;
  background: #f9fafb;
`

const SubNavItem = styled(Link)<{ $active: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1.5rem 0.625rem 3rem;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  color: ${props => props.$active ? '#4a90e2' : '#6b7280'};
  background: ${props => props.$active ? '#e8f2fc' : 'transparent'};
  border-left: ${props => props.$active ? '3px solid #4a90e2' : '3px solid transparent'};

  &:hover {
    background: ${props => props.$active ? '#e8f2fc' : '#f3f4f6'};
    color: ${props => props.$active ? '#4a90e2' : '#1f2937'};
  }
`

interface MenuItem {
  path: string
  label: string
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  { path: '/dashboard', label: 'Overview' },
  { path: '/dashboard/usage', label: 'Usage' },
  { path: '/dashboard/logs', label: 'Logs' },
  {
    path: '/dashboard/integrations',
    label: 'Integrations',
    children: [
      { path: '/dashboard/integrations/facebook', label: 'Facebook' },
      { path: '/dashboard/integrations/tiktok', label: 'TikTok' },
      { path: '/dashboard/integrations/telegram', label: 'Telegram' },
      { path: '/dashboard/integrations/invoice', label: 'Invoice Generator' },
    ]
  },
  {
    path: '/dashboard/billing',
    label: 'Billing',
    children: [
      { path: '/dashboard/billing', label: 'Overview' },
      { path: '/dashboard/billing/pricing', label: 'Pricing' },
      { path: '/dashboard/billing/payments', label: 'Payment History' },
    ]
  },
  { path: '/dashboard/invoices', label: 'Invoices' },
  { path: '/dashboard/settings', label: 'Settings' }
]

const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  mobile = false,
  isOpen = false,
  onClose,
  onNavigate
}) => {
  const location = useLocation()

  // Auto-expand accordion if current path is a child route
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(() => {
    const initial = new Set<string>()
    if (location.pathname.startsWith('/dashboard/integrations')) {
      initial.add('/dashboard/integrations')
    }
    if (location.pathname.startsWith('/dashboard/billing')) {
      initial.add('/dashboard/billing')
    }
    return initial
  })

  // Update expanded state when route changes
  useEffect(() => {
    if (location.pathname.startsWith('/dashboard/integrations')) {
      setExpandedMenus(prev => new Set([...prev, '/dashboard/integrations']))
    }
    if (location.pathname.startsWith('/dashboard/billing')) {
      setExpandedMenus(prev => new Set([...prev, '/dashboard/billing']))
    }
  }, [location.pathname])

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

  const toggleAccordion = (path: string) => {
    setExpandedMenus(prev => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const isMenuActive = (basePath: string) => {
    return location.pathname.startsWith(basePath)
  }

  const renderMenuItem = (item: MenuItem) => {
    if (item.children) {
      const isExpanded = expandedMenus.has(item.path)
      const hasActiveChild = isMenuActive(item.path)

      return (
        <li key={item.path}>
          <AccordionToggle
            $active={hasActiveChild}
            $expanded={isExpanded}
            onClick={() => toggleAccordion(item.path)}
          >
            <span style={{ flex: 1 }}>{item.label}</span>
            <ChevronIcon $expanded={isExpanded}>&#9662;</ChevronIcon>
          </AccordionToggle>
          <SubMenu $expanded={isExpanded}>
            {item.children.map(child => (
              <li key={child.path}>
                <SubNavItem
                  to={child.path}
                  $active={location.pathname === child.path}
                  onClick={handleNavigate}
                >
                  {child.label}
                </SubNavItem>
              </li>
            ))}
          </SubMenu>
        </li>
      )
    }

    const isActive = location.pathname === item.path
    return (
      <li key={item.path}>
        <NavItem to={item.path} $active={isActive} onClick={handleNavigate}>
          {item.label}
        </NavItem>
      </li>
    )
  }

  // Don't render desktop sidebar on mobile devices
  if (!mobile) {
    return (
      <SidebarContainer>
        <NavList>
          {menuItems.map(renderMenuItem)}
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
          {menuItems.map(renderMenuItem)}
        </NavList>
      </SidebarContainer>
    </>
  )
}

export default DashboardSidebar
