# Sentinel Frontend Reconstruction Plan
## From Generic Cards to Cinematic Security Narrative

**Status**: Reconstruction Plan v1.0  
**Date**: August 29, 2026  
**Visual Direction**: See `frontend-visual-direction.md`

---

## Executive Summary

**Current State**: Clean but generic AI-generated SaaS landing page  
**Target State**: Scroll-driven security narrative that makes users EXPERIENCE Sentinel's decision process  
**Approach**: Scene-by-scene reconstruction with visual QA between each phase

---

## Current Implementation Audit

### What Exists (Preserve)
✅ **Infrastructure**
- React 19 + TypeScript 6
- Vite build system
- Tailwind CSS
- GSAP + ScrollTrigger
- React Router 7
- React Query
- Service layer architecture

✅ **Components to Keep**
- `animations/premiumEffects.ts` - Reusable animation functions
- Service clients (`services/api/`)
- Utility functions (`utils/`)
- Hooks (`hooks/useGsapContext`, etc.)

✅ **Backend Integration**
- `/evaluate` endpoint
- `/demo/scenarios` endpoints
- Health checks
- Audit log API

### What Must Change (Rebuild)
❌ **Current Landing Page Issues**
- `LandingPremium.tsx` - Card-heavy, generic composition
- `EnhancedHero.tsx` - Stats cards feel template-y
- `PremiumFeatures.tsx` - 6 identical feature cards
- `ArchitectureViz.tsx` - Diagram is static, not narrative

**Core Problem**: The page DESCRIBES Sentinel instead of SHOWING the security decision.

---

## New Architecture: 8-Scene Scroll Narrative

### Scene Structure

```
├── Navigation (Floating → Sticky)
├── Hero: Immersive Opening
│   ├── Technical Eyebrow
│   ├── Massive Statement
│   ├── Security Field Visualization
│   └── Primary CTAs
├── Scene 01: Intent Arrives
│   └── Full viewport, technical intent object enters
├── Scene 02: Behavioral Observation
│   └── Signals extract, Expected vs Observed
├── Scene 03: Risk Buildup
│   └── Score increases: 31 → 47 → 63 → 78 → 92
├── Scene 04: Policy Evaluation
│   └── Condition threshold exceeded visualization
├── Scene 05: Decision
│   └── Three-path branch: ALLOW / ESCALATE / CONTAIN
├── Scene 06: Capability Token
│   └── Two paths: Token Issued vs Token NOT Issued
├── Scene 07: Execution (CLIMAX)
│   └── Boundary closes, execution blocked
├── Scene 08: Audit Ledger
│   └── Hash-linked chain visualization
├── Evidence Section
│   └── Large bold metrics (97.2%, <30ms, etc.)
├── Architecture Pipeline
│   └── Interactive node-based visualization
├── Security Principles (Editorial)
│   └── Vertical editorial, not cards
└── Final CTA
    └── Statement + Actions
```

---

## Phase-by-Phase Implementation

### Phase 1: Foundation & Design Tokens
**Duration**: 30 minutes

**Tasks**:
1. Update `tailwind.config.js`:
   - Add Space Grotesk font
   - Add IBM Plex Mono
   - Refine color tokens per visual direction
   - Add atmospheric gradient utilities
   - Typography scale (10px → 96px)

2. Create shared components:
   - `<TechnicalData>` - Intent/token display component
   - `<RiskMeter>` - Animated risk visualization
   - `<DecisionBranch>` - Three-path decision UI
   - `<AuditChain>` - Hash link visualization

**Output**: Design system ready

---

### Phase 2: Navigation Rebuild
**Duration**: 20 minutes

**File**: `frontend/src/components/navigation/CinematicNav.tsx`

**Features**:
- Floating minimal nav (transparent)
- Sticky on scroll (solid background)
- Logo + 5 links + Dashboard CTA
- Smooth transition
- Mobile hamburger

**Visual QA**: Test scroll behavior, mobile responsiveness

---

### Phase 3: Hero Reconstruction
**Duration**: 45 minutes

**File**: `frontend/src/pages/Landing/CinematicHero.tsx`

**Structure**:
```tsx
<section className="min-h-screen relative">
  {/* Atmospheric background */}
  
  {/* Technical eyebrow */}
  <div className="text-xs uppercase tracking-wider">
    AI Agent Authorization & Containment Layer
  </div>
  
  {/* Massive statement */}
  <h1 className="text-8xl font-black">
    YOUR AGENTS CAN ACT.
    THEY SHOULD NOT ACT
    WITHOUT BEING VERIFIED.
  </h1>
  
  {/* Supporting copy */}
  <p className="text-xl">...</p>
  
  {/* CTAs */}
  <Button>RUN LIVE SIMULATION</Button>
  <Button>EXPLORE ARCHITECTURE</Button>
  
  {/* Security Field Visualization */}
  <SecurityFieldViz />
</section>
```

