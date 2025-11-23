# Facebook App Setup - Fix "App Needs At Least One Supported Permission"

## Problem
Facebook shows: **"This app needs at least one supported permission"**

This means your Facebook App doesn't have any permissions enabled in the App Dashboard, even for basic OAuth login.

## Solution: Enable Permissions in Facebook App Dashboard

### Step 1: Go to Facebook App Dashboard

1. Open: https://developers.facebook.com/apps
2. Select your app: **App ID 1536800164835472**
3. You should see your app name in the dashboard

### Step 2: Add Facebook Login Product

1. In the left sidebar, look for **"Add Product"** or **"Products"**
2. Find **"Facebook Login"**
3. Click **"Set Up"** or **"Configure"** if it's not already added

### Step 3: Enable Required Permissions

**Option A: Use Basic Permissions (No Review Needed)**

This will work immediately for testing:

1. Go to **App Review** → **Permissions and Features**
2. Find and enable these permissions:
   - ✅ **`public_profile`** - Should be enabled by default
   - ✅ **`user_friends`** - Often enabled by default

3. Under **"Standard Access"** or **"Default Permissions"**:
   - Make sure `public_profile` is listed

**Option B: Request Additional Permissions (For Full Features)**

For screencast and full features, you'll need to request these:

1. Go to **App Review** → **Permissions and Features**
2. Click **"Request Advanced Access"** for:
   - `pages_read_engagement` - To see pages user manages
   - `pages_manage_posts` - To post content
   - `instagram_basic` - If you want Instagram support (optional)

3. For each permission:
   - Click "Request Advanced Access"
   - You'll need to provide:
     - **App verification** (if not done)
     - **Screencast** showing how you use the permission
     - **Explanation** of why you need it

### Step 4: Configure OAuth Redirect URIs

1. Go to **Facebook Login** → **Settings**
2. Under **"Valid OAuth Redirect URIs"**, add:
   ```
   https://web-production-3ed15.up.railway.app/auth/facebook/callback
   ```
3. Click **"Save Changes"**

### Step 5: Make App Live (If In Development Mode)

1. Go to **Settings** → **Basic**
2. Scroll down to **"App Mode"**
3. If it says **"Development"**, you have two options:

   **Option A: Keep in Development + Add Test Users (Recommended for now)**
   - Stay in Development mode
   - Go to **Roles** → **Test Users**
   - Create test users
   - Test users can use ANY permission without app review

   **Option B: Switch to Live Mode (Requires App Review)**
   - Toggle to **"Live"** mode
   - This requires completing App Review first

### Step 6: Update Railway Environment Variable

Based on which option you chose:

**If Using Basic Permissions (Development + Regular Users):**
```
FB_SCOPES=public_profile,user_friends
```

**If Using Test Users (Can use any scope):**
```
FB_SCOPES=public_profile,pages_read_engagement,pages_manage_posts
```

Update in Railway:
1. Go to Railway → Your project → web service
2. Variables tab
3. Update `FB_SCOPES`
4. Save (will redeploy)

## For Screencast Recording

To prepare for screencast and app review:

### Recommended Approach: Use Test Users

1. **Create Test Users**:
   - Facebook App Dashboard → Roles → Test Users
   - Create 1-2 test users
   - Note their email and password

2. **Set Scopes for Full Features**:
   ```
   FB_SCOPES=public_profile,pages_read_engagement,pages_manage_posts,ads_read
   ```

3. **Test Complete Workflow**:
   - Register in your app
   - Login with test user account
   - Connect Facebook (will work with all scopes)
   - Test all features
   - Record the screencast showing:
     - User registration
     - Facebook OAuth connection
     - How you use each permission
     - Why you need each permission

4. **Submit for App Review**:
   - Upload screencast
   - Explain each permission's use case
   - Reference your Privacy Policy and Terms of Service

## Quick Fix Right Now

**Minimum to get OAuth working:**

1. ✅ Go to Facebook App Dashboard
2. ✅ Add **Facebook Login** product if not added
3. ✅ Add OAuth Redirect URI: `https://web-production-3ed15.up.railway.app/auth/facebook/callback`
4. ✅ Update Railway `FB_SCOPES` to: `public_profile,user_friends`
5. ✅ Create 1 test user (Roles → Test Users)
6. ✅ Test with the test user account

This should immediately fix the "app needs at least one supported permission" error!

## Verification

After making changes:
1. Wait 1-2 minutes
2. Go to your Dashboard: https://facebooktiktokautomation.vercel.app/dashboard
3. Click "Connect Facebook"
4. Should see Facebook login screen (not error)
5. Authorize with test user credentials
6. Should redirect back with successful connection ✅

---

**Priority Actions:**
1. Add Facebook Login product
2. Add OAuth redirect URI
3. Create test user
4. Update FB_SCOPES to include at least 2 permissions
