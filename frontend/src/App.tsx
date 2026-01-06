import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from './components/HomePage'
import LoginPageNew from './components/LoginPageNew'
import RegisterPage from './components/RegisterPage'
import OAuthLoginPage from './components/OAuthLoginPage'
import PrivacyPolicy from './components/PrivacyPolicy'
import TermsOfService from './components/TermsOfService'
import DataDeletion from './components/DataDeletion'
import DashboardLayout from './components/layouts/DashboardLayout'
import OverviewPage from './components/dashboard/OverviewPage'
import UsagePage from './components/dashboard/UsagePage'
import LogsPage from './components/dashboard/LogsPage'
import SettingsPage from './components/dashboard/SettingsPage'
import { InvoiceListPage, InvoiceCreatePage, InvoiceDetailPage } from './components/dashboard/invoices'
import {
  IntegrationsOverviewPage,
  FacebookIntegrationPage,
  TikTokIntegrationPage,
  TelegramIntegrationPage,
  InvoiceIntegrationPage
} from './components/dashboard/integrations'
import {
  BillingOverviewPage,
  PricingPage,
  PaymentHistoryPage
} from './components/dashboard/billing'
import { authService } from './services/api'

// Protected Route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = authService.isAuthenticated()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPageNew />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/oauth" element={<OAuthLoginPage />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/data-deletion" element={<DataDeletion />} />

        {/* Protected dashboard routes - wrapped in layout */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<OverviewPage />} />
          <Route path="usage" element={<UsagePage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="integrations">
            <Route index element={<IntegrationsOverviewPage />} />
            <Route path="facebook" element={<FacebookIntegrationPage />} />
            <Route path="tiktok" element={<TikTokIntegrationPage />} />
            <Route path="telegram" element={<TelegramIntegrationPage />} />
            <Route path="invoice" element={<InvoiceIntegrationPage />} />
          </Route>
          <Route path="billing">
            <Route index element={<BillingOverviewPage />} />
            <Route path="pricing" element={<PricingPage />} />
            <Route path="payments" element={<PaymentHistoryPage />} />
          </Route>
          <Route path="invoices" element={<InvoiceListPage />} />
          <Route path="invoices/new" element={<InvoiceCreatePage />} />
          <Route path="invoices/:id" element={<InvoiceDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App