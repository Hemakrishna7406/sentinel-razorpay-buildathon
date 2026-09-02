# Sentinel RC1 - Information Architecture Redesign

**Date**: 2026-08-29  
**Designer**: Principal Product Designer  
**Status**: Proposed Redesign

---

## Executive Summary

The current navigation structure has several issues:
- **Placeholder pages** breaking user flow
- **Unclear grouping** (Authorization vs. Operations)
- **Missing key pages** (Agent Management, Intent History)
- **Inconsistent naming** (Audit Ledger vs. Audit Log)

This document proposes a **refined IA** based on user personas and journey mapping.

---

## Current Structure (RC1)

```
Dashboard
├── Overview
├── [Authorization]
│   ├── Live Decisions
│   ├── Intents (placeholder)
│   ├── Agents (placeholder)
│   ├── Policies
│   └── MCP Gateways (placeholder)
└── [Operations]
    ├── Security Center
    ├── Audit Ledger
    ├── Observability (placeholder)
    ├── Alerts (placeholder)
    └── Settings
```

**Issues**:
- ❌ 5 placeholder pages (40% of navigation)
- ❌ "Intents" and "Live Decisions" overlap
- ❌ No quick access to Demo
- ⚠️ "MCP Gateways" too technical for non-devs
- ⚠️ "Observability" and "Alerts" too vague

---

## Proposed Structure (Enhanced)

### Option A: Flat Navigation (Recommended)

**Rationale**: Fewer clicks, clearer labels, no placeholders.

```
┌─────────────────────────────┐
│ SENTINEL                    │
├─────────────────────────────┤
│ Overview                    │ ← Dashboard home
│                             │
│ Live Decisions              │ ← Real-time feed
│ Intent History              │ ← Searchable archive
│ Policies                    │ ← Authorization rules
│ Agents                      │ ← Agent management
│                             │
│ Security Center             │ ← Security invariants
│ Audit Ledger                │ ← Compliance & audit
│                             │
│ System Health               │ ← Infrastructure status
│                             │
│ Settings                    │ ← Configuration
└─────────────────────────────┘
```

**Pros**:
- ✅ Clear, action-oriented labels
- ✅ No placeholders (only built pages)
- ✅ Flat hierarchy (max 2 clicks to any page)
- ✅ Easy to scan

**Cons**:
- ⚠️ Longer sidebar (9 items)
- ⚠️ No visual grouping

---

### Option B: Grouped Navigation (Alternative)

**Rationale**: Visual grouping by concern, similar to current structure.

```
┌─────────────────────────────┐
│ SENTINEL                    │
├─────────────────────────────┤
│ Overview                    │
│                             │
│ AUTHORIZATION               │
│   Live Decisions            │
│   Intent History            │
│   Policies                  │
│   Agents                    │
│                             │
│ SECURITY                    │
│   Security Center           │
│   Audit Ledger              │
│                             │
│ OPERATIONS                  │
│   System Health             │
│   Settings                  │
└─────────────────────────────┘
```

**Pros**:
- ✅ Clear grouping by concern
- ✅ Familiar structure (similar to current)
- ✅ Scalable (can add items to groups)

**Cons**:
- ⚠️ Slightly longer sidebar
- ⚠️ More visual weight

---

### Option C: Persona-Based Navigation (Future Consideration)

**Rationale**: Optimize for primary user journeys.

```
┌─────────────────────────────┐
│ SENTINEL                    │
├─────────────────────────────┤
│ Overview                    │
│                             │
│ FOR SECURITY ENGINEERS      │
│   Threat Detection          │
│   Incident Investigation    │
│   Security Invariants       │
│                             │
│ FOR DEVOPS ENGINEERS        │
│   System Health             │
│   Performance Metrics       │
│   Logs & Traces             │
│                             │
│ FOR COMPLIANCE OFFICERS     │
│   Audit Trail               │
│   Compliance Reports        │
│   Evidence Export           │
│                             │
│ CONFIGURATION               │
│   Policies                  │
│   Agents                    │
│   Settings                  │
└─────────────────────────────┘
```

**Pros**:
- ✅ Optimized for user goals
- ✅ Reduces cognitive load
- ✅ Clear user journeys

**Cons**:
- ❌ Longer sidebar
- ❌ Redundant pages (same page in multiple groups)
- ❌ Harder to maintain
- ⚠️ Assumes users know their persona

**Recommendation**: Keep for future consideration, not v1.

