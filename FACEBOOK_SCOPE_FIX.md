# Facebook OAuth Scope Fix

## Problem
Facebook returned error: **Invalid Scopes: email, pages_show_list**

This means these permissions are now deprecated or require app review.

## Solution

Update the `FB_SCOPES` environment variable in Railway to use only the default scope that works without app review.

### Railway Environment Variable Update

1. Go to your Railway project: https://railway.app
2. Select the `web` service
3. Go to **Variables** tab
4. Find or add the variable: `FB_SCOPES`
5. Set the value to: `public_profile`
6. Click **Save** (this will trigger a redeploy)

### Current Facebook Permissions (2024+)

**No App Review Needed:**
- `public_profile` - Default scope, always available (user ID, name, profile picture)

**Requires App Review:**
- `email` - User email address (changed in 2024, now requires review)
- `pages_read_engagement` - Read page engagement metrics (requires review)
- `pages_manage_posts` - Post to pages (requires review)
- `ads_read` - Read ad account data (requires review)
- `business_management` - Manage Business Manager assets (requires review)

**Deprecated:**
- `pages_show_list` - Use `pages_read_engagement` instead

### For Testing with Advanced Scopes

If you want to test with more permissions BEFORE app review:

1. **Add Test Users** in Facebook App Dashboard:
   - Go to https://developers.facebook.com/apps
   - Select your app → **Roles** → **Test Users**
   - Click "Add Test Users" or "Create Test Users"

2. **Test users can use ANY scope** without app review:
   ```
   FB_SCOPES=public_profile,pages_read_engagement,pages_manage_posts,ads_read
   ```

3. Login to your app using test user credentials

### Recommended Scopes for Your App

**For Initial Testing (No Review):**
```
FB_SCOPES=public_profile
```

**For Full Features (Requires App Review OR Test Users):**
```
FB_SCOPES=public_profile,pages_read_engagement,pages_manage_posts,ads_read,business_management
```

### After Railway Update

1. Wait 2-3 minutes for Railway to redeploy
2. Go back to Dashboard: https://facebooktiktokautomation.vercel.app/dashboard
3. Click "Connect Facebook" again
4. Should now work with just `public_profile` scope

### App Review Preparation

Once you've tested with test users and are ready for production:

1. **Create Screencast** showing:
   - Registration → Login → Connect Facebook
   - How your app uses each permission
   - Why each permission is necessary for your app

2. **Submit for Review**:
   - Go to Facebook App Dashboard → App Review → Permissions and Features
   - Select each scope you need
   - Upload screencast and provide detailed explanation
   - Submit for review

3. **Required URLs** (already configured in your app):
   - Privacy Policy: https://facebooktiktokautomation.vercel.app/privacy-policy
   - Terms of Service: https://facebooktiktokautomation.vercel.app/terms-of-service
   - Data Deletion: https://facebooktiktokautomation.vercel.app/data-deletion

## Quick Fix Steps

**OPTION 1: Use Basic Scope (Recommended for now)**
1. Update Railway: `FB_SCOPES=public_profile`
2. Redeploy (automatic)
3. Test Facebook connection

**OPTION 2: Use Test Users (For full feature testing)**
1. Create test users in Facebook App Dashboard
2. Update Railway: `FB_SCOPES=public_profile,pages_read_engagement,ads_read`
3. Redeploy
4. Login with test user account
5. Connect Facebook
6. Test all features
7. Create screencast for app review
