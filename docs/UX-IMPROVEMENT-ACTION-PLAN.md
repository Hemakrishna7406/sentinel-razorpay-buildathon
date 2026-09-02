# Sentinel RC1 - UX Improvement Action Plan

**Date**: 2026-08-29  
**Owner**: Principal Product Designer  
**Timeline**: 4 weeks  
**Priority**: High (Production Readiness)

---

## Executive Summary

This document outlines **prioritized, actionable tasks** to address UX gaps identified in the audit. Tasks are grouped into 4 weekly sprints, each building on the previous week's foundation.

**Goal**: Transform Sentinel from "good foundation" (B+) to "production-grade" (A) UX quality.

---

## Week 1: Critical Fixes (Production Blockers)

**Focus**: Fix issues preventing production deployment.

**Goal**: Mobile responsive, accessible, no placeholders.

---

### Task 1.1: Mobile Navigation System
**Priority**: P0 (Critical)  
**Effort**: 8 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Hamburger menu button visible on mobile (< 768px)
- ✅ Slide-out drawer with full navigation
- ✅ Drawer closes on navigation or backdrop click
- ✅ Drawer closes on Esc key
- ✅ Focus trap within drawer
- ✅ Smooth animation (slide-in from left)

**Files to Modify**:
- `frontend/src/components/navigation/MobileMenu.tsx` (create)
- `frontend/src/components/navigation/Drawer.tsx` (create)
- `frontend/src/layouts/AppShell.tsx` (add mobile menu)

**Implementation**:
```tsx
// MobileMenu.tsx
export function MobileMenu() {
  const [open, setOpen] = useState(false);
  
  return (
    <>
      <button
        className="md:hidden p-2"
        onClick={() => setOpen(true)}
        aria-label="Open menu"
      >
        <Menu className="w-6 h-6" />
      </button>
      
      <Drawer open={open} onClose={() => setOpen(false)}>
        <Sidebar />
      </Drawer>
    </>
  );
}
```

---

### Task 1.2: Responsive KPI Grid
**Priority**: P0 (Critical)  
**Effort**: 2 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Mobile (< 640px): 2 columns
- ✅ Tablet (640-1024px): 3 columns
- ✅ Desktop (> 1024px): 5 columns
- ✅ Cards stack gracefully without breaking

**Files to Modify**:
- `frontend/src/pages/Dashboard/Overview.tsx`

**Implementation**:
```tsx
// Before
<motion.div {...stagger} className="grid grid-cols-5 gap-4">

// After
<motion.div {...stagger} className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
```

---

### Task 1.3: Responsive Table → Card View
**Priority**: P0 (Critical)  
**Effort**: 6 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Desktop: Table view
- ✅ Mobile: Card view (stacked)
- ✅ Both views show same data
- ✅ Both views clickable to details

**Files to Modify**:
- `frontend/src/pages/Dashboard/Overview.tsx` (Recent Decisions table)
- `frontend/src/pages/Dashboard/AuditLog.tsx` (Audit table)

**Implementation**:
```tsx
{/* Desktop: Table */}
<div className="hidden md:block overflow-x-auto">
  <table className="w-full">
    {/* ... existing table */}
  </table>
</div>

{/* Mobile: Cards */}
<div className="block md:hidden space-y-3">
  {decisions.map(decision => (
    <div key={decision.id} className="bg-surface border rounded-lg p-4">
      <div className="flex justify-between items-start mb-3">
        <span className="font-mono text-xs text-sentinel">{decision.id}</span>
        <DecisionBadge decision={decision.decision} />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs text-text-muted mb-1">Agent</div>
          <div className="font-medium">{decision.agent}</div>
        </div>
        {/* ... more fields */}
      </div>
    </div>
  ))}
</div>
```

---

### Task 1.4: Focus Indicators (Accessibility)
**Priority**: P0 (Critical)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ All buttons have visible focus ring
- ✅ All links have visible focus ring
- ✅ Focus ring uses brand color (sentinel blue)
- ✅ Focus ring visible on keyboard nav, not mouse click

