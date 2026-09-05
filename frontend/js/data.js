const D = {
  kpis: {
    totalRequests: 2847,
    allowRate: 0.732,
    escalateRate: 0.183,
    containRate: 0.085,
    reqChange: 12.4,
    allowChange: 3.2,
    escChange: -1.8,
    conChange: -2.1,
    systemHealth: 98.7,
    integrityScore: 'Healthy'
  },
  authTimeline: {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '23:00'],
    allow: [320, 410, 580, 620, 490, 410, 255],
    escalate: [85, 102, 118, 135, 98, 72, 52],
    contain: [42, 38, 52, 68, 45, 35, 22]
  },
  riskDistribution: { low: 68, medium: 24, high: 8 },
  infra: [
    { name:'API Service', status:'healthy', ms:12, sub:'Operational' },
    { name:'Kafka', status:'healthy', ms:18, sub:'Operational' },
    { name:'Redis', status:'healthy', ms:1.2, sub:'Operational' },
    { name:'PostgreSQL', status:'healthy', ms:5, sub:'Operational' }
  ],
  topRiskyAgents: [
    { id:'agent-gpt4-prod-003', risk:0.89, level:'high' },
    { id:'agent-claude-staging-002', risk:0.76, level:'medium' },
    { id:'agent-gemini-dev-007', risk:0.68, level:'medium' },
    { id:'agent-llama-prod-001', risk:0.45, level:'medium' },
    { id:'agent-mistral-staging-004', risk:0.32, level:'low' }
  ],
  anomalies: [
    { type:'Velocity Spike Detected', agent:'agent-gpt4-prod-003', sev:'high', time:'2m ago' },
    { type:'Unusual Amount Pattern', agent:'agent-claude-staging-002', sev:'medium', time:'18m ago' },
    { type:'New Merchant Target', agent:'agent-gemini-dev-007', sev:'medium', time:'1h ago' }
  ],
  notifications: [
    { title:'High-risk agent contained', desc:'agent-gpt4-prod-003 exceeded velocity limit', time:'2m ago', dot:'red' },
    { title:'Policy rule triggered 127 times', desc:'NL-001: Amount > 5M escalation active', time:'24m ago', dot:'amber' },
    { title:'System health optimal', desc:'All security invariants passing', time:'1h ago', dot:'green' }
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
    { id:'agent-gpt4-prod-003', txns:487, val:12000000, risk:0.89, allow:298, esc:124, con:65, violations:3, status:'critical', last:'2m ago' },
    { id:'agent-claude-staging-002', txns:623, val:28000000, risk:0.76, allow:502, esc:98, con:23, violations:1, status:'healthy', last:'18m ago' },
    { id:'agent-gemini-dev-007', txns:412, val:9800000, risk:0.68, allow:325, esc:72, con:15, violations:0, status:'healthy', last:'1h ago' },
    { id:'agent-llama-prod-001', txns:891, val:45000000, risk:0.45, allow:782, esc:94, con:15, violations:0, status:'healthy', last:'3h ago' },
    { id:'agent-mistral-staging-004', txns:434, val:11000000, risk:0.32, allow:398, esc:32, con:4, violations:0, status:'healthy', last:'4h ago' }
  ],
  policyRules: [
    { id:'NL-001', text:'ESCALATE IF amount > 5000000', status:'active', hits:87, created:'2025-04-01' },
    { id:'NL-002', text:'CONTAIN IF action_type = "payout" AND amount > 10000000', status:'active', hits:42, created:'2025-04-02' }
  ],
  auditRecords: [
    { id:'AUD-2847', intent:'INT-5523', agent:'agent-gpt4-prod-003', decision:'CONTAIN', risk:0.92, amount:'₹85,00,000', reason:'Velocity limit exceeded', ts:'2m ago', sig:'0x7a2f...8e1c' },
    { id:'AUD-2846', intent:'INT-5522', agent:'agent-claude-staging-002', decision:'ESCALATE', risk:0.78, amount:'₹62,50,000', reason:'Amount threshold breach', ts:'18m ago', sig:'0x4b9d...2a7f' },
    { id:'AUD-2845', intent:'INT-5521', agent:'agent-gemini-dev-007', decision:'ALLOW', risk:0.23, amount:'₹12,00,000', reason:'Within policy limits', ts:'1h ago', sig:'0x9c3e...5d2b' },
    { id:'AUD-2844', intent:'INT-5520', agent:'agent-llama-prod-001', decision:'ALLOW', risk:0.18, amount:'₹8,50,000', reason:'Trusted merchant', ts:'3h ago', sig:'0x1f7a...8c4e' },
    { id:'AUD-2843', intent:'INT-5519', agent:'agent-mistral-staging-004', decision:'ALLOW', risk:0.15, amount:'₹5,20,000', reason:'Normal pattern', ts:'4h ago', sig:'0x6d2b...3f9a' }
  ],
  invariants: { unauthorized_executions:0, duplicate_executions:0, unsafe_allows:0, audit_chain_breaks:0, fail_open_incidents:0 },
  securityTests: 12,
  fraudEvents: [
    { id:'FRD-089', intent:'INT-5523', agent:'agent-gpt4-prod-003', amount:'₹85,00,000', risk:0.92, type:'Velocity Attack', reason:'47 requests in 90 seconds', investigated:false },
    { id:'FRD-088', intent:'INT-5490', agent:'agent-claude-staging-002', amount:'₹1,05,00,000', risk:0.85, type:'Amount Escalation', reason:'Progressive increase pattern', investigated:true }
  ],
  liveFeed: [
    { id:'INT-5523', agent:'agent-gpt4-prod-003', action:'payout', amount:'₹85,00,000', decision:'CONTAIN', risk:0.92, time:'2m ago' },
    { id:'INT-5522', agent:'agent-claude-staging-002', action:'payout', amount:'₹62,50,000', decision:'ESCALATE', risk:0.78, time:'18m ago' },
    { id:'INT-5521', agent:'agent-gemini-dev-007', action:'transfer', amount:'₹12,00,000', decision:'ALLOW', risk:0.23, time:'1h ago' },
    { id:'INT-5520', agent:'agent-llama-prod-001', action:'payout', amount:'₹8,50,000', decision:'ALLOW', risk:0.18, time:'3h ago' },
    { id:'INT-5519', agent:'agent-mistral-staging-004', action:'transfer', amount:'₹5,20,000', decision:'ALLOW', risk:0.15, time:'4h ago' }
  ],
  observability: {
    reqRate: { labels:['00:00','04:00','08:00','12:00','16:00','20:00','23:00'], vals:[850,980,1250,1450,1180,920,720] },
    errorRate: { labels:['00:00','04:00','08:00','12:00','16:00','20:00','23:00'], vals:[0.2,0.1,0.3,0.5,0.2,0.1,0.1] },
    latencyP50: [12,14,18,22,16,13,11],
    latencyP95: [45,52,68,82,58,48,42],
    latencyP99: [125,142,185,220,165,138,118],
    latencyLabels: ['00:00','04:00','08:00','12:00','16:00','20:00','23:00']
  },
  scenarios: [
    { name:'Velocity Burst Attack', desc:'Simulate rapid-fire payout requests from a single agent to test velocity detection.', type:'Attack', samples:50, difficulty:'Hard' },
    { name:'Amount Escalation', desc:'Progressive amount increases to test threshold detection.', type:'Attack', samples:20, difficulty:'Medium' }
  ],

  async init() {
    try {
      const res = await fetch('/api/analytics/dashboard/executive');
      if (!res.ok) throw new Error('Backend not available, using demo data');
      const data = await res.json();

      this.kpis = {
        totalRequests: data.kpis.total_transactions_24h,
        allowRate: data.kpis.allow_rate,
        escalateRate: data.kpis.escalate_rate,
        containRate: data.kpis.contain_rate,
        reqChange: 12.4, allowChange: 3.2, escChange: -1.8, conChange: -2.1,
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
        { name:'Capability Issued', count: Math.round(data.kpis.total_transactions_24h * (1 - data.kpis.contain_rate)) },
        { name:'Executed', count: Math.round(data.kpis.total_transactions_24h * (1 - data.kpis.contain_rate)) },
        { name:'Audit Logged', count: data.kpis.total_transactions_24h }
      ];

      console.log('✅ Loaded live data from backend');
    } catch (e) {
      console.log('📊 Using demo data (backend not available)');
    }
  }
};
