const D = {
  kpis: {
    totalRequests: 2847, allowRate: 0.732, escalateRate: 0.183, containRate: 0.085,
    reqChange: 12.3, allowChange: 5.2, escChange: 8.7, conChange: -3.4,
    systemHealth: 98.7, integrityScore: 'Healthy'
  },
  authTimeline: {
    labels: ['00:00','04:00','08:00','12:00','16:00','20:00','23:59'],
    allow: [95, 102, 145, 178, 162, 134, 98],
    escalate: [22, 18, 35, 48, 42, 31, 25],
    contain: [8, 12, 18, 25, 22, 17, 12]
  },
  riskDistribution: { low: 73.2, medium: 18.3, high: 8.5 },
  infra: [
    { name:'API Service', status:'healthy', ms:12, sub:'Operational' },
    { name:'Kafka', status:'healthy', ms:18, sub:'Operational' },
    { name:'Redis', status:'healthy', ms:1.2, sub:'Operational' },
    { name:'PostgreSQL', status:'healthy', ms:5, sub:'Operational' }
  ],
  topRiskyAgents: [
    { id:'agent-7a3f2b', risk:0.87, level:'high' },
    { id:'agent-9d4c1e', risk:0.79, level:'high' },
    { id:'agent-2e8b5f', risk:0.64, level:'medium' },
    { id:'agent-5c1a9d', risk:0.52, level:'medium' },
    { id:'agent-8f3e2a', risk:0.41, level:'medium' }
  ],
  anomalies: [
    { type:'Velocity Spike Detected', agent:'agent-7a3f2b', time:'2m ago', sev:'high' },
    { type:'Unusual Amount Pattern', agent:'agent-9d4c1e', time:'8m ago', sev:'high' },
    { type:'Location Anomaly', agent:'agent-2e8b5f', time:'15m ago', sev:'medium' },
    { type:'Time-of-Day Anomaly', agent:'agent-5c1a9d', time:'23m ago', sev:'medium' }
  ],
  notifications: [
    { title:'High Risk Transaction Contained', desc:'agent-7a3f2b attempted ₹12.5L payout', time:'4m ago', dot:'red' },
    { title:'Policy Rule Triggered', desc:'NL-002 matched on suspicious pattern', time:'11m ago', dot:'amber' },
    { title:'System Health Check Passed', desc:'All invariants maintained', time:'1h ago', dot:'green' }
  ],
  pipeline: [
    { name:'Intent Received', count:2847 },
    { name:'Idempotency Check', count:2847 },
    { name:'Behavioral Risk', count:'Analyzed' },
    { name:'Policy Decision', count:2847 },
    { name:'Capability Issued', count:2605 },
    { name:'Executed', count:2605 },
    { name:'Audit Logged', count:2847 }
  ],
  agents: [
    { id:'agent-7a3f2b', txns:156, val:42500000, risk:0.87, allow:98, esc:32, con:26, violations:8, status:'critical', last:'2m ago' },
    { id:'agent-9d4c1e', txns:203, val:38200000, risk:0.79, allow:142, esc:41, con:20, violations:6, status:'critical', last:'5m ago' },
    { id:'agent-2e8b5f', txns:178, val:31500000, risk:0.64, allow:145, esc:25, con:8, violations:3, status:'healthy', last:'12m ago' },
    { id:'agent-5c1a9d', txns:194, val:28700000, risk:0.52, allow:162, esc:24, con:8, violations:2, status:'healthy', last:'18m ago' },
    { id:'agent-8f3e2a', txns:142, val:22100000, risk:0.41, allow:125, esc:14, con:3, violations:1, status:'healthy', last:'25m ago' }
  ],
  policyRules: [
    { id:'NL-001', text:'ESCALATE IF amount > 5000000', status:'active', hits:87, created:'2025-04-01' },
    { id:'NL-002', text:'CONTAIN IF action_type = "payout" AND amount > 10000000', status:'active', hits:42, created:'2025-04-02' }
  ],
  auditRecords: [
    { id:'aud-001', intent:'int-7a3f2b-001', agent:'agent-7a3f2b', action:'payout', decision:'CONTAIN', risk:0.92, amount:1250000, reason:'Velocity spike detected', jti:'cap-7a3f2b-001', tx:'—', ts:'2026-09-05 14:23:45' },
    { id:'aud-002', intent:'int-9d4c1e-045', agent:'agent-9d4c1e', action:'payout', decision:'ESCALATE', risk:0.78, amount:780000, reason:'Amount threshold exceeded', jti:'cap-9d4c1e-045', tx:'tx-9d4c1e-045', ts:'2026-09-05 14:19:12' },
    { id:'aud-003', intent:'int-2e8b5f-102', agent:'agent-2e8b5f', action:'transfer', decision:'ALLOW', risk:0.12, amount:45000, reason:'Normal behavioral pattern', jti:'cap-2e8b5f-102', tx:'tx-2e8b5f-102', ts:'2026-09-05 14:12:34' },
    { id:'aud-004', intent:'int-5c1a9d-234', agent:'agent-5c1a9d', action:'transfer', decision:'ALLOW', risk:0.08, amount:32000, reason:'Low risk transaction', jti:'cap-5c1a9d-234', tx:'tx-5c1a9d-234', ts:'2026-09-05 14:27:01' },
    { id:'aud-005', intent:'int-8f3e2a-167', agent:'agent-8f3e2a', action:'payout', decision:'ALLOW', risk:0.15, amount:58000, reason:'Within policy limits', jti:'cap-8f3e2a-167', tx:'tx-8f3e2a-167', ts:'2026-09-05 14:26:18' }
  ],
  invariants: { unauthorized_executions:0, duplicate_executions:0, unsafe_allows:0, audit_chain_breaks:0, fail_open_incidents:0 },
  securityTests: 12,
  fraudEvents: [
    { id:'frd-001', intent:'int-7a3f2b-001', agent:'agent-7a3f2b', amount:1250000, risk:0.92, type:'Velocity Attack', reason:'Rapid-fire payout requests detected', investigated:false },
    { id:'frd-002', intent:'int-9d4c1e-045', agent:'agent-9d4c1e', amount:780000, risk:0.78, type:'Amount Escalation', reason:'Progressive amount increase pattern', investigated:true }
  ],
  liveFeed: [
    { intent:'int-5c1a9d-234', agent:'agent-5c1a9d', action:'transfer', decision:'ALLOW', risk:0.08, amount:32000, detail:'₹320 transfer', time:'just now' },
    { intent:'int-8f3e2a-167', agent:'agent-8f3e2a', action:'payout', decision:'ALLOW', risk:0.15, amount:58000, detail:'₹580 payout', time:'1m ago' },
    { intent:'int-7a3f2b-001', agent:'agent-7a3f2b', action:'payout', decision:'CONTAIN', risk:0.92, amount:1250000, detail:'₹12,500 payout - velocity spike', time:'4m ago' },
    { intent:'int-9d4c1e-045', agent:'agent-9d4c1e', action:'payout', decision:'ESCALATE', risk:0.78, amount:780000, detail:'₹7,800 payout - amount threshold', time:'8m ago' },
    { intent:'int-2e8b5f-102', agent:'agent-2e8b5f', action:'transfer', decision:'ALLOW', risk:0.12, amount:45000, detail:'₹450 transfer', time:'15m ago' }
  ],
  observability: {
    reqRate: {
      labels: ['00:00','04:00','08:00','12:00','16:00','20:00','23:59'],
      vals: [125, 132, 198, 251, 226, 182, 135]
    },
    errorRate: {
      labels: ['00:00','04:00','08:00','12:00','16:00','20:00','23:59'],
      vals: [0.2, 0.1, 0.3, 0.5, 0.4, 0.2, 0.1]
    },
    latencyP50: [12, 15, 14, 18, 16, 13, 12],
    latencyP95: [45, 52, 48, 58, 54, 47, 44],
    latencyP99: [95, 108, 102, 125, 118, 98, 92],
    latencyLabels: ['00:00','04:00','08:00','12:00','16:00','20:00','23:59']
  },
  scenarios: [
    { name:'Velocity Burst Attack', desc:'Simulate rapid-fire payout requests from a single agent to test velocity detection.', type:'Attack', samples:50, difficulty:'Hard' },
    { name:'Amount Escalation', desc:'Progressive amount increases to test threshold detection.', type:'Attack', samples:20, difficulty:'Medium' }
  ],
  
  async init() {
    try {
      const res = await fetch('/api/analytics/dashboard/executive');
      if (!res.ok) return;
      const data = await res.json();
      
      this.kpis = {
        totalRequests: data.kpis.total_transactions_24h,
        allowRate: data.kpis.allow_rate,
        escalateRate: data.kpis.escalate_rate,
        containRate: data.kpis.contain_rate,
        reqChange: 0, allowChange: 0, escChange: 0, conChange: 0,
        systemHealth: data.kpis.system_uptime * 100,
        integrityScore: 'Healthy'
      };
      
      this.authTimeline = { labels: [], allow: [], escalate: [], contain: [] };
      data.trends.forEach(t => {
        const d = new Date(t.timestamp);
        this.authTimeline.labels.push(`${d.getHours()}:00`);
        this.authTimeline.allow.push(t.allow_count);
        this.authTimeline.escalate.push(t.escalate_count);
        this.authTimeline.contain.push(t.contain_count);
      });
      
      this.topRiskyAgents = data.top_agents.map(a => ({
        id: a.agent_id, risk: a.avg_risk_score || 0, level: (a.avg_risk_score||0)>0.8?'high':(a.avg_risk_score||0)>0.3?'medium':'low'
      }));
      
      this.agents = data.top_agents.map(a => ({
        id: a.agent_id, txns: a.total_transactions, val: a.total_value, risk: a.avg_risk_score || 0,
        allow: a.allow_count, esc: a.escalate_count, con: a.contain_count, violations: a.policy_violations,
        status: (a.avg_risk_score||0)>0.8?'critical':'healthy', last: a.last_transaction || 'recent'
      }));
      
      this.fraudEvents = data.recent_fraud.map(f => ({
        id: f.id, intent: f.intent_id, agent: f.agent_id, amount: f.amount, risk: f.risk_score,
        type: f.fraud_type, reason: f.decision_reason, investigated: f.investigated
      }));
      
      this.pipeline = [
        { name:'Intent Received', count: data.kpis.total_transactions_24h },
        { name:'Idempotency Check', count: data.kpis.total_transactions_24h },
        { name:'Behavioral Risk', count:'Analyzed' },
        { name:'Policy Decision', count: data.kpis.total_transactions_24h },
        { name:'Capability Issued', count: data.kpis.total_transactions_24h - data.kpis.contain_rate * data.kpis.total_transactions_24h },
        { name:'Executed', count: data.kpis.total_transactions_24h - data.kpis.contain_rate * data.kpis.total_transactions_24h },
        { name:'Audit Logged', count: data.kpis.total_transactions_24h }
      ];
      
    } catch (e) {
      console.error("Failed to load analytics data", e);
    }
  }
};