**Visual QA**: Typography hierarchy, spacing, atmosphere

---

### Phase 4: Security Field Visualization
**Duration**: 60 minutes

**File**: `frontend/src/components/visualizations/SecurityField.tsx`

**What It Shows**:
- Intent object (left side) moving toward execution boundary (right)
- Behavioral signals emerge as it moves
- Risk score calculated
- Subtle GSAP animation (continuous loop)

**Technology**:
- SVG for shapes
- CSS for styling
- GSAP for animation
- No Canvas unless needed

**Visual QA**: Animation smoothness, mobile scaling

---

### Phase 5: Scene 01 - Intent Arrives
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene01IntentArrives.tsx`

**Structure**:
```tsx
<section className="min-h-screen flex items-center justify-center">
  <IntentObject
    agent="payment-agent-01"
    action="payout.execute"
    amount="₹52,400"
    recipient="merchant_481"
    timestamp="10:42:31"
  />
</section>
```

**Scroll Behavior**:
- Pin scene while scrolling
- Intent enters from left
- Minimal copy, maximum visual

**Visual QA**: Pin timing, entrance animation

---

### Phase 6: Scene 02 - Behavioral Observation
**Duration**: 45 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene02Behavioral.tsx`

**Structure**:
```tsx
<section className="min-h-screen">
  {/* Intent expands */}
  <BehavioralProfile>
    <SignalComparison
      label="AMOUNT"
      expected="₹8K–₹20K"
      observed="₹52.4K"
      status="ELEVATED"
    />
    <SignalComparison
      label="RECIPIENT"
      expected="known"
      observed="new recipient"
      status="NOVEL"
    />
    {/* More signals */}
  </BehavioralProfile>
</section>
```

**Scroll Behavior**:
- Signals fade in sequentially
- Color shifts subtly to indicate deviation

**Visual QA**: Signal timing, readability

---

### Phase 7: Scene 03 - Risk Buildup
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene03Risk.tsx`

**Structure**:
```tsx
<section className="min-h-screen flex items-center justify-center">
  <RiskMeter
    values={[31, 47, 63, 78, 92]}
    final="HIGH RISK"
  />
</section>
```

**Scroll Behavior**:
- Risk score increases with scroll position
- Background tension increases (subtle)
- Typography gets bolder

**Visual QA**: Smooth progression, tension feel

---

### Phase 8: Scene 04 - Policy
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene04Policy.tsx`

**Structure**:
```tsx
<section className="min-h-screen">
  <PolicyRule
    title="HIGH VALUE TRANSFER"
    condition="amount > ₹50,000"
    observed="₹52,400"
    result="THRESHOLD EXCEEDED"
  />
</section>
```

**Scroll Behavior**:
- Policy rule locks onto intent
- Visual connection line appears

**Visual QA**: Policy clarity, visual connection

---

### Phase 9: Scene 05 - Decision
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene05Decision.tsx`

**Structure**:
```tsx
<section className="min-h-screen flex items-center justify-center">
  <DecisionBranch
    options={['ALLOW', 'ESCALATE', 'CONTAIN']}
    selected="CONTAIN"
  />
</section>
```

**Scroll Behavior**:
- Three branches appear
- Selection animates (not explosive, precise)

**Visual QA**: Branch clarity, selection feel

---

### Phase 10: Scene 06 - Capability Token
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene06Token.tsx`

**Structure**:
```tsx
<section className="min-h-screen">
  {/* Show two paths */}
  <TokenPath type="ALLOW">
    <TokenStructure {...jwt} />
  </TokenPath>
  
  <TokenPath type="CONTAIN">
    <TokenDenied />
  </TokenPath>
</section>
```

**Scroll Behavior**:
- CONTAIN path is highlighted
- TOKEN NOT ISSUED displayed

**Visual QA**: Path clarity, token structure readability

---

### Phase 11: Scene 07 - Execution (CLIMAX)
**Duration**: 45 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene07Execution.tsx`

**Structure**:
```tsx
<section className="min-h-screen">
  <ExecutionPipeline>
    <Node>AGENT</Node>
    <Connection />
    <Node>SENTINEL</Node>
    <Connection status="BLOCKED" />
    <Node>EXECUTION</Node>
  </ExecutionPipeline>
  
  <StatusDisplay>
    CONTAIN
    EXECUTION BLOCKED
  </StatusDisplay>
