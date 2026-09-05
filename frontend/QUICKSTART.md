# Sentinel Frontend - Quick Start

## 🚀 Launch Development Server

```bash
cd frontend
npm run dev
```

Then open: **http://localhost:5173**

## 🎯 Pages

- **Landing:** `http://localhost:5173/` - Cinematic hero, terminal demo, bento grid features
- **Dashboard:** `http://localhost:5173/dashboard` - Live execution stream, KPI cards, risk charts

## 🔧 Backend Connection

The frontend proxies to `localhost:8000` for:
- `/api/analytics/dashboard/executive` - Dashboard KPIs & analytics
- `/execution/stream` - Server-Sent Events for live executions

### Start the Demo Server

In the project root (not frontend/):

```bash
python demo_server.py
```

This provides:
- Mock analytics data
- SSE stream for simulated executions
- Demo scenario triggers: `/demo/scenarios/{scenario}`

## 🎨 Key Components

### Landing Page
- **MagneticButton** - Cursor-following buttons with spring physics
- **GlowCard** - Mouse-tracking radial gradient cards
- **TerminalDemo** - Live authorization decision stream
- **AnimatedOrb** - Floating atmospheric gradients
- Glassmorphism nav, scroll-triggered reveals

### Dashboard
- **KPICard** - Animated rolling counters, glassmorphism, mouse glows
- **LiveExecutionStream** - Real-time SSE with flash animations on CONTAIN/ESCALATE
- **RiskTrendChart** - Recharts area chart with 24h trends
- **RecentAlerts** - Color-coded risk alerts with hover effects

## 🎬 Demo Scenarios

Trigger live events via the demo server:

```bash
# Normal traffic
curl -X POST http://localhost:8000/demo/scenarios/normal

# Malicious attempts (CONTAIN decisions)
curl -X POST http://localhost:8000/demo/scenarios/malicious

# Abuse burst (ESCALATE decisions)
curl -X POST http://localhost:8000/demo/scenarios/abuse-burst
```

Watch the dashboard light up with real-time events!

## 🏗️ Build for Production

```bash
npm run build
npm run preview  # Test the production build
```

Output: `frontend/dist/`

## ⚡ Tech Stack

- **React 19** + **TypeScript 6**
- **Vite 8** (build tool)
- **Tailwind CSS 3** (styling)
- **Framer Motion 13** (animations)
- **Recharts 3** (charts)
- **Lucide React** (icons)
- **React Query** (data fetching)

All animations GPU-accelerated. All components production-ready.
