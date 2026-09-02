# Sentinel Frontend Visual Direction
## Design System & Product Experience Philosophy

**Status**: Visual Direction v1.0  
**Date**: August 29, 2026  
**Purpose**: Establish coherent visual language before reconstruction

---

## Problem Statement

The current landing page is **visually clean but compositionally generic**:

- ❌ Excessive card grids (feature cards, metric cards)
- ❌ Weak narrative structure (describes vs. shows)
- ❌ No memorable visual centerpiece
- ❌ Insufficient scroll choreography
- ❌ Everything feels small and disconnected
- ❌ Follows AI-generated SaaS template patterns

**Core Issue**: The page *explains* Sentinel's features rather than making the user *experience* Sentinel's security boundary in action.

---

## Visual Thesis

**CALM FINANCIAL INFRASTRUCTURE + CINEMATIC SECURITY NARRATIVE**

Sentinel is not a consumer app. It's not a crypto project. It's not a gaming platform.

Sentinel is **production infrastructure for financial systems**.

The visual language must communicate:

- **Precision** - Technical exactness
- **Depth** - Layered complexity, not flat surfaces
- **Confidence** - Quiet authority, not loud marketing
- **Instrumentation** - Real system behavior, not decoration
- **Restraint** - Purposeful motion, not decorative animation

---

## Visual Principles

### 1. SHOW, DON'T TELL

**Wrong**:
```
"Sentinel has behavioral detection."
[Feature card with icon]
```

**Right**:
```
[Visual: Intent object enters]
[Behavioral signals extract]
[Risk score increases]
[Policy triggers]
[Execution blocked]
```

The user should **scroll through a security decision** happening in real-time.

### 2. ONE VISUAL SYSTEM, MANY STATES

Create a **single evolving visual system** rather than separate disconnected sections.

The "Sentinel Security Field" becomes the central metaphor:
- Intents enter the field
- Signals are extracted
- Risk is calculated
- Policy is applied
- Execution is controlled

This system should **transform** as the user scrolls, not disappear and get replaced by cards.

### 3. SCALE MATTERS

Typography should vary dramatically:

- **Hero**: Massive (80px+)
- **Scene titles**: Large (48px+)
- **Technical data**: Dense and small (12px)
- **Metrics**: Bold numbers (64px)

Not everything should be 36px heading + 18px paragraph.

### 4. WHITESPACE IS STRUCTURE

Large-scale whitespace creates:
- Visual rhythm
- Breathing room
- Focus
- Premium feel

Small disconnected sections feel crowded and cheap.

### 5. MOTION HAS MEANING

Every animation must answer: **"WHY DOES THIS MOVE?"**

Acceptable reasons:
- ✅ Reveals hierarchy (fade-in on scroll)
- ✅ Shows causality (A causes B)
- ✅ Communicates state (risk increasing)
- ✅ Connects sections (scroll-driven timeline)
- ✅ Rewards exploration (hover reveals detail)

Unacceptable reasons:
- ❌ "Because it looks cool"
- ❌ "To add polish"
- ❌ "Generic entrance animation"

---

## Color System

### Brand
- **Sentinel Blue**: `#2563EB` (Primary)
- **Deep Blue**: `#1E40AF` (Accent)

### Semantic (Decision States)
- **Allow**: `#16A34A` (Green)
- **Escalate**: `#F59E0B` (Amber)
- **Contain**: `#DC2626` (Red)

### Neutrals
- **Background**: `#F7F9FC` (Subtle warm gray)
- **Surface**: `#FFFFFF` (Pure white)
- **Border**: `#E5E7EB` (Soft gray)
- **Text Primary**: `#0F172A` (Near black)
- **Text Secondary**: `#64748B` (Medium gray)
- **Text Muted**: `#94A3B8` (Light gray)

### Atmospheric
- **Field Glow**: `#2563EB` at 5-10% opacity
- **Risk Warning**: `#DC2626` at 3-8% opacity
- **Success Glow**: `#16A34A` at 5% opacity

**Rules**:
- Use color **sparingly** outside the hero and decision states
- Semantic colors should only appear when they carry meaning
- No purple AI gradients
- No excessive glow/glassmorphism
- Background should feel **calm**, not decorative

---

## Typography System

### Fonts
- **Display**: `Space Grotesk` (Headlines, numbers)
- **Body**: `Inter` (Paragraphs, UI)
- **Code**: `IBM Plex Mono` (Technical data, IDs)

