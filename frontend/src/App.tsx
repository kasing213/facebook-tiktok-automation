import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import './i18n' // Initialize i18n
import HomePage from './components/HomePage'
import LoginPageNew from './components/LoginPageNew'
import RegisterPage from './components/RegisterPage'
import OAuthLoginPage from './components/OAuthLoginPage'
import EmailVerificationPage from './components/EmailVerificationPage'
import VerificationPendingPage from './components/VerificationPendingPage'
import ForgotPasswordPage from './components/ForgotPasswordPage'
import ResetPasswordPage from './components/ResetPasswordPage'
import PrivacyPolicy from './components/PrivacyPolicy'
import TermsOfService from './components/TermsOfService'
import DataDeletion from './components/DataDeletion'
import DashboardLayout from './components/layouts/DashboardLayout'
import OverviewPage from './components/dashboard/OverviewPage'
import UsagePage from './components/dashboard/UsagePage'
import LogsPage from './components/dashboard/LogsPage'
import SettingsPage from './components/dashboard/SettingsPage'
import { InvoiceListPage, InvoiceCreatePage, InvoiceDetailPage } from './components/dashboard/invoices'
import { InventoryListPage } from './components/dashboard/inventory'
import ClientsPage from './components/dashboard/ClientsPage'
import SocialMediaPage from './components/dashboard/SocialMediaPage'
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

// Protected Route component with token refresh support
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [authState, setAuthState] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading')

  useEffect(() => {
    const checkAuth = async () => {
      // Check if we have a valid non-expired token
      if (authService.isAuthenticated()) {
        setAuthState('authenticated')
        return
      }

      // Token is expired or missing, try to refresh
      const token = localStorage.getItem('access_token')
      if (token) {
        // Token exists but expired, attempt refresh
        try {
          const newToken = await authService.refreshToken()
          if (newToken) {
            setAuthState('authenticated')
            return
          }
        } catch {
          // Refresh failed
        }
      }

      setAuthState('unauthenticated')
    }

    checkAuth()
  }, [])

  if (authState === 'loading') {
    // Show loading spinner while checking auth
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return authState === 'authenticated' ? <>{children}</> : <Navigate to="/login" replace />
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
        <Route path="/verify-email" element={<EmailVerificationPage />} />
        <Route path="/verification-pending" element={<VerificationPendingPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
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
          <Route path="inventory" element={<InventoryListPage />} />
          <Route path="clients" element={<ClientsPage />} />
          <Route path="social" element={<SocialMediaPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App