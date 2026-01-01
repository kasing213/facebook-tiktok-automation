# UI Layout Specification (Layout Only)

## Scope
This document defines UI layout and navigation only.
No business logic, permissions, OAuth, or backend behavior.

## Pages

### 1. Homepage (Public)
Purpose:
- Let users choose which service they want to use

Layout:
- Top header: Logo | Docs | Login | Sign Up
- Hero section
- Service cards (Facebook Automation, TikTok Automation, Invoice Generator, etc.)
- CTA buttons

No dashboard metrics.
No user-specific data.

---

### 2. Platform Dashboard (Authenticated)
Purpose:
- Observe usage, status, and activity of selected services

Layout reference:
- Similar to OpenAI dashboard (Usage page)

Global layout:
- Top header: Workspace selector | User menu
- Left sidebar:
  - Overview
  - Usage
  - Logs
  - Integrations
  - Settings

Main content area:
- Charts (usage / activity)
- Tables (requests, events)
- Summary cards

All data can be mocked or empty.

3️⃣ One explicit instruction to Claude

When you ask Claude, your prompt should be this simple:

“Read the screenshots and UI_LAYOUT_SPEC.md.
Ignore backend, auth, permissions, and logic.
Help me design the UI layout so the dashboard visually resembles the OpenAI dashboard, and the homepage is a service-selection landing page.”

That’s it.

Do not mention:

Invoice logic

CLI pipelines

OAuth

Tokens

Claude will otherwise drift.

Why this works (important insight)

Claude is very good at:

Visual hierarchy

Layout systems

Navigation consistency

Claude is bad when:

Scope is unclear

Architecture and UI are mixed

Logic leaks into layout decisions

You are fixing that by locking the layout phase.

Final grounding sentence (remember this)

Right now you are not building a system — you are building a container for a system.