**Files to Modify**:
- `frontend/src/index.css` (global styles)
- All components with interactive elements

**Implementation**:
```css
/* Add to index.css */
.focus-visible\:ring-sentinel:focus-visible {
  outline: 2px solid theme('colors.sentinel');
  outline-offset: 2px;
}

/* Update all buttons */
button {
  @apply focus-visible:ring-sentinel focus-visible:ring-2 focus-visible:ring-offset-2;
}
```

---

### Task 1.5: ARIA Labels on Icon Buttons
**Priority**: P0 (Critical)  
**Effort**: 2 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ All icon-only buttons have aria-label
- ✅ All icon-only links have aria-label
- ✅ Labels describe action (not "icon" or "button")

**Files to Modify**:
- `frontend/src/pages/Dashboard/Overview.tsx`
- `frontend/src/pages/App/LiveDecisions.tsx`
- All pages with icon buttons

**Find & Replace**:
```tsx
// Before
<button onClick={onRefresh}>
  <RefreshIcon />
</button>

// After
<button onClick={onRefresh} aria-label="Refresh decisions">
  <RefreshIcon />
</button>
```

---

### Task 1.6: Remove Placeholder Pages from Navigation
**Priority**: P0 (Critical)  
**Effort**: 1 hour  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Placeholder pages hidden from sidebar
- ✅ Routes still work (for future implementation)
- ✅ No broken links

**Files to Modify**:
- `frontend/src/components/navigation/Sidebar.tsx`

**Implementation**:
```tsx
// Remove these items from navigation array:
// - Intents (placeholder)
// - Agents (placeholder)
// - MCP Gateways (placeholder)
// - Observability (placeholder)
// - Alerts (placeholder)

// Keep routes in routes.tsx for future use, just hide from nav
```

---

### **Week 1 Deliverables**:
- ✅ Mobile-responsive navigation
- ✅ Responsive layouts (KPIs, tables)
- ✅ WCAG AA compliant focus indicators
- ✅ All icon buttons labeled
- ✅ No placeholder pages in navigation

**Testing**:
- [ ] Manual testing on iPhone SE (small mobile)
- [ ] Manual testing on iPad (tablet)
- [ ] Keyboard navigation test (Tab, Enter, Esc)
- [ ] Screen reader test (VoiceOver/NVDA)
- [ ] Lighthouse accessibility score > 90

---

## Week 2: User Feedback & Empty States

**Focus**: Improve user feedback, empty states, loading states.

---

### Task 2.1: Toast Notification System
**Priority**: P1 (High)  
**Effort**: 8 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Toast component with 4 variants (success, error, info, warning)
- ✅ Toast provider wraps app
- ✅ useToast hook for easy usage
- ✅ Auto-dismiss after 5s (configurable)
- ✅ Manual dismiss via X button
- ✅ Max 3 toasts stacked
- ✅ Slide-in animation from top-right

**Files to Create**:
- `frontend/src/components/ui/Toast.tsx`
- `frontend/src/components/ui/ToastProvider.tsx`
- `frontend/src/hooks/useToast.ts`

**Implementation**:
```tsx
// Usage
const { toast } = useToast();

toast({
  type: 'success',
  title: 'Policy saved',
  description: 'Changes will take effect immediately',
});
```

**Integrate in**:
- Settings page (save success/error)
- Policies page (save/delete success/error)
- Audit log (export success/error)
- Security center (verification success/error)

---

### Task 2.2: Empty State Component
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Reusable EmptyState component
- ✅ Supports icon, title, description, primary action, secondary action
- ✅ Responsive layout

**Files to Create**:
- `frontend/src/components/ui/EmptyState.tsx`

**Replace**:
- Live Decisions: "No decisions found matching filter"
- Audit Log: "No matching records found"
- Any placeholder pages (if accessed directly)

**Example**:
```tsx
<EmptyState
  icon={Activity}
  title="No decisions yet"
  description="Run your first demo scenario to see decisions appear here."
  action={{
    label: "Run Demo",
    onClick: () => navigate('/demo'),
  }}
  secondaryAction={{
    label: "Learn More",
    onClick: () => window.open('/docs'),
  }}
/>
```

