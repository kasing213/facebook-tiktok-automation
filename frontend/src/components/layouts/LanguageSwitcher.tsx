import React from 'react'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'

const SwitchContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 0.25rem;
`

const LanguageButton = styled.button<{ isActive: boolean }>`
  padding: 0.375rem 0.625rem;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${props => props.isActive ? 'white' : 'transparent'};
  color: ${props => props.isActive ? '#4a90e2' : '#6b7280'};
  box-shadow: ${props => props.isActive ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none'};

  &:hover {
    color: ${props => props.isActive ? '#4a90e2' : '#1f2937'};
  }
`

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation()
  const currentLang = i18n.language

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('language', lang)
  }

  return (
    <SwitchContainer>
      <LanguageButton
        isActive={currentLang === 'en'}
        onClick={() => changeLanguage('en')}
      >
        EN
      </LanguageButton>
      <LanguageButton
        isActive={currentLang === 'km'}
        onClick={() => changeLanguage('km')}
      >
        ខ្មែរ
      </LanguageButton>
    </SwitchContainer>
  )
}

export default LanguageSwitcher
