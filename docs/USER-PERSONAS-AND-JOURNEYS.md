# Sentinel RC1 - User Personas & Journey Maps

**Date**: 2026-08-29  
**Created By**: Principal Product Designer

---

## User Personas

### Persona 1: Security Engineer - Priya Sharma

**Demographics**:
- Age: 32
- Role: Senior Security Engineer
- Company: Mid-size fintech (500 employees)
- Location: Bangalore, India
- Experience: 8 years in security, 3 years in fintech

**Background**:
Priya leads the security operations team responsible for monitoring and responding to threats across their AI agent infrastructure. She's technically deep, writes Python scripts for automation, and is on-call rotation. She's evaluated multiple security tools and values evidence over marketing claims.

**Goals**:
1. **Detect threats early** - catch compromised agents before damage occurs
2. **Investigate incidents quickly** - understand root cause when alerts fire
3. **Prove compliance** - demonstrate audit trail to regulators
4. **Reduce false positives** - alert fatigue is her biggest pain point
5. **Automate responses** - contain threats without manual intervention

**Pain Points**:
- 🚨 **Alert fatigue** - too many low-priority alerts drown out real threats
- 🔍 **Unclear root causes** - alerts fire but don't explain *why*
- ⏱️ **Slow investigation** - correlating logs across systems takes hours
- 📊 **No behavioral baselines** - can't tell normal from anomalous
- 🔗 **Tampered audit logs** - can't trust third-party execution logs

**Critical Features**:
- Real-time threat detection with behavioral baselines
- Detailed incident investigation (intent timeline, risk breakdown)
- Cryptographic audit chain verification
- Automated containment policies
- Export capabilities for compliance reports

**Key Pages**:
1. **Security Command Center** - primary workspace
2. **Audit Ledger** - compliance and investigation
3. **Live Decisions** - real-time threat monitoring
4. **Policies** - tune containment rules

**User Quote**:
> "I need to know the *why* behind every alert. If I can't explain it to my CISO, the alert is useless."

**Success Metrics**:
- Mean time to detection (MTTD) < 30 seconds
- Mean time to investigation (MTTI) < 5 minutes
- Zero tampered audit records
- Alert fatigue reduced (< 10 false positives per day)

---

### Persona 2: DevOps Engineer - Arjun Patel

**Demographics**:
- Age: 28
- Role: DevOps Engineer
- Company: Fast-growing startup (150 employees)
- Location: Pune, India
- Experience: 5 years DevOps, 2 years with AI/ML systems

**Background**:
Arjun maintains the infrastructure that runs their AI agents. He's responsible for uptime, performance, and scaling. He's not a security expert but needs to understand when security systems impact performance. He's hands-on with Kubernetes, Kafka, and observability tools.

**Goals**:
1. **Keep systems running** - 99.9% uptime SLA
2. **Troubleshoot outages quickly** - minimize downtime
3. **Monitor performance** - latency, throughput, error rates
4. **Understand dependencies** - what breaks when Redis goes down?
5. **Plan capacity** - anticipate scaling needs

**Pain Points**:
- 📉 **Service downtime** - unclear what caused outage
- 🐌 **Slow queries** - authorization delays slow down agents
- 🔧 **Unclear errors** - error messages don't point to root cause
- 📊 **Missing metrics** - can't track SLI/SLO compliance
- 🚨 **Noisy alerts** - woken up for non-critical issues

**Critical Features**:
- System health dashboard (Redis, Kafka, DB, ML model)
- Latency metrics (p50, p95, p99)
- Error logs with context
- Dependency health checks
- Performance trends over time

**Key Pages**:
1. **Dashboard Overview** - primary workspace
2. **Observability** (when built) - deep performance metrics
3. **Live Decisions** - see real-time throughput
4. **Audit Ledger** - investigate specific errors

**User Quote**:
> "When something breaks at 3am, I need to know immediately: what broke, why, and how to fix it. No guessing."

**Success Metrics**:
- Uptime > 99.9%
- p99 latency < 100ms
- Mean time to recovery (MTTR) < 15 minutes
- Zero silent failures

---

### Persona 3: Compliance Officer - Rajesh Kumar

**Demographics**:
- Age: 45
- Role: Head of Compliance
- Company: Established bank (5000 employees)
- Location: Mumbai, India
- Experience: 20 years in banking, 10 years in compliance