---

### Task 2.3: Skeleton Loaders
**Priority**: P1 (High)  
**Effort**: 6 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Generic Skeleton component (text, circle, rect)
- ✅ Pre-built skeletons (KPICard, Table, Chart, DecisionCard)
- ✅ Shimmer animation
- ✅ Replace all loading spinners with skeletons

**Files to Create**:
- `frontend/src/components/ui/Skeleton.tsx`

**Replace**:
- Dashboard Overview: Show skeleton KPIs/charts during load
- Live Decisions: Show skeleton cards during load
- Security Center: Show skeleton metrics during load

**Implementation**:
```tsx
// Instead of
{isLoading && <Spinner />}

// Use
{isLoading ? (
  <>
    <SkeletonKPICard />
    <SkeletonKPICard />
    <SkeletonKPICard />
  </>
) : (
  kpis.map(kpi => <KPICard {...kpi} />)
)}
```

---

### Task 2.4: Confirmation Dialogs
**Priority**: P1 (High)  
**Effort**: 6 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Modal component
- ✅ ConfirmDialog component (specialized modal)
- ✅ Focus trap, Esc to close, backdrop click to close
- ✅ ARIA dialog role

**Files to Create**:
- `frontend/src/components/ui/Modal.tsx`
- `frontend/src/components/ui/ConfirmDialog.tsx`

**Use in**:
- Demo: "Reset" button (confirm before reset)
- Policies: "Delete" button (confirm before delete)
- Settings: "Reset to defaults" (confirm before reset)

**Example**:
```tsx
<ConfirmDialog
  open={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  title="Delete Policy"
  description="This policy will be permanently deleted. This action cannot be undone."
  confirmLabel="Delete Forever"
  variant="danger"
/>
```

---

### Task 2.5: Loading States Standardization
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ All pages use skeleton loaders (not spinners)
- ✅ Loading states at component level (not page level)
- ✅ Consistent loading experience across app

**Files to Modify**:
- All pages with loading states

**Before**:
```tsx
if (isLoading) return <Spinner />;
return <Dashboard data={data} />;
```

**After**:
```tsx
<Dashboard>
  {isLoading ? <SkeletonKPICard /> : <KPICard data={data} />}
  {isLoading ? <SkeletonChart /> : <Chart data={data} />}
</Dashboard>
```

---

### **Week 2 Deliverables**:
- ✅ Toast notification system integrated
- ✅ Empty states for all pages
- ✅ Skeleton loaders replacing spinners
- ✅ Confirmation dialogs for destructive actions
- ✅ Consistent loading experience

**Testing**:
- [ ] Toast notifications appear and dismiss correctly
- [ ] Empty states show when no data
- [ ] Skeleton loaders animate smoothly
- [ ] Confirmation dialogs prevent accidental deletions

---

## Week 3: Navigation & Search

**Focus**: Improve navigation, add search, breadcrumbs.

---

### Task 3.1: Breadcrumbs Component
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Breadcrumbs component with separator
- ✅ Auto-generated from route
- ✅ Clickable links to parent pages
- ✅ Current page non-clickable

**Files to Create**:
- `frontend/src/components/navigation/Breadcrumbs.tsx`

**Add to**:
- All dashboard pages (in AppShell layout)

**Example**:
```tsx
// Route: /dashboard/decisions
// Renders: Dashboard > Live Decisions
```

---

### Task 3.2: Search Input Component
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ SearchInput component with icon, clear button
- ✅ Debounced onChange (300ms)
- ✅ Loading spinner when searching

**Files to Create**:
- `frontend/src/components/ui/SearchInput.tsx`

**Use in**:
- Audit Log: Search by intent ID, agent, amount
- Live Decisions: Search by intent ID, agent
- (Future) Intent History: Search all fields

---

### Task 3.3: Implement Audit Log Search
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Search input functional
- ✅ Filters audit records by intent ID, agent, action, reason
- ✅ Case-insensitive search
- ✅ Shows "No results" empty state when no matches