</section>
```

**Scroll Behavior**:
- Signal moves along pipeline
- Sentinel boundary closes
- Execution blocked (visual stop)

**Visual QA**: This is the CLIMAX - must feel impactful but precise

---

### Phase 12: Scene 08 - Audit Ledger
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/scenes/Scene08Audit.tsx`

**Structure**:
```tsx
<section className="min-h-screen">
  <AuditChain>
    <AuditRecord
      timestamp="..."
      intentId="..."
      decision="CONTAIN"
      jti="..."
      previousHash="..."
      recordHash="..."
    />
  </AuditChain>
</section>
```

**Scroll Behavior**:
- Chain visualization reveals
- Hash links animate

**Visual QA**: Technical accuracy, visual clarity

---

### Phase 13: Evidence Section
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/EvidenceSection.tsx`

**Structure**:
```tsx
<section className="py-32">
  <Grid>
    <MetricDisplay value="97.2%" label="Detection Precision" />
    <MetricDisplay value="<30ms" label="Decision Path" />
    <MetricDisplay value="5s" label="Token Lifetime" />
    <MetricDisplay value="100%" label="Fail-Closed" />
    <MetricDisplay value="165+" label="Security Tests" />
    <MetricDisplay value="327 RPS" label="Benchmark" />
  </Grid>
</section>
```

**NOT cards**. Large bold numbers with minimal context.

**Visual QA**: Hierarchy, whitespace

---

### Phase 14: Architecture Pipeline
**Duration**: 45 minutes

**File**: `frontend/src/pages/Landing/ArchitecturePipeline.tsx`

**Structure**:
- Interactive node-based pipeline
- Hover reveals details
- Sequential activation on scroll

**Visual QA**: Interactivity, animation timing

---

### Phase 15: Security Principles (Editorial)
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/PrinciplesEditorial.tsx`

**NOT 5 cards**. Vertical editorial layout.

Each principle:
- Large number
- Bold title
- Technical explanation
- Subtle visual

**Visual QA**: Editorial feel, typography

---

### Phase 16: Final CTA
**Duration**: 20 minutes

**File**: `frontend/src/pages/Landing/FinalCTA.tsx`

**Structure**:
```tsx
<section className="py-32">
  <h2 className="text-6xl font-black">
    TRUST THE AGENT.
    VERIFY THE BEHAVIOR.
    THEN LET IT ACT.
  </h2>
  
  <p>Supporting line...</p>
  
  <ButtonGroup>
    <Button>OPEN SENTINEL</Button>
    <Button>RUN LIVE SIMULATION</Button>
    <Button>READ ARCHITECTURE</Button>
  </ButtonGroup>
</section>
```

**Visual QA**: CTA clarity

---

### Phase 17: Assembly & Main Landing Page
**Duration**: 30 minutes

**File**: `frontend/src/pages/Landing/LandingCinematic.tsx`

Assemble all scenes with proper scroll orchestration:

```tsx
export default function LandingCinematic() {
  useEffect(() => {
    // Initialize GSAP ScrollTrigger
    // Set up pinning
    // Clean up on unmount
  }, []);

  return (
    <>
      <CinematicNav />
      <CinematicHero />
      <Scene01IntentArrives />
      <Scene02Behavioral />
      <Scene03Risk />
      <Scene04Policy />
      <Scene05Decision />
      <Scene06Token />
      <Scene07Execution />
      <Scene08Audit />
      <EvidenceSection />
      <ArchitecturePipeline />
      <PrinciplesEditorial />
      <FinalCTA />
    </>
  );
}
```

**Visual QA**: Full-page scroll flow

---

### Phase 18: Mobile Optimization
**Duration**: 45 minutes

**Tasks**:
- Test at 390px, 430px
- Simplify scenes for mobile
- Adjust typography scale
- Remove complex pinning if needed
- Ensure no horizontal overflow

**Visual QA**: Full mobile audit

---

### Phase 19: Performance Optimization
**Duration**: 30 minutes

**Tasks**:
- Lazy-load GSAP
- Code-split scenes
- Optimize assets
- Clean up ScrollTriggers
- Test Lighthouse

**Target**: Performance ≥ 90

---

### Phase 20: Accessibility Pass
**Duration**: 30 minutes

**Tasks**:
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators
- Reduced motion
- Screen reader testing

---

### Phase 21: Visual QA & Iteration
**Duration**: 60 minutes

**Process**:
1. Build and run locally
2. Capture screenshots (all breakpoints)
3. Critical review against visual direction
4. Identify issues
5. Iterate
6. Repeat until excellent

