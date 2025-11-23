# Facebook App Review Submission Guide

## URLs to Update in Facebook App Settings

### Privacy Policy URL
```
https://facebooktiktokautomation.vercel.app/privacy-policy
```

### Terms of Service URL
```
https://facebooktiktokautomation.vercel.app/terms-of-service
```

### User Data Deletion Callback URL (REQUIRED for App Review)
```
https://web-production-3ed15.up.railway.app/data-deletion/facebook
```

### Data Deletion Instructions URL
```
https://facebooktiktokautomation.vercel.app/data-deletion
```

### App Domain
```
facebooktiktokautomation.vercel.app
railway.app
web-production-3ed15.up.railway.app
```

### Valid OAuth Redirect URIs
```
https://web-production-3ed15.up.railway.app/auth/facebook/callback
https://facebooktiktokautomation.vercel.app/oauth-callback
```

---

## Screencast Script (What to Record)

### Video Requirements:
- **Length**: 2-5 minutes
- **Tool**: Use OBS Studio, Loom, or screen recording software
- **Quality**: 720p minimum, show clear UI interactions
- **Audio**: Optional but helpful to narrate what you're doing

### Recording Steps:

#### Scene 1: Landing Page (10 seconds)
1. Open: https://facebooktiktokautomation.vercel.app
2. Show the homepage with login/register buttons
3. Narrate: "This is the Facebook/TikTok Automation app homepage"

#### Scene 2: User Registration (30 seconds)
1. Click "Register" or "Sign Up"
2. Fill out registration form:
   - Username: `demo_user`
   - Email: `demo@example.com`
   - Password: `DemoPassword123`
3. Click "Register"
4. Show successful registration message
5. Narrate: "Users can create an account with email and password"

#### Scene 3: Login (20 seconds)
1. If redirected, go back to login page
2. Login with the demo credentials
3. Show successful login
4. Narrate: "Users login with their credentials"

#### Scene 4: Dashboard (30 seconds)
1. Show the main dashboard
2. Point out key features:
   - User profile section
   - "Connect Facebook" button
   - "Connect TikTok" button
3. Narrate: "The dashboard allows users to connect their social media accounts"

#### Scene 5: Facebook OAuth Flow (60-90 seconds) **MOST IMPORTANT**
1. Click "Connect Facebook" button
2. Show the Facebook OAuth dialog appears
3. **Important**: Show the permission request screen clearly:
   - public_profile
   - email
   - pages_show_list (if requesting)
4. Click "Continue" or "Authorize"
5. Show redirect back to your app
6. Show connected Facebook account with:
   - User's Facebook name
   - Profile picture
   - List of managed pages (if pages_show_list granted)
7. Narrate: "Users authorize Facebook permissions to connect their account. We request public_profile and email for authentication, and pages_show_list to display the pages they manage."

#### Scene 6: Page Analytics/Data Display (30 seconds)
1. If you have page data, show it
2. If not, show placeholder or "No pages found" message
3. Show what data you plan to display (engagement metrics, etc.)
4. Narrate: "Once connected, users can view their Facebook pages and engagement metrics"

#### Scene 7: Disconnect Account (20 seconds)
1. Show "Disconnect" or "Remove" button for Facebook account
2. Click it
3. Show confirmation and account removed
4. Narrate: "Users can disconnect their accounts at any time"

### Video Upload:
- Upload to YouTube (unlisted or public)
- Copy the YouTube URL
- Paste it in the App Review submission form

---

## App Review Form - Exact Text to Use

### Field 1: Reviewer Instructions (instructions-web-2)

