# Sentinel — frontend.md

React dashboard implementing masterplan §23. Vite + React + TypeScript + Tailwind. Design tokens and motion spec live in `frontend-design.md` — this file is structure and data-flow only.

---

## 1. Screens (masterplan §23, minimum set)

```
src/
├── pages/
│   ├── AgentOverview.tsx      # list of agents, risk state, quick baseline vs current
│   ├── IntentStream.tsx        # live feed: timestamp, agent, action, amount, risk, decision
│   ├── BehavioralDrift.tsx      # baseline vs current window, deviation bars, drift score
│   ├── DecisionDetail.tsx        # risk score, top features (SHAP), policy rule fired, capability status
│   ├── Audit.tsx                   # intent → decision → token → execution → verification, filterable
│   └── Simulate.tsx                 # P1: policy input, historical impact preview
├── components/
│   ├── RiskBadge.tsx           # SAFE/SUSPICIOUS/HIGH-RISK, consistent color mapping everywhere
│   ├── DriftMeter.tsx           # the signature visualization — see frontend-design.md
│   ├── IntentRow.tsx
│   ├── AgentCard.tsx
│   ├── FeatureBar.tsx            # SHAP contribution bars
│   └── CapabilityStatus.tsx       # token issued / expired / verified / denied
├── hooks/
│   ├── useIntentStream.ts       # polling or SSE against GET /audit (or a dedicated /stream endpoint)
│   └── useAgentProfile.ts
├── lib/
│   └── api.ts                     # typed client for the FastAPI surface in backend.md
└── App.tsx
```

## 2. Live intent stream — polling is fine for MVP

Don't build WebSockets/SSE infrastructure for the Sept 5 deadline unless the demo genuinely needs sub-second updates (it doesn't — a 1–2s poll interval is invisible to a judge watching a dashboard). `useIntentStream` polls `GET /audit?since=<last_seq>` every 1.5s and appends new rows — simple, demoable, zero infra risk.

```ts
function useIntentStream() {
  const [rows, setRows] = useState<AuditEvent[]>([]);
  useEffect(() => {
    const id = setInterval(async () => {
      const latest = await api.getAudit({ since: rows.at(-1)?.seq ?? 0 });
      if (latest.length) setRows(r => [...r, ...latest]);
    }, 1500);
    return () => clearInterval(id);
  }, [rows]);
  return rows;
}
```

## 3. Decision detail — what makes the model legible

```tsx
<DecisionDetail>
  <RiskBadge level={decision.risk_level} score={decision.risk_score} />
  <FeatureBar features={decision.top_features} />   {/* SHAP, P1 — omit gracefully if absent in MVP */}
  <PolicyRule version={decision.policy_version} rule={policyRule} />
  <CapabilityStatus token={capability} />
</DecisionDetail>
```
If SHAP (P1) isn't built yet, `FeatureBar` should render the raw feature values it does have (velocity_ratio, amount_deviation, etc.) rather than a placeholder — the dashboard should never show empty states where real data exists.

## 4. Simulate screen (P1) — the "what-if" flow

```tsx
<Simulate>
  <PolicyInput onSubmit={runSimulation} />   {/* NL text (P1) or structured rule editor (P0-safe fallback) */}
  <ImpactSummary
    actionsAffectedPct={result.actions_affected_pct}
    exposureGoverned={result.exposure_governed}
    additionalReviews={result.additional_manual_reviews}
  />
  <ComparisonView policies={[policyA, policyB]} />  {/* side-by-side trade-off, masterplan §18 */}
</Simulate>
```
Build the structured rule editor first (dropdowns/number inputs → the same `rule_json` shape the compiler would produce) — this makes `POST /simulate` fully functional and demoable even if the NL compiler (P1) isn't finished in time.

## 5. Agent Overview — baseline vs. current, at a glance

This is the screen judges will look at longest. Each `AgentCard` shows the profile-vs-current comparison directly, not just a status pill:

```tsx
<AgentCard agent={agent}>
  <BaselineRow label="Refunds/day" baseline={18} current={currentRate} />
  <BaselineRow label="Avg amount" baseline="₹3,240" current={currentAvg} />
  <DriftMeter score={agent.drift_score} />
  <RiskBadge level={agent.current_risk} />
</AgentCard>
```

## 6. State management

Keep it to React Query (or SWR) + local component state. No Redux/Zustand needed — the data model here is server-driven reads plus one write path (Simulate), not complex client-side state.

## 7. Accessibility / quality floor (non-negotiable per frontend-design skill)

- Responsive down to a laptop-in-a-demo-room width at minimum (a panel interview is not mobile, but don't hardcode fixed pixel widths).
- Visible keyboard focus states on every interactive element — a judge or interviewer may tab through it.
- Respect `prefers-reduced-motion` for the DriftMeter and any scroll-triggered elements on the pitch page (see frontend-design.md).
