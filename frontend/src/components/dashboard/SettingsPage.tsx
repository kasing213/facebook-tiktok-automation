import React, { useState } from 'react'
import styled from 'styled-components'

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
  color: ${props => props.$active ? '#4a90e2' : '#6b7280'};
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid ${props => props.$active ? '#4a90e2' : 'transparent'};
  margin-bottom: -2px;
  transition: all 0.2s ease;
  white-space: nowrap;

  &:hover {
    color: #4a90e2;
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
    border-color: #4a90e2;
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
    border-color: #4a90e2;
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
  background: ${props => props.$active ? 'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)' : '#d1d5db'};
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
`

const PrimaryButton = styled(Button)`
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
`

const SecondaryButton = styled(Button)`
  background: white;
  color: #6b7280;
  border: 1px solid #e5e7eb;

  &:hover {
    border-color: #4a90e2;
    color: #4a90e2;
  }
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
`

const ApiKeyBox = styled.div`
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #1f2937;
  word-break: break-all;
  margin-bottom: 1rem;
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
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
`

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'account' | 'workspace' | 'notifications' | 'api-keys'>('account')
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [campaignNotifications, setCampaignNotifications] = useState(true)
  const [weeklyReports, setWeeklyReports] = useState(false)

  const renderTabContent = () => {
    switch (activeTab) {
      case 'account':
        return (
          <TabContent>
            <FormSection>
              <SectionTitle>Personal Information</SectionTitle>
              <FormRow>
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  defaultValue="John Doe"
                  disabled
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  defaultValue="john.doe@example.com"
                  disabled
                />
              </FormRow>
            </FormSection>

            <FormSection>
              <SectionTitle>Change Password</SectionTitle>
              <FormRow>
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  placeholder="Enter current password"
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  placeholder="Enter new password"
                />
              </FormRow>
              <FormRow>
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm new password"
                />
              </FormRow>
            </FormSection>

            <ButtonGroup>
              <PrimaryButton onClick={() => alert('Account settings saved!')}>
                Save Changes
              </PrimaryButton>
              <SecondaryButton>Cancel</SecondaryButton>
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
                <MemberItem>
                  <MemberInfo>
                    <MemberName>John Doe</MemberName>
                    <MemberEmail>john.doe@example.com</MemberEmail>
                  </MemberInfo>
                  <MemberRole>Owner</MemberRole>
                </MemberItem>
                <MemberItem>
                  <MemberInfo>
                    <MemberName>Jane Smith</MemberName>
                    <MemberEmail>jane.smith@example.com</MemberEmail>
                  </MemberInfo>
                  <MemberRole>Admin</MemberRole>
                </MemberItem>
                <MemberItem>
                  <MemberInfo>
                    <MemberName>Bob Johnson</MemberName>
                    <MemberEmail>bob.johnson@example.com</MemberEmail>
                  </MemberInfo>
                  <MemberRole>Member</MemberRole>
                </MemberItem>
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
              <SectionTitle>Email Notifications</SectionTitle>
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
              <PrimaryButton onClick={() => alert('Notification settings saved!')}>
                Save Preferences
              </PrimaryButton>
            </ButtonGroup>
          </TabContent>
        )

      case 'api-keys':
        return (
          <TabContent>
            <FormSection>
              <SectionTitle>API Keys</SectionTitle>
              <InfoBox>
                <InfoText>
                  API keys allow you to integrate with our platform programmatically. Keep your keys secure and never share them publicly.
                </InfoText>
              </InfoBox>

              <FormRow>
                <Label>Your API Key</Label>
                <ApiKeyBox>
                  demo_1234567890abcdefghijklmnopqrstuvwxyz1234567890
                </ApiKeyBox>
              </FormRow>

              <FormRow>
                <Label>Webhook URL (Optional)</Label>
                <Input
                  type="url"
                  placeholder="https://your-domain.com/webhook"
                  defaultValue=""
                />
              </FormRow>
            </FormSection>

            <ButtonGroup>
              <PrimaryButton onClick={() => alert('New API key generated!')}>
                Generate New Key
              </PrimaryButton>
              <SecondaryButton>Revoke Key</SecondaryButton>
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
        <Tab
          $active={activeTab === 'api-keys'}
          onClick={() => setActiveTab('api-keys')}
        >
          API Keys
        </Tab>
      </TabNavigation>

      {renderTabContent()}
    </Container>
  )
}

export default SettingsPage
