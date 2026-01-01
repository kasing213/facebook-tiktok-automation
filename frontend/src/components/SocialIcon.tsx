import React from 'react'
import styled from 'styled-components'
import facebookLogo from '../assets/images/social/facebook-logo.png'
import tiktokLogo from '../assets/images/social/tiktok-logo.png'

// Type-safe platform union
export type SocialPlatform = 'facebook' | 'tiktok'

interface SocialIconProps {
  platform: SocialPlatform
  size?: 'small' | 'medium' | 'large'
  className?: string // Allows styled-components composition
}

// Size mapping for different contexts
const sizeMap = {
  small: '20px',
  medium: '24px',
  large: '28px'
}

const IconImage = styled.img<{ $size: string }>`
  width: ${props => props.$size};
  height: ${props => props.$size};
  display: inline-block;
  vertical-align: middle;
  object-fit: contain;
`

const SocialIcon: React.FC<SocialIconProps> = ({
  platform,
  size = 'medium',
  className
}) => {
  const iconMap: Record<SocialPlatform, string> = {
    facebook: facebookLogo,
    tiktok: tiktokLogo
  }

  const altTextMap: Record<SocialPlatform, string> = {
    facebook: 'Facebook',
    tiktok: 'TikTok'
  }

  return (
    <IconImage
      src={iconMap[platform]}
      alt={altTextMap[platform]}
      $size={sizeMap[size]}
      className={className}
      loading="lazy"
    />
  )
}

export default SocialIcon
