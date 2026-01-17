import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { authService } from '../../services/api'
import { User } from '../../types/auth'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2rem;
`

const TabNavigation = styled.div`
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 2rem;
  overflow-x: auto;
`

const Tab = styled.button<{ $active: boolean }>`
  padding: 0.875rem 1.5rem;
  border: none;
  background: transparent;
  color: ${props => props.$active ? '#10b981' : '#6b7280'};
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid ${props => props.$active ? '#10b981' : 'transparent'};
  margin-bottom: -2px;
  transition: all 0.2s ease;
  white-space: nowrap;

  &:hover {
    color: #10b981;
  }
`

const TabContent = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;

  @media (max-width: 768px) {
    padding: 1.5rem;
  }
`

const FormSection = styled.div`
  margin-bottom: 2rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const SectionTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
`

const FormRow = styled.div`
  margin-bottom: 1.5rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const Label = styled.label`
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.5rem;
`

const Input = styled.input`
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
    border-color: #10b981;
  }

  &:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }
`

const Textarea = styled.textarea`
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  resize: vertical;
  min-height: 100px;

  &:focus {
    outline: none;
    border-color: #10b981;
  }
`

const ToggleWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 1rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const ToggleLabel = styled.div`
  flex: 1;
`

const ToggleLabelText = styled.div`
  font-size: 0.9375rem;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
`

const ToggleLabelDescription = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`

const Toggle = styled.button<{ $active: boolean }>`
  width: 48px;
  height: 28px;
  background: ${props => props.$active ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : '#d1d5db'};
  border: none;
  border-radius: 14px;
  cursor: pointer;
  position: relative;
  transition: background 0.3s ease;

  &::after {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    top: 4px;
    left: ${props => props.$active ? '24px' : '4px'};
    transition: left 0.3s ease;
  }
`

const Button = styled.button`
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const PrimaryButton = styled(Button)`
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }
`

const SecondaryButton = styled(Button)`
  background: white;
  color: #6b7280;
  border: 1px solid #e5e7eb;

  &:hover:not(:disabled) {
    border-color: #10b981;
    color: #10b981;
  }
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
`

const InfoBox = styled.div`
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
`

const InfoText = styled.p`
  font-size: 0.875rem;
  color: #1e40af;
  margin: 0;
  line-height: 1.5;
`

const MembersList = styled.div`
  margin-top: 1rem;
`

const MemberItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 0.75rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const MemberInfo = styled.div`
  flex: 1;
`

const MemberName = styled.div`
  font-size: 0.9375rem;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
`

const MemberEmail = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`

const MemberRole = styled.span`
  padding: 0.25rem 0.75rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
`

// New styled components for email verification
const EmailRow = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
`

const VerificationBadge = styled.span<{ $verified: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background: ${props => props.$verified ? '#d1fae5' : '#fef3c7'};
  color: ${props => props.$verified ? '#065f46' : '#92400e'};
`

const VerifyButton = styled(Button)`
  background: #fbbf24;
  color: #1f2937;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;

  &:hover:not(:disabled) {
    background: #f59e0b;
  }
`

const SuccessMessage = styled.div`
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #065f46;
  font-size: 0.875rem;
  margin-bottom: 1rem;
`