---

## Recommended: Option A (Flat Navigation)

### Page-by-Page Definition

#### 1. Overview
**Route**: `/dashboard`  
**Label**: "Overview"  
**Icon**: LayoutDashboard  
**Description**: Executive dashboard with KPIs, charts, recent decisions, system health.

**Audience**: All users  
**Frequency**: Multiple times daily

**Content**:
- KPI row (Total Intents, ALLOW, ESCALATE, CONTAIN, Unauthorized)
- Decision trend chart (last 24h)
- Risk distribution chart
- Recent decisions table (last 10)
- System health grid
- Quick actions (Run Demo, View Security, Export Data)

---

#### 2. Live Decisions
**Route**: `/dashboard/decisions`  
**Label**: "Live Decisions"  
**Icon**: Activity  
**Description**: Real-time authorization decision feed with auto-refresh.

**Audience**: Security Engineers, DevOps Engineers  
**Frequency**: Multiple times daily

**Content**:
- Auto-refresh toggle (Pause/Resume)
- Stats bar (Total, ALLOW, ESCALATE, CONTAIN counts)
- Filter bar (ALL, ALLOW, ESCALATE, CONTAIN)
- Decision cards (grid, 3 columns)
- Pagination (30 per page)
- Search (intent ID, agent, amount)

**New Features** (to be added):
- Click card to see intent details
- Export visible results to CSV
- Real-time notification on CONTAIN decision

---

#### 3. Intent History
**Route**: `/dashboard/intents`  
**Label**: "Intent History"  
**Icon**: FileText  
**Description**: Searchable archive of all authorization requests.

**Audience**: Security Engineers, Compliance Officers  
**Frequency**: Daily

**Content**:
- Search bar (intent ID, agent, amount, recipient)
- Date range picker (presets + custom)
- Filter sidebar (decision, risk level, agent)
- Results table (paginated, 50 per page)
- Table columns:
  - Timestamp
  - Intent ID
  - Agent
  - Action
  - Amount
  - Risk Score
  - Decision
  - Latency
- Click row to see intent details

**Status**: Currently placeholder, needs implementation.

---

#### 4. Policies
**Route**: `/dashboard/policies`  
**Label**: "Policies"  
**Icon**: Shield  
**Description**: Authorization rules and containment policies.

**Audience**: Security Engineers, DevOps Engineers  
**Frequency**: Weekly

**Content**: (Already built, keep as-is)

---

#### 5. Agents
**Route**: `/dashboard/agents`  
**Label**: "Agents"  
**Icon**: Bot  
**Description**: Connected AI agent registry and management.

**Audience**: DevOps Engineers, Security Engineers  
**Frequency**: Weekly

**Content**:
- Agent cards (grid, 3 columns)
- Agent details:
  - Name, ID, Status (Active/Inactive)
  - Created date, Last seen
  - Total requests (24h), ALLOW/ESCALATE/CONTAIN breakdown
  - Risk profile (baseline status)
  - Quick actions (View Activity, Contain Agent, Edit)
- "Add Agent" button (wizard)
- Search and filter

**Status**: Currently placeholder, needs implementation.

---

#### 6. Security Center
**Route**: `/dashboard/security`  
**Label**: "Security Center"  
**Icon**: ShieldCheck  
**Description**: Security invariants, audit chain verification, release gate.

**Audience**: Security Engineers, Compliance Officers  
**Frequency**: Daily

**Content**: (Already built, keep as-is)

---

#### 7. Audit Ledger
**Route**: `/dashboard/audit`  
**Label**: "Audit Ledger"  
**Icon**: BookOpen  
**Description**: Complete audit trail for compliance and investigation.

**Audience**: Compliance Officers, Security Engineers  
**Frequency**: Weekly (or during audits)

**Content**: (Already built, enhance as per audit report)

**Improvements Needed**:
- Implement search
- Implement CSV export
- Add pagination
- Add date range picker
- Add responsive card view (mobile)

---

#### 8. System Health
**Route**: `/dashboard/system-health`  
**Label**: "System Health"  
**Icon**: Activity  
**Description**: Infrastructure health, performance metrics, logs.

**Audience**: DevOps Engineers  
**Frequency**: Multiple times daily

**Content**:
- Service health grid (API, Kafka, Redis, PostgreSQL, ML Model, MCP Gateway)
- Each service shows:
  - Status (Healthy, Degraded, Down)
  - Latency (p50, p95, p99)
  - Uptime %
  - Last incident
