import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from './components/HomePage'
import LoginPageNew from './components/LoginPageNew'
import RegisterPage from './components/RegisterPage'
import OAuthLoginPage from './components/OAuthLoginPage'
import Dashboard from './components/Dashboard'
import PrivacyPolicy from './components/PrivacyPolicy'
import TermsOfService from './components/TermsOfService'
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

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App