const ErrorMessage = styled.div`
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #991b1b;
  font-size: 0.875rem;
  margin-bottom: 1rem;
`

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6b7280;
`

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'account' | 'workspace' | 'notifications'>('account')

  // User state
  const [user, setUser] = useState<User | null>(null)
  const [userLoading, setUserLoading] = useState(true)

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)
  const [changingPassword, setChangingPassword] = useState(false)

  // Email verification state
  const [sendingVerification, setSendingVerification] = useState(false)
  const [verificationSent, setVerificationSent] = useState(false)
  const [verificationError, setVerificationError] = useState<string | null>(null)
  const [manualToken, setManualToken] = useState('')
  const [verifyingToken, setVerifyingToken] = useState(false)
  const [tokenError, setTokenError] = useState<string | null>(null)

  // Notification preferences
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [campaignNotifications, setCampaignNotifications] = useState(true)
  const [weeklyReports, setWeeklyReports] = useState(false)
  const [notificationSaved, setNotificationSaved] = useState(false)

  // Load user data on mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await authService.getCurrentUser()
        setUser(userData)
      } catch (error) {
        console.error('Failed to fetch user:', error)
      } finally {
        setUserLoading(false)
      }
    }
    fetchUser()
  }, [])

  // Load notification preferences from localStorage
  useEffect(() => {
    const savedNotifications = localStorage.getItem('notification_settings')
    if (savedNotifications) {
      try {
        const settings = JSON.parse(savedNotifications)
        setEmailNotifications(settings.emailNotifications ?? true)
        setCampaignNotifications(settings.campaignNotifications ?? true)
        setWeeklyReports(settings.weeklyReports ?? false)
      } catch {
        // Ignore parse errors
      }
    }
  }, [])

  const handleChangePassword = async () => {
    setPasswordError(null)
    setPasswordSuccess(null)

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('All password fields are required')
      return
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters')
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match')
      return
    }

    setChangingPassword(true)

    try {
      await authService.changePassword(currentPassword, newPassword)
      setPasswordSuccess('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: any) {
      setPasswordError(error.message || 'Failed to change password')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleSendVerification = async () => {
    setSendingVerification(true)
    setVerificationError(null)
    try {
      await authService.sendVerificationEmail()
      setVerificationSent(true)
    } catch (error: any) {
      setVerificationError(error.message || 'Failed to send verification email')
    } finally {
      setSendingVerification(false)
    }
  }

  const handleVerifyToken = async () => {
    if (!manualToken.trim()) {
      setTokenError('Please enter the verification code')
      return
    }

    if (manualToken.trim().length < 32) {
      setTokenError('Invalid verification code format')
      return
    }

    setVerifyingToken(true)
    setTokenError(null)

    try {
      await authService.verifyEmail(manualToken.trim())
      // Refresh user data to show verified status
      const userData = await authService.getCurrentUser()
      setUser(userData)
      setVerificationSent(false)
      setManualToken('')
    } catch (error: any) {
      setTokenError(error.message || 'Invalid or expired verification code')
    } finally {
      setVerifyingToken(false)
    }
  }

  const handleCancelPassword = () => {
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
    setPasswordError(null)
    setPasswordSuccess(null)
  }

  const handleSaveNotifications = () => {
    const settings = {
      emailNotifications,
      campaignNotifications,
      weeklyReports
    }
    localStorage.setItem('notification_settings', JSON.stringify(settings))
    setNotificationSaved(true)
    setTimeout(() => setNotificationSaved(false), 3000)
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'account':
        return (
          <TabContent>
            <FormSection>
              <SectionTitle>Personal Information</SectionTitle>
              {userLoading ? (
                <LoadingSpinner>Loading user data...</LoadingSpinner>
              ) : (
                <>
                  <FormRow>
                    <Label htmlFor="fullName">Username</Label>
                    <Input
                      id="fullName"
                      type="text"
                      value={user?.username || ''}
                      disabled
                    />
                  </FormRow>
                  <FormRow>
                    <Label htmlFor="email">Email Address</Label>
                    <EmailRow>
                      <Input
                        id="email"
                        type="email"
                        value={user?.email || ''}
                        disabled
                        style={{ flex: 1, minWidth: '200px' }}
                      />
                      <VerificationBadge $verified={user?.email_verified ?? false}>
                        {user?.email_verified ? '✓ Verified' : '! Unverified'}
                      </VerificationBadge>
                      {!user?.email_verified && user?.email && (
                        <VerifyButton
                          onClick={handleSendVerification}
                          disabled={sendingVerification || verificationSent}
                        >
                          {sendingVerification ? 'Sending...' : verificationSent ? 'Email Sent' : 'Verify Email'}
                        </VerifyButton>
                      )}
                    </EmailRow>
                    {verificationSent && (
                      <InfoBox style={{ marginTop: '0.75rem' }}>
                        <InfoText>
                          Verification email sent! Please check your inbox and click the verification link.
                        </InfoText>
                        <div style={{ marginTop: '1rem', borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
                          <Label style={{ marginBottom: '0.5rem', fontSize: '0.8125rem' }}>
                            Or enter verification code from email:
                          </Label>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <Input
                              type="text"
                              placeholder="Paste verification code here"
                              value={manualToken}
                              onChange={(e) => setManualToken(e.target.value)}
                              style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.8125rem' }}
                            />
                            <VerifyButton
                              onClick={handleVerifyToken}
                              disabled={verifyingToken || !manualToken.trim()}
                              style={{ whiteSpace: 'nowrap' }}
                            >
                              {verifyingToken ? 'Verifying...' : 'Verify'}
                            </VerifyButton>
                          </div>
                          {tokenError && (
                            <ErrorMessage style={{ marginTop: '0.5rem', fontSize: '0.8125rem' }}>
                              {tokenError}
                            </ErrorMessage>
                          )}
                        </div>
                      </InfoBox>
                    )}
                    {verificationError && (
                      <ErrorMessage style={{ marginTop: '0.75rem' }}>
                        {verificationError}
                      </ErrorMessage>
                    )}
                  </FormRow>
                  <FormRow>
                    <Label>Role</Label>
                    <Input
                      type="text"
                      value={user?.role === 'admin' ? 'Owner' : user?.role === 'user' ? 'Member' : user?.role || ''}
                      disabled
                    />
                  </FormRow>
                </>
              )}
            </FormSection>

            <FormSection>
              <SectionTitle>Change Password</SectionTitle>
              {passwordSuccess && <SuccessMessage>{passwordSuccess}</SuccessMessage>}
              {passwordError && <ErrorMessage>{passwordError}</ErrorMessage>}
              <FormRow>
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  placeholder="Enter new password (min 8 characters)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </FormRow>
            </FormSection>

            <ButtonGroup>
              <PrimaryButton
                onClick={handleChangePassword}
                disabled={changingPassword}
              >
                {changingPassword ? 'Saving...' : 'Save Changes'}
              </PrimaryButton>
              <SecondaryButton onClick={handleCancelPassword}>Cancel</SecondaryButton>
            </ButtonGroup>
          </TabContent>
        )

      case 'workspace':
        return (
          <TabContent>
            <FormSection>
              <SectionTitle>Workspace Details</SectionTitle>
              <FormRow>
                <Label htmlFor="workspaceName">Workspace Name</Label>
                <Input
                  id="workspaceName"
                  type="text"
                  defaultValue="My Workspace"
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="workspaceDescription">Description</Label>
                <Textarea
                  id="workspaceDescription"
                  placeholder="Describe your workspace..."
                  defaultValue="Main workspace for social media automation"
                />
              </FormRow>
            </FormSection>

            <FormSection>
              <SectionTitle>Team Members</SectionTitle>
              <MembersList>
                {user && (
                  <MemberItem>
                    <MemberInfo>
                      <MemberName>{user.username}</MemberName>
                      <MemberEmail>{user.email}</MemberEmail>
                    </MemberInfo>
                    <MemberRole>{user.role === 'admin' ? 'Owner' : user.role === 'user' ? 'Member' : 'Viewer'}</MemberRole>
                  </MemberItem>
                )}
              </MembersList>
            </FormSection>

            <ButtonGroup>
              <PrimaryButton onClick={() => alert('Workspace settings saved!')}>
                Save Changes
              </PrimaryButton>
              <SecondaryButton>Invite Member</SecondaryButton>
            </ButtonGroup>
          </TabContent>
        )

      case 'notifications':
        return (
          <TabContent>
            <FormSection>
              <SectionTitle>Notification Preferences</SectionTitle>
              {notificationSaved && (
                <SuccessMessage>Notification preferences saved!</SuccessMessage>
              )}
              <ToggleWrapper>
                <ToggleLabel>
                  <ToggleLabelText>Email notifications</ToggleLabelText>
                  <ToggleLabelDescription>
                    Receive email notifications for important updates
                  </ToggleLabelDescription>
                </ToggleLabel>
                <Toggle
                  $active={emailNotifications}
                  onClick={() => setEmailNotifications(!emailNotifications)}
                />
              </ToggleWrapper>

              <ToggleWrapper>
                <ToggleLabel>
                  <ToggleLabelText>Campaign notifications</ToggleLabelText>
                  <ToggleLabelDescription>
                    Get notified when campaigns start, finish, or encounter errors
                  </ToggleLabelDescription>
                </ToggleLabel>
                <Toggle
                  $active={campaignNotifications}
                  onClick={() => setCampaignNotifications(!campaignNotifications)}
                />
              </ToggleWrapper>

              <ToggleWrapper>
                <ToggleLabel>
                  <ToggleLabelText>Weekly reports</ToggleLabelText>
                  <ToggleLabelDescription>
                    Receive weekly performance reports every Monday
                  </ToggleLabelDescription>
                </ToggleLabel>
                <Toggle
                  $active={weeklyReports}
                  onClick={() => setWeeklyReports(!weeklyReports)}
                />
              </ToggleWrapper>
            </FormSection>

            <ButtonGroup>
              <PrimaryButton onClick={handleSaveNotifications}>
                Save Preferences
              </PrimaryButton>
            </ButtonGroup>
          </TabContent>
        )
    }
  }

  return (
    <Container>
      <Title>Settings</Title>

      <TabNavigation>
        <Tab
          $active={activeTab === 'account'}
          onClick={() => setActiveTab('account')}
        >
          Account
        </Tab>
        <Tab
          $active={activeTab === 'workspace'}
          onClick={() => setActiveTab('workspace')}
        >
          Workspace
        </Tab>
        <Tab
          $active={activeTab === 'notifications'}
          onClick={() => setActiveTab('notifications')}
        >
          Notifications
        </Tab>
      </TabNavigation>

      {renderTabContent()}
    </Container>
  )
}

export default SettingsPage
