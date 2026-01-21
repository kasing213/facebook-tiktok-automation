import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import styled from 'styled-components'
import DashboardHeader from './DashboardHeader'
import DashboardSidebar from './DashboardSidebar'

const LayoutGrid = styled.div`
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main";
  grid-template-columns: 250px 1fr;
  grid-template-rows: 60px 1fr;
  min-height: 100vh;
  background: ${props => props.theme.backgroundSecondary};
  transition: background-color 0.3s ease;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "main";
  }
`

const HeaderArea = styled.div`
  grid-area: header;
  position: sticky;
  top: 0;
  z-index: 100;
`

const SidebarArea = styled.div`
  grid-area: sidebar;
  @media (max-width: 768px) {
    display: none;
  }
`

const MainContentArea = styled.main`
  grid-area: main;
  padding: 2rem;
  overflow-y: auto;

  @media (max-width: 768px) {
    padding: 1.5rem;
  }

  @media (max-width: 480px) {
    padding: 1rem;
  }
`

const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  return (
    <LayoutGrid>
      <HeaderArea>
        <DashboardHeader onMenuClick={toggleSidebar} />
      </HeaderArea>

      <SidebarArea>
        <DashboardSidebar onNavigate={closeSidebar} />
      </SidebarArea>

      {/* Mobile sidebar overlay */}
      <DashboardSidebar
        mobile
        isOpen={sidebarOpen}
        onClose={closeSidebar}
        onNavigate={closeSidebar}
      />

      <MainContentArea>
        <Outlet />
      </MainContentArea>
    </LayoutGrid>
  )
}

export default DashboardLayout