**Files to Modify**:
- `frontend/src/pages/Dashboard/AuditLog.tsx`

**Implementation**:
```tsx
const [searchQuery, setSearchQuery] = useState('');

const filteredRecords = records.filter(record => {
  const query = searchQuery.toLowerCase();
  return (
    record.intent_id.toLowerCase().includes(query) ||
    record.agent_id.toLowerCase().includes(query) ||
    record.action_type.toLowerCase().includes(query) ||
    (record.reason_codes || []).some(r => r.toLowerCase().includes(query))
  );
});
```

---

### Task 3.4: Implement Live Decisions Search
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Search input functional
- ✅ Filters decisions by intent ID, agent, amount
- ✅ Works with filter (search + filter both applied)

**Files to Modify**:
- `frontend/src/pages/App/LiveDecisions.tsx`

---

### Task 3.5: Pagination Component
**Priority**: P1 (High)  
**Effort**: 6 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Pagination component with prev/next, page numbers
- ✅ Shows first, last, current, ±2 pages
- ✅ Ellipsis for skipped pages
- ✅ Page size selector (optional)

**Files to Create**:
- `frontend/src/components/ui/Pagination.tsx`

**Use in**:
- Audit Log: 50 rows per page
- Live Decisions: 30 cards per page

**Example**:
```
Showing 1-50 of 18,392

< 1 2 3 ... 368 >
```

---

### Task 3.6: Implement Audit Log Pagination
**Priority**: P1 (High)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Table shows 50 rows per page
- ✅ Pagination controls at bottom
- ✅ URL updates with page number (for deep linking)

**Files to Modify**:
- `frontend/src/pages/Dashboard/AuditLog.tsx`

---

### **Week 3 Deliverables**:
- ✅ Breadcrumbs on all dashboard pages
- ✅ Search functionality in Audit Log and Live Decisions
- ✅ Pagination in Audit Log
- ✅ Improved navigation experience

**Testing**:
- [ ] Breadcrumbs show correct path
- [ ] Search filters results correctly
- [ ] Pagination navigates correctly
- [ ] URL updates with page number

---

## Week 4: Polish & Onboarding

**Focus**: Final polish, onboarding flow, documentation.

---

### Task 4.1: Date Range Picker
**Priority**: P2 (Medium)  
**Effort**: 8 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ DatePicker component with calendar
- ✅ Range selection mode
- ✅ Preset quick selects (Last 24h, 7d, 30d, Quarter)
- ✅ Custom range selection

**Files to Create**:
- `frontend/src/components/ui/DatePicker.tsx`

**Use in**:
- Audit Log: Filter by date range
- Dashboard Overview: Time range selector (replace dropdown)

---

### Task 4.2: Implement Audit Log Date Filtering
**Priority**: P2 (Medium)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Date range picker above audit table
- ✅ Filters records by timestamp
- ✅ Preset ranges (Last 24h, 7d, 30d, This Quarter)

**Files to Modify**:
- `frontend/src/pages/Dashboard/AuditLog.tsx`

---

### Task 4.3: CSV Export (Audit Log)
**Priority**: P2 (Medium)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ "Export CSV" button functional
- ✅ Exports current filtered results (respects search, filter, date range)
- ✅ Includes all fields (timestamp, intent_id, agent_id, action, risk, decision, reason)
- ✅ Downloads as `sentinel-audit-{timestamp}.csv`

**Files to Modify**:
- `frontend/src/pages/Dashboard/AuditLog.tsx`

