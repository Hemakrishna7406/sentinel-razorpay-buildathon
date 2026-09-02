# Sentinel Demo & Presentation Guide
## Razorpay Buildathon 2026

**Duration**: 5-7 minutes  
**Goal**: Show production-ready AI agent authorization layer  
**Key Message**: Zero-trust execution for autonomous financial agents

---

## Demo Flow (5 Minutes)

### Act 1: The Problem (30 seconds)

**Opening Hook:**
> "What happens when an AI agent with payment authority gets compromised?"

**The Setup:**
- Traditional RBAC says: "Agent X can make payments up to ₹10,000"
- But what if Agent X is hacked? Prompt-injected? Hallucinating?
- **Static permissions can't detect behavioral drift**

**Visual**: Show a normal transaction executing instantly

---

### Act 2: The Solution - Live Demo (3 minutes)

#### Demo 1: Normal Transaction (30s)
```
✅ ALLOW Decision
- Agent: checkout-agent-01
- Amount: ₹1,500
- Behavioral Risk: 5%
- Decision: ALLOW in 28ms
- Capability Token Issued
```

**Narration:**
> "Normal transaction. Behavioral model sees typical patterns. Sub-30ms decision. Capability token issued. Payment executes."

#### Demo 2: Behavioral Drift Detection (45s)
```
⚠️ CONTAIN Decision
- Agent: checkout-agent-01
- Amount: ₹50,000 (x31 spike)
- Behavioral Risk: 91%
- Semantic Risk: 85%
- Decision: CONTAIN
- Reason: "Velocity anomaly - 31x baseline"
```

**Narration:**
> "Same agent, but sudden velocity spike. XGBoost model detects 31x baseline. No capability token issued. Transaction blocked. This is the fail-closed guarantee."

#### Demo 3: Infrastructure Failure = ESCALATE (45s)
```
🔴 ESCALATE Decision
- Scenario: Redis Down
- Decision: ESCALATE
- Reason: "Idempotency state unavailable"
- No Capability Token
```

**Narration:**
> "Critical infrastructure fails. Redis is down. Can't verify idempotency. Sentinel doesn't guess - it escalates. No uncertainty produces ALLOW. Ever."

#### Demo 4: Real-Time Execution Pipeline (30s)

Show the **SSE stream** visualization:
```
INTENT → BEHAVIOR → POLICY → CAPABILITY → MCP → RAZORPAY ✅
```

**Narration:**
> "Every authorization flows through four planes. Decision Plane evaluates. Audit Plane records cryptographically. Observability Plane monitors. Recovery Plane handles failures. This is the architecture that makes autonomous agents safe."

---

### Act 3: The Evidence (90 seconds)

**Show the Grafana Dashboard (30s)**
- Real-time metrics
- p99 latency < 30ms
- 327 RPS baseline (CPU)
- Decision distribution

**Show the Audit Log (30s)**
- Cryptographic chain
- Genesis-to-latest verification
- Immutable history
- Every decision reconstructible

**Show the Architecture (30s)**
```
4 Planes:
✅ Decision  - XGBoost + Policy + Tokens
✅ Audit     - PostgreSQL + Merkle Chain
✅ Observe   - Prometheus + Grafana + Jaeger
✅ Recovery  - Kafka + Idempotency
```

---

## Key Talking Points

### 1. Fail-Closed Guarantee
- "Any infrastructure uncertainty produces ESCALATE, never ALLOW"
- "Redis down? ESCALATE. Kafka timeout? ESCALATE. Model unreachable? ESCALATE."
- **This is the security primitive that makes AI agents production-safe**

### 2. Performance
- "Sub-30ms authorization path"
- "97.2% precision in behavioral detection"
- "Sub-1ms ML inference on CPU"
- "No perceptible latency added to financial transactions"

### 3. Production-Ready Engineering
- "165+ security tests passing"
- "Docker-compose deployment ready"
- "Kubernetes manifests included"
- "Prometheus + Grafana + Jaeger observability"
- "Cryptographic audit chain from genesis"

### 4. Razorpay Integration
- "Direct SDK integration ready"
- "MCP protocol support"
- "Test and live mode support"
- "Built for the Razorpay ecosystem"

---

## Demo Script Commands

### Setup (Before Demo)

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for healthy
curl http://localhost:8000/health/ready

# 3. Open browser tabs
# Tab 1: Landing page (http://localhost:8000)
# Tab 2: Dashboard (http://localhost:8000/dashboard)
# Tab 3: Grafana (http://localhost:3000)
```

### During Demo

#### Normal Transaction
```bash
curl -X POST http://localhost:8000/demo/scenarios/normal
# Watch SSE stream update in real-time
```

#### Abuse Burst
```bash
curl -X POST http://localhost:8000/demo/scenarios/abuse-burst
# Show CONTAIN decision
```

#### Infrastructure Failure
```bash
# Simulate Redis down
docker-compose stop redis
curl -X POST http://localhost:8000/evaluate # ... (will ESCALATE)

