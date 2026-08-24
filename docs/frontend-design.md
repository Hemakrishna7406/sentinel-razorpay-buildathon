# Sentinel — frontend-design.md

Design direction for the **pitch/landing page** (the page a judge or the panel opens before the live demo) and the visual language the dashboard in `frontend.md` inherits from it. Razorpay-inspired in spirit — dark, precise, product-screenshot-driven — not a literal copy of Razorpay's palette or components.

---

## 1. Brief, pinned down

**Subject**: a behavioral-risk detector that watches AI financial agents and asks "is this agent still behaving like the agent we trusted." **Audience**: a technical fintech hiring panel, in a demo room, on a laptop screen. **Page's single job**: make the loss class and the detection mechanism legible in the first 20 seconds — this page IS the 0:00–0:20 demo beat, rendered as a page instead of spoken.

## 2. Design plan (pass 1)

**Color** — a control-room register, not a fintech-brochure register. Named tokens:
- `--ink` `#0A0E1A` — page background, near-black navy, not pure black (avoids the generic "near-black + neon" default)
- `--panel` `#121A2E` — card/section surfaces
- `--signal` `#4C8DFF` — trust / SAFE / baseline state, the "this agent is itself" color
- `--drift` `#F5A623` — SUSPICIOUS / escalation state
- `--contain` `#E5484D` — HIGH-RISK / CONTAIN state
- `--text` `#E8ECF7` — primary text
- `--muted` `#6B7592` — secondary text, hairlines, dividers

**Type** — three roles, chosen for what the subject actually is (a measurement instrument, not a consumer app):
- Display: **Space Grotesk** — geometric, slightly technical, used only for the hero headline and section numerals, never for body copy
- Body: **Inter** — neutral, high legibility at small sizes for explanatory copy
- Data/mono: **IBM Plex Mono** — every number on the page (risk scores, precision/recall, ₹ amounts, timestamps) renders in this face. This is a deliberate choice, not decoration: it visually reinforces the page's own thesis ("measured on held-out data, not vibes") by making measured numbers look different from prose.

**Layout concept** — the page IS the pipeline. Section order mirrors the actual system flow (Agent → Intent → Behavioral Drift → Risk Decision → Containment), because that sequence carries real information — it's the one place numbered/ordered structure is earned rather than decorative (per the "question numbered markers" guidance: here the order is the architecture, not an arbitrary list).

```
[ HERO: pulse line, one-sentence thesis ]
[ 01 AGENT — a card showing a real agent baseline ]
[ 02 INTENT — a live-looking intent hits the pipeline ]
[ 03 DRIFT — baseline vs. current, deviating ]
[ 04 DECISION — SAFE/SUSPICIOUS/HIGH-RISK, with the real held-out metrics ]
[ 05 CONTAINMENT — capability token denied, fail-closed proof ]
[ CLOSE — the one-line thesis, repeated ]
```

**Signature element — the Trust Pulse.** A single continuous waveform, styled like a heart-rate monitor line, running across the hero. It reads as a steady, regular rhythm (the agent's normal behavioral baseline) — until the user scrolls to the DRIFT section, where the same line visibly breaks rhythm: amplitude spikes, spacing becomes erratic, color shifts from `--signal` to `--drift` to `--contain`. This is the one piece of boldness the whole page spends: a heartbeat monitor is an intuitive, near-universal visual metaphor for "is this thing still behaving normally," and it's literally what the product does, not a generic AI-dashboard flourish.

## 3. Critique against the brief (pass 2 — before building)

- A dark background + single accent risks reading as the generic "near-black + neon accent" AI-design default. **Revision**: keep the base near-black, but make the signature element (the pulse line) carry three colors across its own journey (signal → drift → contain) rather than one static neon accent sitting decoratively in a corner — the color *is* the narrative, not an accessory to it. That's different enough from the default to earn the palette.
- Numbered section markers (01–05) risk reading as templated. **Kept anyway**, because here the numbers are the literal pipeline order from `architecture.md` §3 — removing them would remove real information, which is the opposite of the guidance's concern.
- Considered a big-number hero stat ("97% precision") as the opening move — rejected. It's the template answer, and it also undercuts the page's own thesis: leading with an unverified number before showing the mechanism that produced it is exactly the "vibes" the product argues against. The pulse line leads instead; the real numbers appear in section 04, in context, in the mono face.

## 4. Scroll choreography (Razorpay-inspired: sticky panels, deliberate reveals, product-screenshot-first — not scattered parallax)

- **Hero**: Trust Pulse animates continuously on load (CSS/SVG `stroke-dashoffset` loop), independent of scroll — this is the ambient-atmosphere use of motion, not scroll-triggered.
- **01–05 sections**: each section's visual (agent card, intent card, drift meter, decision panel, capability-denied panel) is **sticky within its section** while supporting copy scrolls past beside it — one orchestrated moment per section, not five separate scroll gimmicks. This is the Razorpay-marketing-site pattern (sticky product visual, scrolling narrative) rather than fade-everything-in.
- **Transition into 03 DRIFT**: this is the one place scroll position directly drives an animation value — the pulse line's amplitude and color interpolate with scroll progress through the section (`IntersectionObserver` + a 0–1 progress value, not scroll-jacking the whole page). Everywhere else, reveals are simple opacity/translateY-on-enter, 200–300ms, no bounce, no stagger-for-its-own-sake.
- **04 DECISION**: the metric numbers (precision, recall, PR-AUC, false-escalation) count up from 0 to their real measured value on scroll-into-view, using the mono face — the one "counting number" moment on the page, used because these are the numbers the whole page exists to justify, not because count-up is a default hero move.
- **prefers-reduced-motion**: pulse line becomes a static waveform image at its "current" state per section; count-ups render their final value immediately; sticky-scroll sections degrade to normal document flow (sticky positioning removed, not just animation removed).

## 5. Component tokens (Tailwind config excerpt)

```js
// tailwind.config.js
colors: {
  ink: '#0A0E1A', panel: '#121A2E',
  signal: '#4C8DFF', drift: '#F5A623', contain: '#E5484D',
  text: '#E8ECF7', muted: '#6B7592',
},
fontFamily: {
  display: ['"Space Grotesk"', 'sans-serif'],
  body: ['"Inter"', 'sans-serif'],
  mono: ['"IBM Plex Mono"', 'monospace'],
},
```

## 6. Dashboard inheritance (`frontend.md`)

The live dashboard (post-pitch-page, the actual product) uses the same token set but drops the scroll choreography entirely — a working dashboard needs density and speed, not narrative pacing. It keeps: the ink/panel/signal/drift/contain color mapping (consistent `RiskBadge` colors across both the pitch page and the dashboard is what makes the whole thing feel like one product, not a marketing site bolted onto a different app), the mono face for every number, and a simplified, static (non-animated) version of the DriftMeter as `components/DriftMeter.tsx`.

## 7. What to explicitly avoid

No particle backgrounds, no glassmorphism, no gradient text, no generic "AI orb" or neural-network-lines motif — none of these say anything true about behavioral drift detection specifically, and per the design skill's calibration note, they're exactly the kind of decoration that reads as AI-generated-by-default rather than chosen for this subject.
