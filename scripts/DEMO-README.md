# Sentinel Interactive Demo System

This directory contains the orchestration scripts and scenario definitions for the Sentinel interactive demo.

## Overview

The demo system showcases 5 key security scenarios demonstrating Sentinel's zero-trust authorization capabilities:

1. **Normal Agent** 🟢 - Routine transaction within behavioral baseline (ALLOW)
2. **Suspicious Agent** 🟡 - High-value transaction requiring human review (ESCALATE)
3. **Malicious Agent** 🔴 - Behavioral drift indicating compromise (CONTAIN)
4. **Replay Attack** 🔁 - Duplicate transaction blocked by idempotency
5. **Redis Failure** 💥 - Infrastructure failure triggers fail-closed behavior

## Architecture

```
┌─────────────────────┐
│  Frontend UI        │
│  /demo              │  ← ScenarioRunner.tsx
└──────┬──────────────┘
       │ POST /demo/scenarios/{id}
       │ SSE /execution/stream
┌──────▼──────────────┐
│  Backend API        │
│  api/main.py        │  ← Demo endpoints + SSE broadcaster
└──────┬──────────────┘
       │ Events
┌──────▼──────────────┐
│  Decision Timeline  │  ← DecisionTimeline.tsx (GSAP animations)
└─────────────────────┘
```

## Files

### Backend
- `api/main.py` - Demo endpoints (`POST /demo/scenarios/{scenario}`, `GET /execution/stream`)
- `scripts/scenarios.json` - Scenario definitions with expected outcomes

### Frontend
- `frontend/src/pages/Demo/ScenarioRunner.tsx` - Main demo UI
- `frontend/src/components/DecisionTimeline.tsx` - Animated timeline component

### Orchestration Scripts
- `scripts/demo_orchestrator.py` - Python CLI for running all 5 scenarios (Rich UI)
- `scripts/demo.py` - Legacy demo script (basic output)

## Scenario API Endpoints

### Available Scenarios
- `normal` - Normal agent (ALLOW)
- `suspicious` - Suspicious agent (ESCALATE)
- `malicious` - Malicious agent (CONTAIN)
- `abuse-burst` - Abuse burst (legacy, maps to malicious)
- `privilege-violation` - Privilege violation (legacy)
- `replay` - Replay attack (idempotency)
- `redis_failure` - Infrastructure failure

### Trigger Scenario
```bash
POST http://localhost:8000/demo/scenarios/{scenario_id}
```

Returns:
```json
{
  "status": "started",
  "scenario": "normal"
}
```

### Stream Events
```bash
GET http://localhost:8000/execution/stream
```

Returns SSE stream with `SentinelExecutionEvent` payloads:
```typescript
{
  event_id: string,
  timestamp: string,
  intent_id: string,
  agent_id: string,
  stage: "INTENT" | "BEHAVIOR" | "POLICY" | "CAPABILITY" | "MCP" | "RAZORPAY",
  behavioral_risk?: number,
  semantic_risk?: number,
  policy_decision?: string,
  capability_issued?: boolean,
  execution_status?: string,
  reason_codes?: string[]
}
```

## Running the Demo

### Option 1: Frontend UI (Recommended for judges)
```bash
# Visit the demo page
open http://localhost:3000/demo

# Or from dashboard
# Navigate to: Dashboard → Demo
```

### Option 2: Python CLI
```bash
# Run all 5 scenarios
python scripts/demo_orchestrator.py

# Output includes:
# - Colored console output (Rich)
# - Real-time progress indicators
# - Summary table with all results
```

### Option 3: Manual API Calls
```bash
# Trigger a scenario
curl -X POST http://localhost:8000/demo/scenarios/normal

# Listen to events
curl -N http://localhost:8000/execution/stream
```

## Test Integration

### Test IDs (for E2E tests)
- `data-testid="scenario-card"` - Scenario selection buttons
- `data-scenario="{id}"` - Scenario ID attribute
- `data-testid="run-scenario-button"` - Run button
- `data-testid="reset-demo-button"` - Reset button
- `data-testid="decision-timeline"` - Timeline container