**Implementation**:
```tsx
function exportToCSV() {
  const csv = [
    ['Timestamp', 'Intent ID', 'Agent', 'Action', 'Risk', 'Decision', 'Reason'],
    ...filteredRecords.map(r => [
      r.timestamp,
      r.intent_id,
      r.agent_id,
      r.action_type,
      r.behavioral_risk,
      r.policy_decision,
      r.reason_codes?.join('; '),
    ]),
  ].map(row => row.join(',')).join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sentinel-audit-${Date.now()}.csv`;
  a.click();
}
```

---

### Task 4.4: Onboarding Tour (First-Time Users)
**Priority**: P2 (Medium)  
**Effort**: 12 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Detect first-time user (no prior activity)
- ✅ Show welcome modal
- ✅ 5-step tour (Dashboard, Live Decisions, Security Center, Run Demo, Complete)
- ✅ Spotlight highlights for each step
- ✅ Skip button at any time
- ✅ "Restart Tour" in help menu

**Files to Create**:
- `frontend/src/components/onboarding/OnboardingTour.tsx`
- `frontend/src/hooks/useOnboarding.ts`

**Libraries**:
- Use `react-joyride` or build custom

---

### Task 4.5: Help Modal with Keyboard Shortcuts
**Priority**: P2 (Medium)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Help button in top bar (question mark icon)
- ✅ Modal shows:
  - Getting Started checklist
  - Keyboard shortcuts
  - Link to documentation
  - Link to video tutorials
  - Contact support
- ✅ Keyboard shortcut to open: `?` key

**Files to Create**:
- `frontend/src/components/help/HelpModal.tsx`

---

### Task 4.6: Error Pages (404, 500, 403)
**Priority**: P2 (Medium)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ 404 page: Page not found (with "Go to Dashboard" button)
- ✅ 500 page: Server error (with "Retry" button)
- ✅ 403 page: Access denied (with "Contact Admin" button)

**Files to Create**:
- `frontend/src/pages/Error/404.tsx`
- `frontend/src/pages/Error/500.tsx`
- `frontend/src/pages/Error/403.tsx`

**Add to routes**:
```tsx
{
  path: '*',
  element: <NotFound />,
}
```

---

### Task 4.7: Top Bar Enhancement
**Priority**: P2 (Medium)  
**Effort**: 4 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Top bar added to AppShell
- ✅ Contains: Breadcrumbs, Search (Cmd+K button), Notifications (bell), User menu
- ✅ Responsive (collapses on mobile)

**Files to Create**:
- `frontend/src/components/navigation/TopBar.tsx`

**Add to**:
- `frontend/src/layouts/AppShell.tsx`

---

### **Week 4 Deliverables**:
- ✅ Date range filtering in Audit Log
- ✅ CSV export functional
- ✅ Onboarding tour for new users
- ✅ Help modal with shortcuts
- ✅ Error pages
- ✅ Top bar with breadcrumbs and user menu

**Testing**:
- [ ] Date picker selects correct ranges
- [ ] CSV export includes all filtered data
- [ ] Onboarding tour completes successfully
- [ ] Help modal accessible and informative
- [ ] Error pages render correctly

---

## Post-Implementation: Week 5 (Validation & Documentation)

### Task 5.1: Accessibility Audit
**Priority**: P1 (High)  
**Effort**: 8 hours  
**Owner**: QA Engineer + Frontend Developer

**Tools**:
- Lighthouse (Chrome DevTools)
- axe DevTools (browser extension)
- NVDA / VoiceOver (screen readers)

**Acceptance Criteria**:
- ✅ Lighthouse Accessibility score > 90
- ✅ axe DevTools: 0 violations
- ✅ All pages navigable via keyboard
- ✅ All interactive elements have focus indicators
- ✅ Screen reader announces all important content

---

### Task 5.2: User Testing
**Priority**: P1 (High)  
**Effort**: 16 hours  
**Owner**: Product Designer + User Researcher

**Method**:
- **Participants**: 3 Security Engineers, 2 DevOps Engineers, 1 Compliance Officer
- **Tasks**:
  1. Navigate to Security Center and verify audit chain
  2. Investigate a suspicious transaction in Live Decisions
  3. Export audit log for last quarter
  4. Add a new agent (when built)
  5. Complete onboarding tour
- **Metrics**:
  - Task success rate
  - Time on task
  - Error rate
  - Satisfaction (SUS score)

**Deliverables**:
- User testing report with findings
- Prioritized list of issues to fix

---

### Task 5.3: Update Design System Documentation
**Priority**: P2 (Medium)  
**Effort**: 8 hours  
**Owner**: Product Designer

**Files to Update**:
- `frontend/README-DESIGN-SYSTEM.md` (add new components)
- `docs/UX-GUIDELINES.md` (create if not exists)

**Content**:
- Document all new components (Toast, Modal, Pagination, etc.)
- Add usage examples
- Add do's and don'ts
- Add accessibility notes

---

### Task 5.4: Storybook Setup (Optional)
**Priority**: P3 (Nice to Have)  
**Effort**: 16 hours  
**Owner**: Frontend Developer

**Acceptance Criteria**:
- ✅ Storybook installed and configured
- ✅ Stories for all design system components
- ✅ Variants documented
- ✅ Accessible via `/storybook` route or separate port

**Benefits**:
- Component showcase for team
- Visual regression testing
- Easier design review

---

## Success Metrics

### Before UX Improvements (Baseline):
- Lighthouse Accessibility: 75
- Mobile usability: Fails
- Placeholder pages: 5 (40% of navigation)
- User can find any page: 50% success rate
- Task completion time: 5 minutes (avg)

### After UX Improvements (Target):
- Lighthouse Accessibility: > 90 ✅
- Mobile usability: Passes ✅
- Placeholder pages: 0 ✅
- User can find any page: 95% success rate ✅
- Task completion time: < 2 minutes ✅

---

## Risk Mitigation

### Risk 1: Timeline Slippage
**Mitigation**: 
- Prioritize P0 tasks first
- P2/P3 tasks can slide to Week 5 if needed
- Weekly check-ins to reassess priorities

### Risk 2: Scope Creep
**Mitigation**:
- Stick to defined acceptance criteria
- Nice-to-haves marked as P3 (defer if needed)
- No new features mid-sprint

### Risk 3: Technical Blockers
**Mitigation**:
- Identify dependencies early
- Parallel tracks where possible
- Fallback plans for complex features (e.g., Cmd+K can be deferred)

---

## Resource Requirements

### Frontend Developer
- **Allocation**: 100% (4 weeks)
- **Skills**: React, TypeScript, Tailwind, Accessibility

### Product Designer
- **Allocation**: 50% (4 weeks)
- **Skills**: UX design, prototyping, user research

### QA Engineer
- **Allocation**: 25% (Week 5 only)
- **Skills**: Accessibility testing, manual testing

---

## Communication Plan

### Daily:
- Standup (15 min): Progress, blockers, plan for day

### Weekly:
- Sprint review (30 min): Demo completed tasks
- Sprint planning (1 hour): Plan next week's tasks
- Design review (30 min): Review UX decisions

### Ad-hoc:
- Slack channel: `#ux-improvement-sprint`
- Quick questions, screenshots, feedback

---

## Appendix: Component Library Checklist

Components to build in order of priority:

**Week 1**:
- [x] Drawer (mobile nav)
- [x] Focus indicators (global CSS)

**Week 2**:
- [ ] Toast
- [ ] ToastProvider
- [ ] EmptyState
- [ ] Skeleton
- [ ] SkeletonKPICard
- [ ] SkeletonTable
- [ ] SkeletonChart
- [ ] Modal
- [ ] ConfirmDialog

**Week 3**:
- [ ] Breadcrumbs
- [ ] SearchInput
- [ ] Pagination

**Week 4**:
- [ ] DatePicker
- [ ] OnboardingTour
- [ ] HelpModal
- [ ] TopBar
- [ ] UserMenu
- [ ] NotificationBadge

**Future**:
- [ ] CommandPalette (Cmd+K)
- [ ] ProgressBar
- [ ] Tabs
- [ ] Accordion
- [ ] Combobox
- [ ] MultiSelect

---

**Document Owner**: Principal Product Designer  
**Last Updated**: 2026-08-29  
**Status**: Ready for Implementation  
**Start Date**: 2026-09-01 (Monday)  
**Target Completion**: 2026-09-28 (Friday)