### Scale (Desktop)
- **Massive Display**: 80-96px (Hero statement)
- **Large Display**: 56-72px (Scene titles)
- **Display**: 40-48px (Section headings)
- **Heading**: 24-32px (Subsections)
- **Body**: 16-18px (Paragraphs)
- **Small**: 14px (Supporting text)
- **Technical**: 12px (Dense data, labels)
- **Micro**: 10px (Metadata, timestamps)

### Scale (Mobile)
- **Massive Display**: 48-56px
- **Large Display**: 36-42px
- **Display**: 28-32px
- Reduce proportionally but maintain hierarchy

### Weight Distribution
- **Black/Extra Bold** (900/800): Large numbers, massive headlines
- **Bold** (700): Headings, emphasis
- **Semibold** (600): Subheadings, UI labels
- **Regular** (400): Body text
- **Medium** (500): Small technical text

**Anti-pattern**: Don't make everything semibold. Use weight to create hierarchy.

---

## Spacing System

### Vertical Rhythm
- **Scene Gap**: 120-160px (between major sections)
- **Section Gap**: 80-120px (between subsections)
- **Component Gap**: 40-64px (between components)
- **Element Gap**: 16-32px (between related elements)
- **Tight Gap**: 8-16px (within components)

### Horizontal Padding
- **Desktop**: 80-120px edge padding
- **Tablet**: 40-60px edge padding
- **Mobile**: 24-32px edge padding

### Max Width
- **Content**: 1440px (absolute maximum)
- **Reading**: 680px (paragraphs)
- **Technical**: 1200px (data tables, wide layouts)

**Rule**: Use the **full viewport** for cinematic scenes, then constrain reading content.

---

## Composition Patterns

### AVOID
- ❌ **3-column card grids**
- ❌ **Centered marketing blocks**
- ❌ **Icon + Heading + Paragraph cards**
- ❌ **Generic blob backgrounds**
- ❌ **Excessive rounded corners (> 16px)**
- ❌ **Equal-sized sections stacked vertically**

### USE
- ✅ **Full-viewport cinematic scenes**
- ✅ **Asymmetric layouts**
- ✅ **Data-first visualizations**
- ✅ **Editorial typography**
- ✅ **Sticky/pinned scroll scenes**
- ✅ **Horizontal movement where meaningful**
- ✅ **Large-scale whitespace**

---

## Scroll Narrative Structure

The landing page should be a **scroll-driven security narrative**:

```
SCENE 01: INTENT ARRIVES
Full viewport. Technical intent object enters field.

SCENE 02: BEHAVIORAL OBSERVATION  
Signals extract. Visual comparison: Expected vs Observed.

SCENE 03: RISK BUILDUP
Risk score increases visually: 31 → 47 → 63 → 78 → 92

SCENE 04: POLICY EVALUATION
Policy rule visualized. Condition threshold exceeded.

SCENE 05: DECISION
Three branches shown: ALLOW / ESCALATE / CONTAIN
Sentinel selects: CONTAIN

SCENE 06: CAPABILITY TOKEN
Two paths visualized:
- ALLOW: Token issued (show JWT structure)
- CONTAIN: Token NOT issued

SCENE 07: EXECUTION (CLIMAX)
Visual: Signal reaches boundary → Boundary closes → BLOCKED

SCENE 08: AUDIT LEDGER
Decision becomes immutable audit record with hash chain.
```

Each scene should **pin or transform** as the user scrolls, not just fade in/out.

---

## Animation Principles

### Timing
- **Fast**: 200-300ms (micro-interactions, hovers)
- **Medium**: 400-600ms (scene transitions, reveals)
- **Slow**: 800-1200ms (scroll-driven transforms)
- **Scrubbed**: Tied to scroll position (scroll timelines)

### Easing
- **UI Interactions**: `ease-out` (buttons, hovers)
- **Entrances**: `cubic-bezier(0.16, 1, 0.3, 1)` (smooth deceleration)
- **Scroll**: `none` or `linear` (tied to scroll position)
- **Elastic**: Only for special moments (capability denied)

### Types
- **Opacity**: 0 → 1 (reveals)
- **Transform**: translateY, scale (depth, movement)
- **Blur**: For depth layers only
- **Color**: Semantic state changes (risk increasing)

**NO**:
- ❌ Rotate (unless showing rejection/denial)
- ❌ SkewX/Y (unnecessary distortion)
- ❌ 3D transforms (overkill)
- ❌ Continuous infinite loops (distracting)

### Reduced Motion
Respect `prefers-reduced-motion`:
- Disable scroll pinning
- Remove parallax
- Reduce to simple fade-in
- Keep state changes
- Keep meaning

---

## Atmospheric Techniques

