import { Routes, Route } from 'react-router-dom'
import OAuthLoginPage from './components/OAuthLoginPage'
import OAuthCallback from './components/OAuthCallback'
import Dashboard from './components/Dashboard'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<OAuthLoginPage />} />
        <Route path="/oauth/callback" element={<OAuthCallback />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </div>
  )
}

export default App