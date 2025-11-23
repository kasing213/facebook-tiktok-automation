# Facebook/TikTok Automation — Actionable TODO (2025-11-22)

This list consolidates everything that is still outstanding after the latest deployment fixes. Knock out the items in priority order so the production stack stays aligned with reality.

---

## 1. Immediate Production Checks
- [x] **Confirm Railway deploy finished** — `railway status` now shows the prod app running; `/auth/login`, `/auth/me`, and `/api/tenants/.../auth-status` all returned 200 (tenant `2618029f-9fe5-48a2-881b-fc724dbf28ba`).
- [x] **Verify Vercel build** — The browser console reports `https://web-production-3ed15.up.railway.app` as `VITE_API_URL`, and registration/login calls complete without the old "Network Error".
- [x] **Monitor backend logs** — Logs captured at 2025-11-22 13:53-13:54 show healthy startup, CORS config, and OAuth initiations for both Facebook and TikTok.
- [x] **Supabase sanity check** — Connection + schema validation completed (7 tables detected); new accounts land in the expected tenant.

---

## 2. OAuth Credentials & Redirects (Blockers for social logins)
- [ ] **Populate Railway secrets** — Set `FB_APP_ID`, `FB_APP_SECRET`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `OAUTH_STATE_SECRET` via `railway variables`.
- [ ] **Match redirect URIs** — Update Facebook Developer + TikTok portals with both Railway (`https://web-production-3ed15.up.railway.app/auth/<platform>/callback`) and Vercel (`https://facebooktiktokautomation.vercel.app/oauth/<platform>/callback`) URLs.
- [ ] **Re-test dashboard buttons** — From `/dashboard`, click “Connect Facebook/TikTok” and verify you reach the provider login page, then ensure the callbacks persist tokens in Supabase `ad_token`.
- [ ] **Document secrets storage** — Record how/where credentials are stored for hand-off (e.g., Railway variables snapshot in `CREDENTIALS_INVENTORY.md`).

---

## 3. QA & Observability
- [ ] **Run full `TESTING_CHECKLIST.md`** — Registration, login, protected route redirect, multi-user scenarios, and CORS/caching checks.
- [ ] **Extended browser coverage** — Validate Chrome/Firefox/Safari/Edge plus mobile Safari/Chrome; capture screenshots for regressions.
- [ ] **Add structured logging** — Ensure FastAPI logs tenant ID, user ID, and OAuth outcomes for easier debugging.
- [ ] **Alerting/monitoring** — Decide on Railway/Vercel uptime monitors or integrate a simple health-check pinger.

---

## 4. Security & Account Management Enhancements
- [ ] Email verification flow for new accounts.
- [ ] Password reset (request + token + update endpoints).
- [ ] Session timeout / refresh tokens (optional but recommended).
- [ ] Admin dashboard for tenant management (roles, user list, manual OAuth disconnect).
- [ ] Review encryption for `ad_token` (confirm key rotation plan for `MASTER_SECRET_KEY`).

---

## 5. Automation Roadmap (post-auth work)
- [ ] Telegram bot core (command handling, tenant linking) — see `app/bot.py`.
- [ ] Automation scheduler service (job definitions + background worker or external scheduler).
- [ ] Report generation for Facebook/TikTok metrics with delivery destinations.
- [ ] Alerting/notification destinations (Telegram, webhook, email) management UI.
- [ ] Advanced analytics / campaign optimization modules.

---

## 6. Documentation Cleanup
- [ ] Align `SETUP_SUMMARY.md`, `FRONTEND_IMPLEMENTATION.md`, and `DEPLOYMENT_SETUP.md` with the current deployment state to avoid claims that everything is already production-ready.
- [ ] Trim redundant instructions across `QUICK_FIX_GUIDE.md`, `SUPABASE_TESTING_GUIDE.md`, and `TESTING_CHECKLIST.md`; point them to the single source of truth where possible.
- [ ] Keep `CURRENT_STATUS.md` synced with the checklist above whenever a task flips to ✅.

---

### Next Update Window
Once the first two sections are complete (deploy verifications + OAuth credentials), schedule a mini review to reprioritize Sections 4–6 based on business needs.