**Background**:
Rajesh ensures the bank meets RBI regulations and internal audit requirements. He's not technical but needs to understand how systems ensure compliance. He's responsible for regulatory reporting and internal audits. He's risk-averse and values documentation over speed.

**Goals**:
1. **Audit trail completeness** - every transaction logged
2. **Regulatory compliance** - meet RBI, PCI-DSS requirements
3. **Evidence of controls** - prove security measures work
4. **Export reports** - generate compliance reports quarterly
5. **Tamper-proof records** - logs can't be altered

**Pain Points**:
- 📋 **Incomplete audit logs** - missing critical fields
- 🔓 **Tampered records** - can't trust third-party logs
- 📊 **Manual reporting** - generating reports takes days
- 🔍 **No search** - finding specific transactions difficult
- ⏱️ **Slow audits** - reviewing logs manually is tedious

**Critical Features**:
- Complete audit trail (every decision logged)
- Cryptographic chain verification (tamper-proof)
- Export to CSV/PDF for regulators
- Search and filter by date, agent, decision
- Compliance reports (summary, detailed, exception report)

**Key Pages**:
1. **Audit Ledger** - primary workspace
2. **Security Command Center** - verify security invariants
3. **Dashboard Overview** - executive summary
4. **Policies** - document authorization rules

**User Quote**:
> "I need to prove to auditors that every transaction is logged, traceable, and tamper-proof. No exceptions."

**Success Metrics**:
- 100% audit trail completeness
- Zero tampered records (cryptographic verification)
- Audit report generation < 1 hour
- Regulatory audit passes (zero findings)

---

## User Journey Maps

### Journey 1: Investigating a Suspicious Transaction (Priya - Security Engineer)

**Scenario**: Priya receives an alert that an agent attempted a high-value transaction that was escalated.

**Stages**:

#### 1. Discovery (Alert Received)
- **Touchpoint**: Security Command Center / Email / Slack
- **Actions**: 
  - Sees alert: "payments-agent attempted ₹2.4L transfer (ESCALATE)"
  - Clicks notification to navigate to Sentinel
- **Thoughts**: "Is this a real threat or false positive?"
- **Emotions**: 😟 Concerned (high value), 🤔 Curious
- **Pain Points**: ⚠️ Alert doesn't show context (why escalated?)

**Improvements Needed**:
- Add rich context to alerts (risk score, reason codes)
- Link directly to intent details page
- Show agent behavioral history in alert

---

#### 2. Investigation (Gathering Context)
- **Touchpoint**: Live Decisions → Intent Details
- **Actions**:
  - Searches for intent ID in Live Decisions
  - Clicks decision card to see full details
  - Reviews risk breakdown (behavioral, semantic, policy)
  - Checks agent history (normal vs. anomalous)
- **Thoughts**: "What triggered the escalation? Is the agent compromised?"
- **Emotions**: 🔍 Investigating, 🤨 Skeptical
- **Pain Points**: 
  - ❌ **No direct link from alert to intent details**
  - ❌ **Agent history not shown** (needs separate page)
  - ⚠️ Reason codes cryptic ("BEHAVIORAL_DRIFT_HIGH")

**Improvements Needed**:
- Add Intent Details page with full context
- Show agent behavioral timeline (baseline vs. current)
- Translate reason codes to plain English
- Add "Related Decisions" from same agent

---

#### 3. Decision (Determine Action)
- **Touchpoint**: Intent Details → Policies
- **Actions**:
  - Determines agent is likely compromised (spike in high-value requests)
  - Navigates to Policies page
  - Creates containment policy: "Block all payments-agent requests > ₹50K"
  - Saves policy
- **Thoughts**: "I need to contain this agent until we investigate offline"
- **Emotions**: ⚡ Decisive, 😤 Frustrated (manual policy creation)
- **Pain Points**: 
  - ⚠️ **Manual policy creation** (should have "Contain Agent" quick action)
  - ❌ **No confirmation** when policy saved
  - ❌ **Can't see policy impact** (how many requests will be blocked?)

**Improvements Needed**:
- Add "Contain Agent" quick action button on Intent Details
- Show confirmation toast when policy saved
- Show policy impact preview (e.g., "Will block 12 pending requests")

---