```
**How to Test Our Application:**

1. Visit: https://facebooktiktokautomation.vercel.app

2. Create a test account:
   - Click "Register" or "Sign Up"
   - Use any email and password
   - No email verification required for testing

3. After logging in, you'll see the Dashboard

4. Test Facebook Integration:
   - Click "Connect Facebook" button
   - You'll be redirected to Facebook OAuth
   - Authorize the requested permissions:
     * public_profile - To display your name and profile picture
     * email - For account creation and communication
     * pages_show_list - To list the Facebook Pages you manage
   - After authorization, you'll be redirected back to our app
   - Your connected Facebook account will be displayed

5. What You'll See:
   - Your Facebook profile information
   - List of Facebook Pages you manage (if any)
   - Page engagement metrics (if pages_read_engagement is granted)

**Use of Facebook Login:**

We use Facebook Login ONLY for user authentication and to access the user's managed Facebook Pages. We do NOT use any other Meta APIs. Specifically:

- **Authentication**: We use Facebook Login as an OAuth provider to authenticate users
- **Pages Access**: We request `pages_show_list` to display which Facebook Pages the user manages
- **Page Analytics**: We request `pages_read_engagement` to show page performance metrics (likes, reach, engagement)

We do NOT access, store, or process any data beyond what is necessary for displaying page analytics to the user.

**Data Handling:**

- All OAuth tokens are encrypted and stored securely
- Users can disconnect their Facebook account at any time
- When disconnected, all associated tokens are deleted
- We comply with Facebook Platform Terms and Data Use Policy

**Privacy Policy**: https://facebooktiktokautomation.vercel.app/privacy-policy
**Terms of Service**: https://facebooktiktokautomation.vercel.app/terms-of-service
```

### Field 2: Access Codes (accesscode-web-1) - OPTIONAL

```
**No payment or membership is required.**

You can create a free account at: https://facebooktiktokautomation.vercel.app/register

Test Credentials (if needed):
- Email: reviewer@test.com
- Password: ReviewerTest123

Or simply create a new account using any email address - no verification required for testing.

All features are immediately accessible after registration.
```

---

## What Permissions Are You Requesting?

Based on your current configuration, you're requesting:

1. ✅ **public_profile** (Default - Always granted)
   - Use: Display user's name and profile picture

2. ✅ **email** (Default - Always granted)
   - Use: User authentication and account creation

3. 🟡 **pages_show_list** (Standard Access - May require justification)
   - Use: List the Facebook Pages the user manages
   - Justification: "We display the user's managed Facebook Pages in our dashboard to allow them to select which pages to monitor and analyze."

4. 🔴 **pages_read_engagement** (Advanced Access - Requires App Review)
   - Use: Read page engagement metrics
   - Justification: "We provide analytics and insights for the user's Facebook Pages, including engagement metrics such as likes, shares, comments, and reach. This helps users understand their page performance."

---

## After Deployment: Update Facebook App Settings

### 1. Basic Settings
Go to: https://developers.facebook.com/apps/1536800164835472/settings/basic/

Update:
- **Privacy Policy URL**: `https://facebooktiktokautomation.vercel.app/privacy-policy`
- **Terms of Service URL**: `https://facebooktiktokautomation.vercel.app/terms-of-service`
- **App Domains**: Add all three domains mentioned above

### 2. Facebook Login Settings
Go to: https://developers.facebook.com/apps/1536800164835472/fb-login/settings/

Update:
- **Valid OAuth Redirect URIs**: Add both callback URLs mentioned above

---

## Timeline

- **Submission**: Today
- **Facebook Review**: 3-7 business days (typically)
- **Approval Notification**: Via email and Facebook Developer Dashboard
- **If Rejected**: You'll receive feedback on what to fix

---

## Tips for Approval

✅ **DO**:
- Make sure your app actually works before submitting
- Ensure privacy policy is accessible and complete
- Show clear use case for each permission
- Make the screencast clear and easy to follow
- Test the OAuth flow yourself first

❌ **DON'T**:
- Request more permissions than you need
- Have broken links or errors in your app
- Submit without a working privacy policy
- Rush the submission - test thoroughly first

---

## Next Steps

1. ✅ Deploy the updated frontend to Vercel (with Privacy Policy)
2. ✅ Update Facebook App Settings with new URLs
3. 📹 Record the screencast (2-5 minutes)
4. 📝 Fill out the App Review form with text above
5. ✅ Submit for review
6. ⏳ Wait for Facebook's response (3-7 days)

Need help with any of these steps? Let me know!