**Questions to Ask**:
- Does this look AI-generated? (NO)
- Clear visual point of view? (YES)
- Scroll is rewarding? (YES)
- Memorable visual moment? (YES - Scene 07 climax)
- Typography excellent? (YES)
- Hero premium? (YES)
- Story builds tension? (YES)
- Containment earned? (YES)
- Animations purposeful? (YES)
- Anything unnecessary? (NO)

---

## File Structure

```
frontend/src/pages/Landing/
├── LandingCinematic.tsx          # Main assembly
├── CinematicHero.tsx            # Hero section
├── EvidenceSection.tsx          # Metrics
├── ArchitecturePipeline.tsx     # Interactive pipeline
├── PrinciplesEditorial.tsx      # Principles
├── FinalCTA.tsx                 # CTA
└── scenes/
    ├── Scene01IntentArrives.tsx
    ├── Scene02Behavioral.tsx
    ├── Scene03Risk.tsx
    ├── Scene04Policy.tsx
    ├── Scene05Decision.tsx
    ├── Scene06Token.tsx
    ├── Scene07Execution.tsx
    └── Scene08Audit.tsx

frontend/src/components/
├── navigation/
│   └── CinematicNav.tsx
└── visualizations/
    ├── SecurityField.tsx
    ├── IntentObject.tsx
    ├── BehavioralProfile.tsx
    ├── RiskMeter.tsx
    ├── PolicyRule.tsx
    ├── DecisionBranch.tsx
    ├── TokenStructure.tsx
    ├── ExecutionPipeline.tsx
    └── AuditChain.tsx

frontend/src/animations/
├── premiumEffects.ts (existing, keep)
└── scrollNarrative.ts (new, for scroll orchestration)
```

---

## Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Foundation | 30 min | 30 min |
| Navigation | 20 min | 50 min |
| Hero | 45 min | 95 min |
| Security Field | 60 min | 155 min |
| Scene 01 | 30 min | 185 min |
| Scene 02 | 45 min | 230 min |
| Scene 03 | 30 min | 260 min |
| Scene 04 | 30 min | 290 min |
| Scene 05 | 30 min | 320 min |
| Scene 06 | 30 min | 350 min |
| Scene 07 | 45 min | 395 min |
| Scene 08 | 30 min | 425 min |
| Evidence | 30 min | 455 min |
| Architecture | 45 min | 500 min |
| Principles | 30 min | 530 min |
| Final CTA | 20 min | 550 min |
| Assembly | 30 min | 580 min |
| Mobile | 45 min | 625 min |
| Performance | 30 min | 655 min |
| Accessibility | 30 min | 685 min |
| Visual QA | 60 min | 745 min |

**Total**: ~12-13 hours of focused work

**Realistic with breaks**: 2-3 days

---

## Success Criteria

The landing page is complete when:

- ✅ Composition feels intentional, not template-based
- ✅ Visual direction is coherent (calm financial + cinematic)
- ✅ Scroll narrative works (8 scenes flow smoothly)
- ✅ Hero is memorable (security field visualization)
- ✅ Product story is clear (user EXPERIENCES the decision)
- ✅ Animations are meaningful (every motion has purpose)
- ✅ Mobile is excellent (redesigned, not shrunk)
- ✅ Accessibility respected (semantic, keyboard, reduced motion)
- ✅ Performance acceptable (Lighthouse ≥ 90)
- ✅ Browser console clean (no errors)
- ✅ No layout overflow (all breakpoints tested)
- ✅ API/demo integration works (real data where available)
- ✅ Screenshots survive critical review (not AI-generated)

---

## Risk Mitigation

### Risk: Too ambitious for buildathon timeline
**Mitigation**: Build scene-by-scene, stop when "good enough" rather than perfect

### Risk: GSAP performance issues
**Mitigation**: Use transforms/opacity only, clean up triggers, test early

### Risk: Mobile complexity
**Mitigation**: Simplify mobile narrative if desktop takes longer than expected

### Risk: Visual QA reveals fundamental issues
**Mitigation**: Plan includes iteration buffer (60 min)

---

## Post-Reconstruction

After landing is excellent:

1. **Dashboard** - Apply same visual language
2. **Intent Explorer** - Dense, efficient UI
3. **Decision Details** - Forensic investigation UI
4. **Observability** - Infrastructure monitoring UI
5. **Audit** - Technical ledger UI

But **landing comes first**.

---

## Notes

- **DO NOT** start coding until this plan is approved
- **DO** visual QA after each major phase
- **DO** iterate based on browser screenshots
- **DO NOT** skip Phase 21 (visual QA is critical)
- **DO** test in real browser, not just code review
- **DO** respect `prefers-reduced-motion`
- **DO NOT** claim this looks like "Razorpay's internal design"
- **DO** aim for "fintech-quality infrastructure product"

---

**Ready to implement? Awaiting approval to proceed.**
