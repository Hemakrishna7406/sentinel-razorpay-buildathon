const D = {
  kpis: {
    totalRequests: 0, allowRate: 0, escalateRate: 0, containRate: 0,
    reqChange: 0, allowChange: 0, escChange: 0, conChange: 0,
    systemHealth: 100, integrityScore: 'Healthy'
  },
  authTimeline: { labels: [], allow: [], escalate: [], contain: [] },
  riskDistribution: { low: 0, medium: 0, high: 0 },
  infra: [
    { name:'API Service', status:'healthy', ms:12, sub:'Operational' },
    { name:'Kafka', status:'healthy', ms:18, sub:'Operational' },
    { name:'Redis', status:'healthy', ms:1.2, sub:'Operational' },
    { name:'PostgreSQL', status:'healthy', ms:5, sub:'Operational' }
  ],
  topRiskyAgents: [],
  anomalies: [],
  notifications: [],
  pipeline: [
    { name:'Intent Received', count:0 },
    { name:'Idempotency Check', count:0 },
    { name:'Behavioral Risk', count:'Analyzed' },
    { name:'Policy Decision', count:0 },
    { name:'Capability Issued', count:0 },
    { name:'Executed', count:0 },
    { name:'Audit Logged', count:0 }
  ],
  agents: [],
  policyRules: [
    { id:'NL-001', text:'ESCALATE IF amount > 5000000', status:'active', hits:0, created:'2025-04-01' },
    { id:'NL-002', text:'CONTAIN IF action_type = "payout" AND amount > 10000000', status:'active', hits:0, created:'2025-04-02' }
  ],
  auditRecords: [],
  invariants: { unauthorized_executions:0, duplicate_executions:0, unsafe_allows:0, audit_chain_breaks:0, fail_open_incidents:0 },
  securityTests: 12,
  fraudEvents: [],
  liveFeed: [],
  observability: {
    reqRate: { labels:[], vals:[] },
    errorRate: { labels:[], vals:[] },
    latencyP50: [],
    latencyP95: [],
    latencyP99: [],
    latencyLabels: []
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