#### 4. Resolution (Verify Containment)
- **Touchpoint**: Security Command Center → Live Decisions
- **Actions**:
  - Navigates to Security Command Center
  - Verifies "Unauthorized Executions" still = 0
  - Checks Live Decisions to confirm agent requests blocked
  - Creates incident report
- **Thoughts**: "Good, the agent is contained. Now I need to document this."
- **Emotions**: ✅ Relieved, 📝 Focused
- **Pain Points**: 
  - ❌ **No incident report export** (manual copy-paste)
  - ⚠️ **Can't share investigation with team** (no collaboration features)

**Improvements Needed**:
- Add "Export Incident Report" button (PDF with timeline, risk scores, policies)
- Add comment/note feature on intent details
- Add sharing link to send investigation to team

---

#### 5. Post-Incident (Documentation & Learning)
- **Touchpoint**: Audit Ledger → Export
- **Actions**:
  - Navigates to Audit Ledger
  - Filters by payments-agent, last 24 hours
  - Exports CSV for incident report
  - Shares with team and management
- **Thoughts**: "I need to document this for the post-mortem"
- **Emotions**: 📊 Analytical, 😌 Satisfied
- **Pain Points**: 
  - ⚠️ **CSV export missing fields** (no risk scores, reason codes)
  - ❌ **No built-in incident timeline** (manual reconstruction)

**Improvements Needed**:
- Add comprehensive CSV export with all fields
- Add Incident Timeline view (visual reconstruction of events)
- Add "Lessons Learned" section to document root cause

**Journey Duration**: 15 minutes (target: < 10 minutes)

---

### Journey 2: Responding to a Security Alert (Priya - Security Engineer)

**Scenario**: Priya receives a critical alert that the audit chain has been broken (security invariant violated).

**Stages**:

#### 1. Alert Received
- **Touchpoint**: Security Command Center / PagerDuty
- **Actions**: Woken up at 2am, checks phone, sees "Audit Chain Breaks: 3"
- **Thoughts**: "This is bad. Someone tampered with logs."
- **Emotions**: 😱 Alarmed, 😠 Angry
- **Pain Points**: ❌ **No details in alert** (which records broken?)

**Improvements Needed**:
- Include details in alert (broken record IDs, timestamp)
- Add severity level (critical vs. warning)

---

#### 2. Investigation
- **Touchpoint**: Security Command Center → Audit Chain Verifier
- **Actions**:
  - Opens laptop, navigates to Security Command Center
  - Scrolls to Audit Chain Verifier section
  - Clicks "Verify Chain"
  - Sees 3 broken links highlighted
- **Thoughts**: "I need to find out who tampered with these records"
- **Emotions**: 🔍 Investigating, ⚡ Urgent
- **Pain Points**: ⚠️ **Broken records not explained** (why broken?)

**Improvements Needed**:
- Show why chain broke (hash mismatch, missing record, timestamp jump)
- Link to original records for comparison
- Show who had access to DB during tampering window

---

#### 3. Escalation
- **Touchpoint**: Security Command Center → Export
- **Actions**:
  - Exports security report with broken chain details
  - Emails CISO and incident response team
  - Calls on-call DBA to investigate DB access logs
- **Thoughts**: "This is a P0 incident. All hands on deck."
- **Emotions**: ⚡ Urgent, 😰 Stressed
- **Pain Points**: ❌ **Manual export** (should auto-escalate)

**Improvements Needed**:
- Add auto-escalation for critical security events
- Integrate with PagerDuty/Opsgenie
- Add runbook links for common incidents

---

#### 4. Resolution
- **Touchpoint**: Database → Audit Chain Verifier
- **Actions**:
  - DBA finds unauthorized access (compromised credentials)
  - Rotates credentials, restores backup
  - Re-verifies audit chain (now valid)
- **Thoughts**: "Crisis averted. Need to prevent this from happening again."
- **Emotions**: ✅ Relieved, 📝 Focused
- **Pain Points**: ⚠️ **No preventive alerts** (should have detected unusual DB access)

**Improvements Needed**:
- Add anomaly detection for DB access patterns
- Alert on unusual write patterns to audit table
- Add write-once, append-only DB config guidance

**Journey Duration**: 45 minutes (target: < 30 minutes)

---

### Journey 3: Running a Compliance Audit (Rajesh - Compliance Officer)

**Scenario**: Rajesh needs to generate a quarterly compliance report for RBI audit.

**Stages**:

