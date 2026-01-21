// Theme color definitions for light and dark modes

export interface ThemeColors {
  // Backgrounds
  background: string
  backgroundSecondary: string
  backgroundTertiary: string

  // Cards & surfaces
  card: string
  cardHover: string

  // Borders
  border: string
  borderLight: string

  // Text
  textPrimary: string
  textSecondary: string
  textMuted: string

  // Accent (primary action color)
  accent: string
  accentDark: string
  accentLight: string
  accentLightBorder: string

  // Status colors
  success: string
  successLight: string
  warning: string
  warningLight: string
  error: string
  errorLight: string

  // Overlay
  overlay: string

  // Shadows
  shadowColor: string
}

export const lightTheme: ThemeColors = {
  // Backgrounds
  background: '#ffffff',
  backgroundSecondary: '#f8f9fa',
  backgroundTertiary: '#f9fafb',

  // Cards & surfaces
  card: '#ffffff',
  cardHover: '#f9fafb',

  // Borders
  border: '#e5e7eb',
  borderLight: '#f3f4f6',

  // Text
  textPrimary: '#1f2937',
  textSecondary: '#6b7280',
  textMuted: '#9ca3af',

  // Accent (blue for light mode)
  accent: '#4a90e2',
  accentDark: '#2a5298',
  accentLight: '#e8f4fd',
  accentLightBorder: '#d1e7f8',

  // Status colors
  success: '#10b981',
  successLight: '#d1fae5',
  warning: '#f59e0b',
  warningLight: '#fef3c7',
  error: '#ef4444',
  errorLight: '#fee2e2',

  // Overlay
  overlay: 'rgba(0, 0, 0, 0.5)',

  // Shadows
  shadowColor: 'rgba(0, 0, 0, 0.1)',
}

export const darkTheme: ThemeColors = {
  // Backgrounds (Supabase-style dark)
  background: '#171717',
  backgroundSecondary: '#1c1c1c',
  backgroundTertiary: '#242424',

  // Cards & surfaces
  card: '#242424',
  cardHover: '#2a2a2a',

  // Borders
  border: '#2e2e2e',
  borderLight: '#3a3a3a',

  // Text
  textPrimary: '#f8f8f8',
  textSecondary: '#a0a0a0',
  textMuted: '#6b6b6b',

  // Accent (Supabase green for dark mode)
  accent: '#3ECF8E',
  accentDark: '#2da36e',
  accentLight: 'rgba(62, 207, 142, 0.15)',
  accentLightBorder: 'rgba(62, 207, 142, 0.3)',

  // Status colors (slightly adjusted for dark mode)
  success: '#3ECF8E',
  successLight: 'rgba(62, 207, 142, 0.15)',
  warning: '#f59e0b',
  warningLight: 'rgba(245, 158, 11, 0.15)',
  error: '#ef4444',
  errorLight: 'rgba(239, 68, 68, 0.15)',

  // Overlay
  overlay: 'rgba(0, 0, 0, 0.7)',

  // Shadows
  shadowColor: 'rgba(0, 0, 0, 0.3)',
}

export type ThemeMode = 'light' | 'dark'