- Performance charts:
  - Request throughput (requests/second)
  - Latency over time (p50, p95, p99)
  - Error rate (%)
- Quick actions:
  - View Logs
  - View Traces (if OpenTelemetry integrated)
  - Restart Worker (if supported)

**Status**: Partially exists in Overview, needs dedicated page.

---

#### 9. Settings
**Route**: `/dashboard/settings`  
**Label**: "Settings"  
**Icon**: Settings  
**Description**: System configuration, user preferences, integrations.

**Audience**: All users  
**Frequency**: Rarely

**Content**: (Already built, keep as-is)

---

## Top Bar Enhancements

**Current**: Empty (no top bar).

**Proposed**:
```
┌──────────────────────────────────────────────────────────────┐
│ 🏠 Sentinel > Dashboard > Live Decisions      🔍 ⌘K  🔔  👤  │
└──────────────────────────────────────────────────────────────┘
```

**Elements**:
1. **Breadcrumbs**: Current page path (Home > Dashboard > Live Decisions)
2. **Search / Command Palette**: Click to open Cmd+K palette
3. **Notifications**: Bell icon with badge (count of unread alerts)
4. **User Menu**: Avatar with dropdown (Profile, Settings, Logout)

---

## Mobile Navigation

**Current**: Sidebar always visible (breaks on mobile).

**Proposed**:

### Mobile (< 768px):
```
┌──────────────────────────────────────┐
│ ☰  Sentinel        🔍 ⌘K  🔔  👤    │ ← Top bar
├──────────────────────────────────────┤
│                                      │
│ Content                              │
│                                      │
└──────────────────────────────────────┘
```

**Hamburger Menu** (☰) opens slide-out drawer with full navigation.

### Tablet (768px - 1024px):
- Sidebar visible
- Collapsed (icons only, expand on hover)
- Full sidebar on click

### Desktop (> 1024px):
- Full sidebar always visible
- Fixed width (240px)

---

## Quick Actions (Dashboard Shortcuts)

**Location**: Dashboard Overview, below KPIs

**Buttons**:
1. **Run Demo** → Navigate to `/demo`
2. **View Security** → Navigate to `/dashboard/security`
3. **Export Audit Log** → Download CSV
4. **Verify Audit Chain** → Run verification, show toast
5. **Add Agent** → Open agent wizard

---

## Search & Command Palette (Cmd+K)

**Trigger**: Cmd+K (Mac) or Ctrl+K (Windows/Linux)

**Functionality**:
- **Global search** across all pages
- **Quick navigation** to any page
- **Quick actions** (Run Demo, Export Data, etc.)
- **Fuzzy search** (typo-tolerant)
- **Recent pages** (last 5 visited)
- **Keyboard navigation** (Arrow keys, Enter to select)

**Example**:
```
┌──────────────────────────────────────┐
│ Search pages and actions...          │
├──────────────────────────────────────┤
│ PAGES                                │
│   Dashboard Overview                 │
│   Live Decisions                     │
│   Security Center                    │
│                                      │
│ ACTIONS                              │
│   Run Demo Scenario                  │
│   Export Audit Log                   │
│   Verify Audit Chain                 │
│                                      │
│ AGENTS                               │
│   payments-agent                     │
│   payouts-agent                      │
└──────────────────────────────────────┘
```

---

## Help & Documentation

**Current**: No in-app help.

**Proposed**:

### Help Button (Top Bar)
- Question mark icon
- Opens help modal

### Help Modal Content:
1. **Getting Started** (onboarding checklist)
2. **Keyboard Shortcuts** (Cmd+K, Esc, Tab, Enter, etc.)
3. **Documentation** (link to external docs)
4. **Video Tutorials** (embedded or linked)
5. **Contact Support** (email, Slack, etc.)

### Keyboard Shortcuts:
```
NAVIGATION
  Cmd+K        Open command palette
  G then D     Go to Dashboard
  G then S     Go to Security Center
  
ACTIONS
  Cmd+R        Refresh current page
  Cmd+E        Export data (where applicable)
  Esc          Close modal/drawer
  
TABLE NAVIGATION
  Tab          Next row/column
  Shift+Tab    Previous row/column
  Enter        Open details
```

---

## Onboarding Flow (First-Time Users)

**Trigger**: User logs in for the first time (no prior activity).

**Steps**:

