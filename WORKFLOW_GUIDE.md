# Complete Workflow Guide: Registration to OAuth Connection

This guide covers the complete user workflow from registration to connecting Facebook and TikTok accounts for testing and app review preparation.

## What Was Fixed

### 1. Registration Error: "Failed to get organization"
**Problem**: The registration page was trying to fetch a tenant from `/api/tenants`, but if no tenant existed in the database, it would fail.

**Solution**:
- Created a new backend endpoint `/api/tenants/default` that automatically creates a default tenant if none exists
- Updated frontend to use this new endpoint
- Now registration works seamlessly even with an empty database

### 2. OAuth Scopes for Testing (Before App Review)

#### Facebook Scopes
**Current Configuration** (in `.env`):
```
FB_SCOPES=public_profile,email,pages_show_list
```

**Scope Breakdown**:
- ✅ `public_profile` - Access to user ID, name, profile picture (NO review needed)
- ✅ `email` - Access to user email (NO review needed)
- ✅ `pages_show_list` - List pages the user manages (Limited review needed)

**For Testing with Test Users**:
- Test users can use ALL scopes without app review
- Add test users in Facebook App Dashboard → Roles → Test Users
- Test users can test advanced scopes like `ads_read`, `pages_manage_posts`, etc.

#### TikTok Scopes
**Current Configuration** (in `.env`):
```
TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats
```

**Scope Breakdown**:
- ✅ `user.info.basic` - Get basic user profile (username, display name, avatar)
- ✅ `user.info.profile` - Extended profile info (bio, links, verification status)
- ✅ `user.info.stats` - Get user stats (followers, likes, video count)

**Note**: Video scopes (`video.publish`, `video.upload`) require TikTok app approval/audit. Use these basic scopes for initial testing.

## Complete User Workflow

### Step 1: Register a New Account

1. **Navigate to Registration Page**
   - URL: `https://facebooktiktokautomation.vercel.app/register`
   - Or click "Sign Up" from the login page

2. **Fill in Registration Form**
   - Email: Your valid email address
   - Username: Choose a unique username
   - Password: At least 8 characters
   - Confirm Password: Re-enter your password

3. **Submit**
   - Click "REGISTER" button
   - The system will automatically:
     - Create a default organization if none exists
     - Create your user account
     - Link you to the default organization
   - You'll be redirected to the login page after successful registration

### Step 2: Login

1. **Navigate to Login Page**
   - URL: `https://facebooktiktokautomation.vercel.app/login`

2. **Enter Credentials**
   - Username: The username you registered with
   - Password: Your password

3. **Submit**
   - Click "LOG IN" button
   - You'll be redirected to the Dashboard

### Step 3: Connect Facebook Account

1. **On the Dashboard**
   - You'll see two cards: Facebook and TikTok
   - Facebook card will show "Not Connected" status in red

2. **Click "Connect Facebook" Button**
   - This initiates the Facebook OAuth flow
   - You'll be redirected to Facebook's authorization page

3. **Authorize on Facebook**
   - Log in to Facebook if not already logged in
   - Review the permissions being requested:
     - Access your public profile
     - Access your email address
     - See your Pages list
   - Click "Continue" or "Authorize"

4. **OAuth Callback**
   - Facebook redirects back to your app
   - The backend exchanges the authorization code for access tokens
   - Your Facebook account is now connected!

5. **Verify Connection**
   - You'll be redirected back to the Dashboard
   - Facebook card should now show "Connected" status in green
   - You'll see your connected Facebook account details

### Step 4: Connect TikTok Account

1. **On the Dashboard**
   - TikTok card will show "Not Connected" status in red

2. **Click "Connect TikTok" Button**
   - This initiates the TikTok OAuth flow
   - You'll be redirected to TikTok's authorization page

3. **Authorize on TikTok**
   - Log in to TikTok if not already logged in
   - Review the permissions being requested:
     - Access your basic profile info
     - Access your extended profile
     - Access your account statistics
   - Click "Authorize" or "Confirm"

4. **OAuth Callback**
   - TikTok redirects back to your app
   - The backend exchanges the authorization code for access tokens
   - Your TikTok account is now connected!

5. **Verify Connection**
   - You'll be redirected back to the Dashboard
   - TikTok card should now show "Connected" status in green
   - You'll see your connected TikTok account details

## Testing with Facebook Test Users

For testing advanced scopes (like ad management) before app review:

