import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import styled from 'styled-components'

// Color constants
const COLORS = {
  primary: '#4a90e2',
  primaryDark: '#2a5298',
  primaryLight: '#e8f4fd',
  primaryLightBorder: '#d1e7f8',
  success: '#10b981',
  textPrimary: '#1f2937',
  textSecondary: '#6b7280',
  textMuted: '#9ca3af',
  border: '#e5e7eb',
  borderLight: '#f3f4f6',
  bgLight: '#f9fafb',
}

interface DashboardSidebarProps {
  mobile?: boolean
  isOpen?: boolean
  onClose?: () => void
  onNavigate?: () => void
}

const SidebarContainer = styled.nav<{ $mobile?: boolean; $isOpen?: boolean }>`
  width: 250px;
  background: white;
  border-right: 1px solid ${COLORS.border};
  height: calc(100vh - 60px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;

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

// Branding header
const BrandingHeader = styled.div`
  padding: 1.25rem 1rem;
  border-bottom: 1px solid ${COLORS.borderLight};
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

const BrandLogo = styled.div`
  width: 36px;
  height: 36px;
  background: ${COLORS.primary};
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.875rem;
`

const BrandName = styled.span`
  font-weight: 600;
  font-size: 1rem;
  color: ${COLORS.textPrimary};
`

// Navigation sections
const NavContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
`

const NavSection = styled.div`
  margin-bottom: 0.5rem;
`

const SectionLabel = styled.div`
  padding: 0.75rem 1rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${COLORS.textMuted};
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
  padding: 0.625rem 1rem;
  margin: 0.125rem 0.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
  color: ${props => props.$active ? COLORS.primary : COLORS.textSecondary};
  background: ${props => props.$active ? COLORS.primaryLight : 'transparent'};

  &:hover {
    background: ${props => props.$active ? COLORS.primaryLight : COLORS.bgLight};
    color: ${props => props.$active ? COLORS.primary : COLORS.textPrimary};
  }

  svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }
`

// Accordion styled components
const AccordionToggle = styled.button<{ $active: boolean; $expanded: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  margin: 0.125rem 0.5rem;
  border-radius: 8px;
  width: calc(100% - 1rem);
  border: none;
  background: ${props => props.$active ? COLORS.primaryLight : 'transparent'};
  color: ${props => props.$active ? COLORS.primary : COLORS.textSecondary};
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;

  &:hover {
    background: ${props => props.$active ? COLORS.primaryLight : COLORS.bgLight};
    color: ${props => props.$active ? COLORS.primary : COLORS.textPrimary};
  }

  svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }
`

const ChevronIcon = styled.span<{ $expanded: boolean }>`
  margin-left: auto;
  transition: transform 0.2s ease;
  transform: ${props => props.$expanded ? 'rotate(180deg)' : 'rotate(0)'};
  font-size: 0.625rem;
  color: ${COLORS.textMuted};
`

const SubMenu = styled.ul<{ $expanded: boolean }>`
  list-style: none;
  padding: 0;
  margin: 0;
  overflow: hidden;
  max-height: ${props => props.$expanded ? '500px' : '0'};
  transition: max-height 0.3s ease;
`

const SubNavItem = styled(Link)<{ $active: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem 0.5rem 2.75rem;
  margin: 0.125rem 0.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all 0.15s ease;
  color: ${props => props.$active ? COLORS.primary : COLORS.textSecondary};
  background: ${props => props.$active ? COLORS.primaryLight : 'transparent'};

  &:hover {
    background: ${props => props.$active ? COLORS.primaryLight : COLORS.bgLight};
    color: ${props => props.$active ? COLORS.primary : COLORS.textPrimary};
  }
`

// Subscription card at bottom
const SubscriptionCard = styled.div`
  margin: 0.5rem;
  padding: 0.875rem 1rem;
  background: ${COLORS.bgLight};
  border: 1px solid ${COLORS.border};
  border-radius: 10px;
`

const SubscriptionHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
`

const SubscriptionPlan = styled.span`
  font-size: 0.875rem;
  font-weight: 600;
  color: ${COLORS.textPrimary};
`

const SubscriptionBadge = styled.span`
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  background: rgba(16, 185, 129, 0.1);
  color: ${COLORS.success};
`

const SubscriptionDate = styled.div`
  font-size: 0.75rem;
  color: ${COLORS.textMuted};
`

// Icons as SVG components
const HomeIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
  </svg>
)

const ShareIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
  </svg>
)

const DocumentIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
)

const BoxIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
  </svg>
)

const MegaphoneIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a20.845 20.845 0 01-1.44-4.282m3.102.069a18.03 18.03 0 01-.59-4.59c0-1.586.205-3.124.59-4.59m0 9.18a23.848 23.848 0 018.835 2.535M10.34 6.66a23.847 23.847 0 008.835-2.535m0 0A23.74 23.74 0 0018.795 3m.38 1.125a23.91 23.91 0 011.014 5.395m-1.014 8.855c-.118.38-.245.754-.38 1.125m.38-1.125a23.91 23.91 0 001.014-5.395m0-3.46c.495.413.811 1.035.811 1.73 0 .695-.316 1.317-.811 1.73m0-3.46a24.347 24.347 0 010 3.46" />
  </svg>
)

const UsersIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
  </svg>
)

const LinkIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
  </svg>
)

const CogIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

// Menu item icons mapping
const getIcon = (label: string) => {
  switch (label) {
    case 'Overview':
      return <HomeIcon />
    case 'Social Media':
      return <ShareIcon />
    case 'Invoices':
      return <DocumentIcon />
    case 'Inventory':
      return <BoxIcon />
    case 'Ads Alert':
      return <MegaphoneIcon />
    case 'Clients':
      return <UsersIcon />
    case 'Integrations':
      return <LinkIcon />
    case 'Settings':
      return <CogIcon />
    default:
      return null
  }
}

// Grouped menu structure
interface MenuItem {
  path: string
  label: string
  children?: MenuItem[]
}

interface MenuGroup {
  label: string
  items: MenuItem[]
}

const menuGroups: MenuGroup[] = [
  {
    label: 'MAIN',
    items: [
      { path: '/dashboard', label: 'Overview' },
    ]
  },
  {
    label: 'SERVICES',
    items: [
      { path: '/dashboard/social', label: 'Social Media' },
      { path: '/dashboard/invoices', label: 'Invoices' },
      { path: '/dashboard/inventory', label: 'Inventory' },
      { path: '/dashboard/ads-alert', label: 'Ads Alert' },
      { path: '/dashboard/clients', label: 'Clients' },
    ]
  },
  {
    label: 'SETTINGS',
    items: [
      {
        path: '/dashboard/integrations',
        label: 'Integrations',
        children: [
          { path: '/dashboard/integrations/facebook', label: 'Facebook' },
          { path: '/dashboard/integrations/tiktok', label: 'TikTok' },
          { path: '/dashboard/integrations/telegram', label: 'Telegram' },
        ]
      },
      { path: '/dashboard/settings', label: 'Settings' },
    ]
  }
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
    return initial
  })

  // Update expanded state when route changes
  useEffect(() => {
    if (location.pathname.startsWith('/dashboard/integrations')) {
      setExpandedMenus(prev => new Set([...prev, '/dashboard/integrations']))
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

  const isExactMatch = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard'
    }
    return location.pathname === path || location.pathname.startsWith(path + '/')
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
            {getIcon(item.label)}
            <span style={{ flex: 1 }}>{item.label}</span>
            <ChevronIcon $expanded={isExpanded}>▾</ChevronIcon>
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

    const isActive = isExactMatch(item.path)
    return (
      <li key={item.path}>
        <NavItem to={item.path} $active={isActive} onClick={handleNavigate}>
          {getIcon(item.label)}
          {item.label}
        </NavItem>
      </li>
    )
  }

  const renderSidebarContent = () => (
    <>
      <BrandingHeader>
        <BrandLogo>KS</BrandLogo>
        <BrandName>KS Automation</BrandName>
      </BrandingHeader>

      <NavContent>
        {menuGroups.map(group => (
          <NavSection key={group.label}>
            <SectionLabel>{group.label}</SectionLabel>
            <NavList>
              {group.items.map(renderMenuItem)}
            </NavList>
          </NavSection>
        ))}
      </NavContent>

      <SubscriptionCard>
        <SubscriptionHeader>
          <SubscriptionPlan>Pro Plan</SubscriptionPlan>
          <SubscriptionBadge>Active</SubscriptionBadge>
        </SubscriptionHeader>
        <SubscriptionDate>Renews Jan 15, 2026</SubscriptionDate>
      </SubscriptionCard>
    </>
  )

  // Don't render desktop sidebar on mobile devices
  if (!mobile) {
    return (
      <SidebarContainer>
        {renderSidebarContent()}
      </SidebarContainer>
    )
  }

  // Mobile sidebar with overlay
  return (
    <>
      <Overlay $isOpen={isOpen} onClick={onClose} />
      <SidebarContainer $mobile $isOpen={isOpen}>
        {renderSidebarContent()}
      </SidebarContainer>
    </>
  )
}

export default DashboardSidebar