### Example E2E Test
```typescript
// Select scenario
await page.click('[data-scenario="normal"]');

// Run scenario
await page.click('[data-testid="run-scenario-button"]');

// Wait for completion
await page.waitForSelector('[data-testid="decision-timeline"] .final-decision');

// Verify decision
const decision = await page.textContent('.final-decision');
expect(decision).toContain('ALLOW');
```

## Expected Outcomes

| Scenario | Decision | Behavioral Risk | Capability Token | Execution |
|----------|----------|----------------|------------------|-----------|
| Normal | ALLOW | ~0.05-0.08 | ✓ ISSUED | SUCCESS |
| Suspicious | ESCALATE | ~0.68-0.71 | ✗ NONE | ESCALATED |
| Malicious | CONTAIN | ~0.89-0.94 | ✗ NONE | CONTAINED |
| Replay (1st) | ALLOW | ~0.05-0.08 | ✓ ISSUED | SUCCESS |
| Replay (2nd) | ALLOW | N/A | ✗ NONE | BLOCKED_REPLAY |
| Redis Failure | ESCALATE | N/A | ✗ NONE | ESCALATED_INFRA_FAILURE |

## Performance Targets

- Total scenario execution: <5 seconds
- SSE event latency: <100ms
- Timeline animation: 60fps
- Demo reset: <500ms

## Troubleshooting

### API Not Responding
```bash
# Check API health
curl http://localhost:8000/health/live

# Check readiness
curl http://localhost:8000/health/ready
```

### SSE Connection Issues
- Ensure CORS is configured correctly
- Check browser console for connection errors
- Verify Redis is running (required for SSE)

### Scenario Not Triggering
- Check backend logs: `docker-compose logs api`
- Verify scenario name matches: `normal`, `suspicious`, `malicious`, `replay`, `redis_failure`
- Test with curl first before UI

### Timeline Not Animating
- Check GSAP is installed: `npm list gsap`
- Verify events are arriving: Browser DevTools → Network → EventStream
- Check console for React errors

## Demo Walkthrough (for Judges)

### 3-Minute Demo Script

**[30 seconds] Introduction**
"Sentinel is a zero-trust authorization control plane for autonomous financial agents. Let me show you 5 scenarios demonstrating our security guarantees."

**[30 seconds] Scenario 1: Normal Agent**
- Click "Normal Agent" → Run
- Point out: "Behavioral risk is low (0.05), all checks pass, capability token issued, execution succeeds."

**[30 seconds] Scenario 2: Suspicious Agent**
- Click "Suspicious Agent" → Run
- Point out: "High-value transaction (₹85k) exceeds baseline by 3σ. No token issued. Escalated for human review."

**[30 seconds] Scenario 3: Malicious Agent**
- Click "Malicious Agent" → Run
- Point out: "Severe behavioral anomaly (0.94 risk). Agent contained. No execution allowed."

**[30 seconds] Scenario 4: Replay Attack**
- Click "Replay Attack" → Run
- Point out: "First request succeeds. Second request with same idempotency key is blocked. No duplicate payments."

**[30 seconds] Scenario 5: Redis Failure**
- Click "Redis Failure" → Run
- Point out: "Infrastructure failure detected. System fails closed. No fail-open scenarios."

**[30 seconds] Summary**
"Sentinel provides: behavioral ML, policy engine, capability tokens, idempotency protection, and fail-closed guarantees. All in <20ms P95 latency."

## Success Criteria

✅ All 5 scenarios execute deterministically  
✅ Judge can run full demo in <3 minutes  
✅ Visual feedback is immediate and compelling  
✅ Each scenario tells a clear security story  
✅ Zero setup required (one-click execution)  
✅ Timeline animations are smooth (60fps)  

## Next Steps

- [ ] Add telemetry tracking for demo runs
- [ ] Create screencast video for async reviews
- [ ] Add "Download Results" button (JSON export)
- [ ] Implement comparison mode (side-by-side scenarios)
