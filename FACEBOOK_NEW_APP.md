# New Facebook App Configuration

## App Details
- **App ID**: 768978102868207
- **App Name**: Facebook TikTok Automation V2 (or similar)
- **Created**: November 2025
- **Purpose**: Fresh start to avoid configuration issues with old app

## Configuration Applied

### OAuth Settings
- **Valid OAuth Redirect URIs**: `https://web-production-3ed15.up.railway.app/auth/facebook/callback`

### Site Settings
- **App Domains**:
  - `facebooktiktokautomation.vercel.app`
  - `web-production-3ed15.up.railway.app`
- **Site URL**: `https://facebooktiktokautomation.vercel.app/`

### Scopes
- **Current**: `public_profile` (only scope that works without Advanced Access)
- **Future**: Will need to request Advanced Access for `email`, `pages_read_engagement`, `pages_manage_posts` for full features

## Next Steps

1. ✅ Update Railway environment variables:
   - `FACEBOOK_APP_ID=768978102868207`
   - `FB_APP_ID=768978102868207`
   - `FACEBOOK_APP_SECRET=<secret>`
   - `FB_APP_SECRET=<secret>`
   - `FB_SCOPES=public_profile`

2. Test Facebook OAuth flow:
   - Register → Login → Connect Facebook
   - Should work with `public_profile` scope

3. If successful, test TikTok OAuth

4. For full features later:
   - Go to App Review → Permissions and Features
   - Request Advanced Access for needed permissions
   - Provide screencast and use case
   - Update scopes after approval

## Advantages of New App
- ✅ Clean slate - no legacy configuration issues
- ✅ You're automatically added as Administrator
- ✅ Modern app setup following 2024/2025 best practices
- ✅ Easier to manage going forward