#### 1. Preparation
- **Touchpoint**: Dashboard Overview
- **Actions**:
  - Logs into Sentinel
  - Reviews high-level metrics (total decisions, breakdown)
  - Notes date range (Q3 2026: July 1 - Sep 30)
- **Thoughts**: "I need complete audit trail for Q3"
- **Emotions**: 📋 Methodical, 🤔 Planning
- **Pain Points**: ⚠️ **No quarterly view** (only 24h/7d/30d)

**Improvements Needed**:
- Add custom date range selector
- Add preset ranges (Quarter, Year, Custom)

---

#### 2. Audit Trail Verification
- **Touchpoint**: Security Command Center
- **Actions**:
  - Navigates to Security Command Center
  - Verifies all security invariants = 0
  - Runs audit chain verification (PASS)
  - Screenshots results for report
- **Thoughts**: "Good, all security guarantees hold. Need evidence for auditor."
- **Emotions**: ✅ Satisfied, 📊 Confident
- **Pain Points**: ❌ **Manual screenshots** (should have "Export Evidence" button)

**Improvements Needed**:
- Add "Export Compliance Report" button
- Include all security invariants + audit chain verification
- Generate PDF with timestamp and cryptographic signature

---

#### 3. Data Export
- **Touchpoint**: Audit Ledger
- **Actions**:
  - Navigates to Audit Ledger
  - Sets date range to Q3 2026
  - Clicks "Export CSV"
  - Downloads 180,000 records
  - Opens in Excel to generate summary