1. **Create Test Users in Facebook App Dashboard**
   - Go to https://developers.facebook.com/apps
   - Select your app → Roles → Test Users
   - Click "Add Test Users"

2. **Update Scopes for Testing** (Optional)
   - Edit `.env` file:
     ```
     FB_SCOPES=public_profile,email,pages_show_list,ads_read,pages_manage_posts
     ```
   - Restart the backend server

3. **Login with Test User**
   - Register/Login to your app using test user credentials
   - Connect Facebook using the test user account
   - Test user can authorize advanced scopes without app review

## Preparing for App Review

### Facebook App Review

1. **Required Items for Submission**
   - App Icon (1024x1024)
   - Privacy Policy URL: `https://facebooktiktokautomation.vercel.app/privacy-policy`
   - Terms of Service URL: `https://facebooktiktokautomation.vercel.app/terms-of-service`
   - Data Deletion Instructions: `https://facebooktiktokautomation.vercel.app/data-deletion`

2. **Create Screen Recording**
   - Use this complete workflow guide to create a screencast
   - Show: Registration → Login → Facebook Connection → Features
   - Demonstrate why you need each scope:
     - `pages_show_list` - To show user which pages they manage
     - `pages_manage_posts` - To post content to their pages
     - `ads_read` - To read their ad campaign data

3. **Submit for Review**
   - Go to Facebook App Dashboard → App Review → Permissions and Features
   - Request the scopes you need
   - Upload your screencast
   - Provide detailed explanations

### TikTok App Review

1. **Apply for Scopes**
   - Go to https://developers.tiktok.com/apps
   - Select your app → Apply for Permissions
   - Request `video.publish` and `video.upload` if needed

2. **Create Screen Recording**
   - Show the same workflow: Registration → Login → TikTok Connection
   - Demonstrate your video publishing features

3. **Submit Application**
   - Provide detailed use case
   - Upload screencast
   - Wait for approval (usually 3-7 business days)

## Troubleshooting

### "Failed to get organization" Error
**Fixed!** The new endpoint auto-creates a default organization.

### Facebook OAuth Scope Error
- **Error**: "Invalid scope"
- **Solution**: Make sure your `.env` has valid scopes
- **For Testing**: Use test users for advanced scopes
- **For Production**: Submit for app review first

### TikTok OAuth Scope Error
- **Error**: "Scope not authorized"
- **Solution**: Check that you're only using approved scopes
- **Current**: `user.info.basic,user.info.profile,user.info.stats` work without review
- **For Video**: Submit app for review to get `video.publish` scope

### Connection Doesn't Show on Dashboard
- Click the "Refresh" button
- Check browser console for errors
- Verify the tenant_id is correct in the URL

## Environment Variables Summary

**Current `.env` Configuration**:
```env
# Facebook OAuth
FACEBOOK_APP_ID=1536800164835472
FACEBOOK_APP_SECRET=d1bfce9e058edbb1a660cf74ecb26b2b
FB_SCOPES=public_profile,email,pages_show_list

# TikTok OAuth - Production
TIKTOK_CLIENT_ID=7555418840261167116
TIKTOK_CLIENT_SECRET=aRlS7f5d3JQfsi8ITuwUdHKKO0nwkZ8S
TIKTOK_CLIENT_KEY=awgperuwx6xm78g3
TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats

# Frontend & Backend URLs
BASE_URL=https://web-production-3ed15.up.railway.app
FRONTEND_URL=https://facebooktiktokautomation.vercel.app
```

## Files Modified

1. **Backend**:
   - [app/main.py](app/main.py:209-239) - Added `/api/tenants/default` endpoint

2. **Frontend**:
   - [frontend/src/services/tenant.ts](frontend/src/services/tenant.ts) - Updated to use new endpoint

3. **Configuration**:
   - [.env](.env:58) - Facebook scopes configured for testing
   - [.env](.env:78) - TikTok scopes configured for testing

## Next Steps

1. **Test the Complete Workflow**
   - Register → Login → Connect Facebook → Connect TikTok
   - Verify all connections show on Dashboard

2. **Create Screencast for App Review**
   - Follow this guide step-by-step
   - Record your screen showing the workflow
   - Narrate why you need each permission

3. **Submit for App Review**
   - Facebook: App Dashboard → App Review
   - TikTok: Developer Portal → Apply for Permissions

4. **After Approval**
   - Update scopes in `.env` with approved advanced scopes
   - Deploy updated configuration
   - Test with real users

---

**Ready to test!** Start with registration and follow the workflow guide above.