### Subtle Depth
- **Radial gradients**: 5-10% opacity, massive scale
- **Soft glows**: Around risk/decision moments
- **Technical grid lines**: 1px, subtle
- **Noise texture**: < 2% opacity if needed
- **Blur layers**: Far background only

### Forbidden
- ❌ **Blob gradients** (overdone)
- ❌ **Neon glow** (wrong aesthetic)
- ❌ **Glassmorphism** (trendy, not timeless)
- ❌ **Cyberpunk grid** (wrong tone)
- ❌ **Particle effects** (distracting)

---

## Component Philosophy

### Hero
- **NOT**: Logo + Headline + 2 buttons + 4 metric cards
- **IS**: Immersive opening scene with live security field visualization

### Navigation
- **NOT**: Heavy bar with dropdowns
- **IS**: Floating minimal nav that transitions on scroll

### Metrics
- **NOT**: 6 identical cards in a grid
- **IS**: Large, bold numbers with minimal context (97.2%, <30ms, 100%)

### Architecture
- **NOT**: Generic flow diagram
- **IS**: Interactive pipeline with hover states and sequential activation

### Principles
- **NOT**: 5 identical cards
- **IS**: Vertically evolving editorial section with varied typography

### CTA
- **NOT**: Centered text block with gradient
- **IS**: Confident statement + action buttons

---

## Anti-AI-Slop Checklist

Before finalizing, verify:

- [ ] No excessive card grids
- [ ] No purple AI gradient
- [ ] No generic blob backgrounds
- [ ] No meaningless animations
- [ ] No fake dashboard screenshots
- [ ] No invented metrics
- [ ] Typography hierarchy is dramatic
- [ ] Whitespace feels intentional
- [ ] One section flows into the next
- [ ] Scroll reveals something meaningful
- [ ] Hero has a memorable visual moment
- [ ] The page tells a story, not a feature list

---

## Mobile Strategy

**Not**: Shrink desktop

**Is**: Redesign for vertical scroll narrative

- Simplify scenes to single-column
- Reduce typography scale proportionally
- Keep scroll narrative structure
- Remove complex pinning if necessary
- Ensure all technical data remains readable
- Test at 390px minimum

---

## Performance Targets

- **Lighthouse Performance**: ≥ 90
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Total Blocking Time**: < 300ms
- **Cumulative Layout Shift**: < 0.1

**Strategy**:
- Lazy-load GSAP for landing page only
- Use transforms (GPU-accelerated)
- Avoid layout thrashing
- Clean up ScrollTriggers on unmount
- Code-split heavy routes

---

## Accessibility Requirements

- Semantic HTML structure
- Keyboard navigation for all interactive elements
- Focus indicators (2px outline, offset)
- ARIA labels where necessary
- Color-independent status (icons + text)
- Reduced motion support
- Screen reader friendly (scene structure)
- Alt text for visual metaphors

---

## Visual QA Process

After implementation:

1. **Build & Run**
2. **Capture Screenshots** (1440px, 1280px, 1024px, 768px, 430px, 390px)
3. **Critical Review**:
   - Does this look AI-generated?
   - Is there a clear visual point of view?
   - Is scrolling rewarding?
   - Is there a memorable visual moment?
   - Is typography excellent?
   - Are animations purposeful?
4. **Iterate**
5. **Browser Console** (check for errors)
6. **Performance** (Lighthouse audit)
7. **Accessibility** (axe DevTools)

**DO NOT stop when code compiles. Stop when visuals are excellent.**

---

## Signature Visual Language

**Sentinel's visual signature**:

1. **The Security Field** - Evolving boundary visualization
2. **Technical Data Artifacts** - Intent objects, signals, tokens shown as structured data
3. **Progressive Risk Tension** - Visual buildup from calm to critical
4. **Deterministic Branching** - Three-path decision visualization
5. **Hash-Linked Audit** - Chain visualization for audit trail

These should be **recognizable as Sentinel** and **not generic security imagery**.

---

## Final Standard

The landing page should make a judge think:

1. "This team understands **product design**"
2. "They understand **frontend engineering**"
3. "They understand **financial infrastructure**"
4. "They understand **security**"
5. "I want to **see this system run**"

**NOT**:
- "This looks like a nice AI-generated template"
- "Pretty, but generic"
- "Where's the actual product?"

---

## Next Steps

1. Create `docs/frontend-reconstruction-plan.md`
2. Audit current implementation against this direction
3. Identify components to preserve vs rebuild
4. Design the 8-scene scroll narrative in detail
5. Build scene-by-scene with visual QA between each
6. Iterate until excellent

---

**This direction is the foundation. Code comes after clarity.**