- **Thoughts**: "Excel crashes with this many rows. Need a better way."
- **Emotions**: 😤 Frustrated, ⏱️ Impatient
- **Pain Points**: 
  - ❌ **CSV too large** (Excel can't handle)
  - ❌ **No summary report** (manual aggregation)
  - ⚠️ **Missing compliance fields** (regulator ID, transaction type)

**Improvements Needed**:
- Add "Summary Report" option (aggregated metrics, not raw data)
- Split large exports into multiple files
- Add compliance-specific fields to export
- Add direct export to Google Sheets / Airtable

---

#### 4. Report Generation
- **Touchpoint**: Excel / Word
- **Actions**:
  - Creates pivot tables in Excel
  - Generates summary metrics (total transactions, ALLOW/ESCALATE/CONTAIN %)
  - Copies into Word document
  - Adds narrative and screenshots
- **Thoughts**: "This is tedious. Should be automated."
- **Emotions**: 😓 Tired, ⏱️ Time-consuming
- **Pain Points**: ❌ **Manual report creation** (should have template)

**Improvements Needed**:
- Add "Compliance Report Template" (pre-built PDF)
- Include executive summary, metrics, security evidence
- Allow customization (logo, company name, date range)

---

#### 5. Submission
- **Touchpoint**: Email / Regulatory Portal
- **Actions**:
  - Emails report to internal audit team
  - Uploads to RBI regulatory portal
  - Files copy for internal records
- **Thoughts**: "Report submitted. Hope there are no questions."
- **Emotions**: ✅ Done, 😌 Relieved
- **Pain Points**: ⚠️ **No audit trail of report generation** (when generated, by whom)

**Improvements Needed**:
- Add report generation audit log
- Email report automatically to stakeholders
- Integrate with regulatory portals (future)

**Journey Duration**: 4 hours (target: < 1 hour)

---

### Journey 4: Onboarding a New AI Agent (Arjun - DevOps Engineer)

**Scenario**: Arjun needs to connect a new AI agent ("invoice-agent") to Sentinel for authorization.

**Stages**:

#### 1. Initial Setup
- **Touchpoint**: Settings Page → Agent Registry (placeholder)
- **Actions**:
  - Navigates to Settings (or Agent page if built)
  - Clicks "Add Agent"
  - Fills in agent details (name, description, capabilities)
  - Generates API key
- **Thoughts**: "Hope this works. Documentation is sparse."
- **Emotions**: 🤔 Uncertain, ⚠️ Cautious
- **Pain Points**: 
  - ❌ **Agent page placeholder** (feature not built)
  - ❌ **No guided setup** (unclear steps)
  - ⚠️ **Documentation missing** (no SDK examples)

**Improvements Needed**:
- Build Agent Registry page
- Add Setup Wizard (step-by-step guide)
- Provide SDK examples (Python, JavaScript, cURL)

---

#### 2. Integration
- **Touchpoint**: Agent Code → Sentinel API
- **Actions**:
  - Adds Sentinel SDK to agent code
  - Configures API endpoint and key
  - Sends test request
  - Receives error: "Invalid request format"
- **Thoughts**: "What's wrong with my request? Error message unhelpful."
- **Emotions**: 😤 Frustrated, ⏱️ Stuck
- **Pain Points**: 
  - ❌ **Cryptic error messages** (no guidance on fix)
  - ❌ **No test endpoint** (can't validate without real transaction)
  - ⚠️ **No request/response examples** in docs

**Improvements Needed**:
- Add test endpoint (`/api/test-authorization`)
- Improve error messages with fix suggestions
- Add request/response examples to docs

---

#### 3. First Authorization
- **Touchpoint**: Dashboard → Live Decisions
- **Actions**:
  - Sends real authorization request
  - Opens Sentinel dashboard
  - Navigates to Live Decisions
  - Sees new decision card appear
  - Checks decision: ESCALATE (first request = no baseline)
- **Thoughts**: "Why escalated? Agent is legitimate."
- **Emotions**: 🤔 Confused, ⚠️ Concerned
- **Pain Points**: 
  - ⚠️ **First request always escalates** (expected but not explained)
  - ❌ **No onboarding flow** (should explain baseline building)

**Improvements Needed**:
- Add banner on first request: "Building behavioral baseline (first 10 requests may escalate)"
- Show baseline progress (3/10 requests completed)
- Add tooltip explaining baseline requirement

---

#### 4. Baseline Training
- **Touchpoint**: Agent Registry (future)
- **Actions**:
  - Sends 10 normal requests
  - Waits for baseline to build
  - Checks agent status: "Baseline complete"
  - Sends 11th request → ALLOW
- **Thoughts**: "Good, baseline is working. Agent is live."
- **Emotions**: ✅ Satisfied, 😌 Relieved
- **Pain Points**: ⚠️ **No progress visibility** (unclear when baseline complete)

**Improvements Needed**:
- Show baseline training progress
- Send notification when baseline complete
- Add "Skip Baseline" option for trusted agents

---

#### 5. Monitoring
- **Touchpoint**: Dashboard Overview
- **Actions**:
  - Adds dashboard to daily routine
  - Monitors agent activity, latency, errors
  - Sets up alerts for anomalies
- **Thoughts**: "Nice, I can see everything in one place."
- **Emotions**: ✅ Confident, 📊 Informed
- **Pain Points**: ⚠️ **No agent-specific dashboard** (shows all agents mixed)

**Improvements Needed**:
- Add agent-specific dashboard
- Filter dashboard by agent ID
- Add agent comparison view (compare 2 agents side-by-side)

**Journey Duration**: 2 hours (target: < 30 minutes with wizard)

---

## Persona-to-Feature Mapping

| Feature | Priya (Security) | Arjun (DevOps) | Rajesh (Compliance) |
|---------|:----------------:|:--------------:|:-------------------:|
| Real-time Threat Detection | ⭐⭐⭐ | ⭐ | ⭐ |
| Incident Investigation | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Audit Chain Verification | ⭐⭐ | - | ⭐⭐⭐ |
| Behavioral Baselines | ⭐⭐⭐ | ⭐ | - |
| System Health Monitoring | ⭐ | ⭐⭐⭐ | - |
| Performance Metrics | ⭐ | ⭐⭐⭐ | - |
| Audit Trail Export | ⭐ | - | ⭐⭐⭐ |
| Compliance Reports | - | - | ⭐⭐⭐ |
| Agent Management | ⭐ | ⭐⭐⭐ | - |
| Policy Configuration | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| Containment Controls | ⭐⭐⭐ | - | ⭐ |
| Search & Filter | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

⭐⭐⭐ = Critical  
⭐⭐ = Important  
⭐ = Nice to have  
- = Not relevant  

---

## Next Steps

1. **Validate Personas** - Interview real users to confirm assumptions
2. **Prioritize Journeys** - Focus on high-frequency, high-pain journeys first
3. **Map Features to Journeys** - Build what users need most
4. **Design Solutions** - Create mockups for critical journey improvements
5. **Test & Iterate** - User testing to validate designs

---

**Document Owner**: Principal Product Designer  
**Last Updated**: 2026-08-29