### Step 1: Welcome
```
┌────────────────────────────────────┐
│ Welcome to Sentinel!               │
│                                    │
│ Let's get you started with a      │
│ quick tour.                        │
│                                    │
│ [Skip]  [Start Tour]               │
└────────────────────────────────────┘
```

### Step 2: Dashboard Tour
- Spotlight highlight KPI cards
- Tooltip: "These show real-time authorization metrics"
- [Next]

### Step 3: Live Decisions
- Navigate to Live Decisions
- Tooltip: "See every authorization decision as it happens"
- [Next]

### Step 4: Security Center
- Navigate to Security Center
- Tooltip: "Verify Sentinel's security guarantees"
- [Next]

### Step 5: Run Demo
```
┌────────────────────────────────────┐
│ Try it yourself!                   │
│                                    │
│ Run a demo scenario to see         │
│ Sentinel in action.                │
│                                    │
│ [Skip]  [Run Demo]                 │
└────────────────────────────────────┘
```
- Navigate to `/demo`
- Auto-select "Normal Agent" scenario
- User clicks "Run Scenario"

### Step 6: Complete
```
┌────────────────────────────────────┐
│ You're all set!                    │
│                                    │
│ Explore the dashboard or check     │
│ out our documentation.             │
│                                    │
│ [View Docs]  [Close]               │
└────────────────────────────────────┘
```

**Progress**: Show steps (e.g., "Step 3 of 6")

**Skip**: Allow users to skip tour at any point

**Revisit**: Add "Restart Tour" in help menu

---

## Error Pages

### 404: Page Not Found
```
┌────────────────────────────────────┐
│          404                       │
│     Page Not Found                 │
│                                    │
│ The page you're looking for       │
│ doesn't exist.                     │
│                                    │
│ [Go to Dashboard]                  │
└────────────────────────────────────┘
```

### 500: Server Error
```
┌────────────────────────────────────┐
│          500                       │
│     Server Error                   │
│                                    │
│ Something went wrong on our end.   │
│ We're working to fix it.           │
│                                    │
│ [Retry]  [Go to Dashboard]         │
└────────────────────────────────────┘
```

### 403: Forbidden
```
┌────────────────────────────────────┐
│          403                       │
│     Access Denied                  │
│                                    │
│ You don't have permission to       │
│ view this page.                    │
│                                    │
│ [Contact Admin]  [Go to Dashboard] │
└────────────────────────────────────┘
```

---

## Sitemap (Complete)

```
Landing
  /                       Landing page (POC)
  /hero                   Hero architecture page
  /demo                   Interactive demo

Dashboard (App Shell)
  /dashboard              Overview
  /dashboard/decisions    Live Decisions
  /dashboard/intents      Intent History
  /dashboard/policies     Policies
  /dashboard/agents       Agents
  /dashboard/security     Security Center
  /dashboard/audit        Audit Ledger
  /dashboard/system-health System Health
  /dashboard/settings     Settings
  
  Intent Details (Modal or Page)
  /dashboard/intents/:id  Intent details

Error Pages
  /404                    Page not found
  /500                    Server error
  /403                    Access denied
```

---

## Implementation Plan

### Phase 1: Remove Placeholders (Week 1)
- Remove placeholder pages from navigation
- Update routes.tsx to hide unbuilt pages
- Update Sidebar.tsx with new structure

### Phase 2: Build Missing Pages (Week 2-3)
- Intent History page
- Agents page
- System Health page (enhance)

### Phase 3: Navigation Enhancements (Week 4)
- Mobile hamburger menu + drawer
- Breadcrumbs component
- Command palette (Cmd+K)
- Top bar with user menu

### Phase 4: Onboarding & Help (Week 5)
- First-time user onboarding tour
- Help modal with shortcuts
- Error pages (404, 500, 403)

---

## Success Metrics

**Usability**:
- ✅ Users can find any page in < 5 seconds
- ✅ Zero clicks on placeholder pages
- ✅ 90% of users complete onboarding tour

**Navigation**:
- ✅ Average navigation depth: 1.5 clicks (from dashboard to any page)
- ✅ Command palette usage: 30% of users
- ✅ Mobile menu adoption: 100% mobile users

**Discoverability**:
- ✅ Users discover all pages within first session
- ✅ Help documentation accessed by 50% of users
- ✅ Keyboard shortcuts used by 20% of power users

---

**Document Owner**: Principal Product Designer  
**Last Updated**: 2026-08-29  
**Status**: Approved for Implementation
