import { keyframes, css } from 'styled-components'

// ============================================
// CUSTOM EASING CURVES
// ============================================
export const easings = {
  // Standard easings
  easeOutCubic: 'cubic-bezier(0.33, 1, 0.68, 1)',
  easeInOutCubic: 'cubic-bezier(0.65, 0, 0.35, 1)',
  easeOutQuart: 'cubic-bezier(0.25, 1, 0.5, 1)',
  easeOutExpo: 'cubic-bezier(0.16, 1, 0.3, 1)',

  // Spring-like (slight overshoot)
  spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  springSmooth: 'cubic-bezier(0.34, 1.56, 0.64, 1)',

  // Smooth deceleration
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
}

// ============================================
// KEYFRAME ANIMATIONS
// ============================================

// Fade animations
export const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`

export const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`

export const fadeInDown = keyframes`
  from {
    opacity: 0;
    transform: translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`

export const fadeInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`

export const fadeInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`

// Scale animations
export const scaleIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`

export const scaleInBounce = keyframes`
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.02);
  }
  70% {
    transform: scale(0.98);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
`

// Slide animations
export const slideInUp = keyframes`
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
`

export const slideInDown = keyframes`
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
`

// Shake animation (for errors)
export const shake = keyframes`
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
`

// Pulse animation
export const pulse = keyframes`
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.85;
    transform: scale(1.02);
  }
`

// Subtle glow pulse for highlighted elements
export const glowPulse = keyframes`
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(74, 144, 226, 0.4);
  }
  50% {
    box-shadow: 0 0 20px 4px rgba(74, 144, 226, 0.15);
  }
`

// Spinner
export const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`

// Checkmark draw animation
export const drawCheck = keyframes`
  0% {
    stroke-dashoffset: 50;
  }
  100% {
    stroke-dashoffset: 0;
  }
`

// Float animation (subtle up/down)
export const float = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
`

// ============================================
// CSS HELPER - REDUCED MOTION SUPPORT
// ============================================
export const reduceMotion = css`
  @media (prefers-reduced-motion: reduce) {
    animation: none !important;
    transition-duration: 0.01ms !important;
  }
`

// ============================================
// ANIMATION HELPER FUNCTION
// ============================================
export const animate = (
  animation: ReturnType<typeof keyframes>,
  duration: string = '0.4s',
  delay: string = '0s',
  easing: string = easings.easeOutCubic,
  fillMode: string = 'both'
) => css`
  animation: ${animation} ${duration} ${easing} ${delay} ${fillMode};
  ${reduceMotion}
`

// Stagger delay helper (for lists)
export const staggerDelay = (index: number, baseDelay: number = 50) =>
  `${index * baseDelay}ms`

// ============================================
// CSS MIXINS
// ============================================

// Button hover effect mixin
export const buttonHoverEffect = css`
  transition: transform 0.2s ${easings.easeOutCubic},
              box-shadow 0.2s ${easings.easeOutCubic},
              background-color 0.2s ease,
              border-color 0.2s ease;

  &:hover:not(:disabled) {
    transform: scale(1.02) translateY(-1px);
    box-shadow: 0 6px 16px rgba(74, 144, 226, 0.25);
  }

  &:active:not(:disabled) {
    transform: scale(0.98);
    transition-duration: 0.1s;
  }

  ${reduceMotion}
`

// Secondary button hover (no scale, just color shift)
export const buttonHoverSubtle = css`
  transition: background-color 0.2s ease,
              border-color 0.2s ease,
              color 0.2s ease;

  ${reduceMotion}
`

// Card hover lift effect
export const cardHoverLift = css`
  transition: transform 0.3s ${easings.easeOutCubic},
              box-shadow 0.3s ${easings.easeOutCubic};

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
  }

  ${reduceMotion}
`

// Input focus effect
export const inputFocusEffect = css`
  transition: border-color 0.2s ease,
              box-shadow 0.2s ease,
              background-color 0.2s ease;

  &:focus {
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.12);
    outline: none;
  }

  ${reduceMotion}
`

// Smooth height transition for collapsibles
export const smoothCollapse = (isOpen: boolean, maxHeight: string = '500px') => css`
  max-height: ${isOpen ? maxHeight : '0'};
  opacity: ${isOpen ? 1 : 0};
  overflow: hidden;
  transition: max-height 0.3s ${easings.easeOutCubic},
              opacity 0.25s ${easings.easeOutCubic},
              padding 0.3s ${easings.easeOutCubic};

  ${reduceMotion}
`

// Dropdown/menu appear effect
export const dropdownAppear = (isVisible: boolean) => css`
  opacity: ${isVisible ? 1 : 0};
  transform: ${isVisible ? 'translateY(0) scale(1)' : 'translateY(-8px) scale(0.96)'};
  transform-origin: top;
  transition: opacity 0.15s ease,
              transform 0.2s ${easings.easeOutCubic};
  pointer-events: ${isVisible ? 'auto' : 'none'};

  ${reduceMotion}
`

// Table row hover
export const tableRowHover = css`
  transition: background-color 0.15s ease,
              transform 0.15s ease;

  &:hover {
    background-color: #f8fafc;
  }

  ${reduceMotion}
`

// Nav item active indicator
export const navActiveIndicator = (isActive: boolean) => css`
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #4a90e2;
    transform: scaleY(${isActive ? 1 : 0});
    transition: transform 0.2s ${easings.easeOutCubic};
  }

  ${reduceMotion}
`