# Restart
docker-compose start redis
```

---

## Presentation Slides (Optional Visual Aid)

### Slide 1: Title
```
SENTINEL
AI Agent Authorization Layer

Built for Razorpay Buildathon 2026
```

### Slide 2: The Problem
```
AI Agents Need More Than RBAC

❌ Static permissions
❌ Can't detect drift
❌ Can't see compromise

✅ Behavioral detection
✅ Real-time risk scoring
✅ Fail-closed execution
```

### Slide 3: The Solution
```
4-Plane Architecture

Decision  → XGBoost + Policy
Audit     → Cryptographic Chain
Observe   → Prometheus + Grafana
Recovery  → Kafka + Idempotency
```

### Slide 4: The Results
```
Performance:
- p99 < 30ms
- 97.2% precision
- 327 RPS (CPU)

Security:
- 0 unsafe ALLOWs
- 100% fail-closed
- Cryptographically auditable
```

### Slide 5: Production Ready
```
✅ Docker-compose deployment
✅ Kubernetes manifests
✅ Razorpay SDK integrated
✅ 165+ tests passing
✅ Load tested
✅ Observability complete
```

---

## Handling Q&A

### Q: "How does this compare to Razorpay's existing fraud detection?"
**A:** "Sentinel is complementary. Razorpay detects fraud at the payment level. Sentinel detects behavioral drift at the agent level - before the payment API is even called. We're a pre-authorization layer."

### Q: "What's the performance overhead?"
**A:** "Sub-30ms p99 latency. XGBoost inference is sub-1ms on CPU. This is faster than typical payment gateway latency. No perceptible overhead."

### Q: "How do you handle false positives?"
**A:** "10% false escalation rate, which is intentional policy friction. Better to escalate an uncertain transaction than to blindly ALLOW it. The audit log provides full context for every decision."

### Q: "Can this scale to production traffic?"
**A:** "Yes. 327 RPS per pod on CPU, 3000+ RPS on GPU. Horizontal scaling proven. Kafka-based architecture for distributed processing. Load tested up to 500 concurrent users."

### Q: "What about the ML model - how is it trained?"
**A:** "XGBoost trained on synthetic behavioral scenarios with temporal and agent-level splits to prevent leakage. Features: velocity, amounts, recipients, operating hours. Deterministic evaluation - same seed produces same results."

### Q: "How does the fail-closed guarantee work?"
**A:** "Any exception, timeout, or infrastructure failure forces ESCALATE without issuing a capability token. No token = no execution. It's cryptographically enforced at 10 invariant checkpoints."

---

## Success Metrics (For Judges)

### Technical Excellence
- ✅ Production-grade architecture
- ✅ Fail-closed security design
- ✅ Sub-30ms performance
- ✅ Full observability stack
- ✅ Comprehensive testing

### Business Value
- ✅ Solves real problem (AI agent security)
- ✅ Razorpay-native integration
- ✅ Clear deployment path
- ✅ Scalable architecture

### Innovation
- ✅ 4-plane architecture (unique)
- ✅ Capability token pattern
- ✅ Cryptographic audit chain
- ✅ Behavioral drift detection

---

## Post-Demo Follow-Up

**Leave Behind:**
1. GitHub repository link
2. Demo video URL
3. Architecture diagram (PDF)
4. Contact information

**Call to Action:**
> "Sentinel makes autonomous AI financial agents safe to deploy in production. It's open-source, Razorpay-native, and ready today. Let's put a security boundary between AI and money."

---

## Demo Checklist

### 24 Hours Before
- [ ] Test all demo scenarios
- [ ] Record backup video (in case of live demo issues)
- [ ] Charge laptop
- [ ] Test projector/screen share
- [ ] Prepare backup slides (PDF)

### 1 Hour Before
- [ ] Start services (`docker-compose up -d`)
- [ ] Verify health checks
- [ ] Open browser tabs
- [ ] Close unnecessary applications
- [ ] Silent notifications
- [ ] Full screen mode ready

### During Demo
- [ ] Speak clearly and confidently
- [ ] Point to visuals as you explain
- [ ] Pause for dramatic effect (especially on CONTAIN)
- [ ] Make eye contact with judges
- [ ] Smile and show enthusiasm
- [ ] Time yourself (5 min max)

### After Demo
- [ ] Thank judges
- [ ] Offer to answer questions
- [ ] Share repository link
- [ ] Collect feedback

---

**Remember**: The best demos tell a story. You're not just showing code - you're showing how Sentinel solves a real problem that Razorpay will face as they deploy AI agents.

**Good luck! 🚀**
