const D = {
  kpis: {
    totalRequests: 24812, allowRate: .723, escalateRate: .241, containRate: .036,
    reqChange: 12.6, allowChange: 5.4, escChange: 2.1, conChange: -0.8,
    systemHealth: 93, integrityScore: 'Healthy'
  },
  authTimeline: {
    labels: ['00:00','02:00','04:00','06:00','08:00','10:00','12:00','14:00','16:00','18:00','20:00','22:00'],
    allow: [320,280,210,180,350,620,980,1200,1350,1100,870,520],
    escalate: [80,65,45,38,95,180,290,350,380,310,240,145],
    contain: [12,10,8,5,18,32,48,55,60,50,38,22]
  },
  riskDistribution: { low: 45.2, medium: 44.1, high: 10.7 },
  infra: [
    { name:'API Service', status:'healthy', ms:23, sub:'Operational' },
    { name:'Kafka', status:'healthy', ms:42, sub:'Operational' },
    { name:'Redis', status:'healthy', ms:1.2, sub:'Operational' },
    { name:'PostgreSQL', status:'healthy', ms:18, sub:'Operational' }
  ],
  topRiskyAgents: [
    { id:'payment-agent-07', risk:0.78, level:'high' },
    { id:'trading-agent-03', risk:0.67, level:'high' },
    { id:'arb-bot-12', risk:0.61, level:'medium' },
    { id:'payout-agent-02', risk:0.59, level:'medium' },
    { id:'collector-agent-09', risk:0.53, level:'medium' }
  ],
  anomalies: [
    { type:'Velocity Spike', agent:'payment-agent-07', time:'14:42:10', sev:'high' },
    { type:'Amount Deviation', agent:'trading-agent-03', time:'14:41:55', sev:'medium' },
    { type:'Pattern Break', agent:'arb-bot-12', time:'14:41:32', sev:'high' },
    { type:'New Recipient', agent:'payout-agent-02', time:'14:41:01', sev:'medium' }
  ],
  notifications: [
    { title:'Unusual Velocity Pattern Detected', desc:'Multiple high-value transfers from agent-07', time:'14:42', dot:'red' },
    { title:'New Policy Rule Added', desc:'ESCALATE IF amount > 15,00,000', time:'14:38', dot:'blue' },
    { title:'Audit Chain Verified', desc:'No tampering detected in audit ledger', time:'14:22', dot:'green' }
  ],
  pipeline: [
    { name:'Intent Received', count:24812 },
    { name:'Idempotency Check', count:24812 },
    { name:'Behavioral Risk', count:'Analyzed' },
    { name:'Policy Decision', count:24812 },
    { name:'Capability Issued', count:17892 },
    { name:'Executed', count:15234 },
    { name:'Audit Logged', count:24812 }
  ],
  agents: [
    { id:'payment-agent-07', txns:4280, val:15200000, risk:0.78, allow:2800, esc:1100, con:380, violations:12, status:'critical', last:'1 min ago' },
    { id:'trading-agent-03', txns:3850, val:12800000, risk:0.67, allow:2900, esc:750, con:200, violations:7, status:'warning', last:'2 mins ago' },
    { id:'checkout-agent-01', txns:5200, val:18400000, risk:0.05, allow:5100, esc:85, con:15, violations:0, status:'healthy', last:'30s ago' },
    { id:'arb-bot-12', txns:2100, val:8900000, risk:0.61, allow:1400, esc:520, con:180, violations:5, status:'warning', last:'3 mins ago' },
    { id:'payout-agent-02', txns:3100, val:9800000, risk:0.59, allow:2200, esc:700, con:200, violations:4, status:'warning', last:'5 mins ago' },
    { id:'refund-agent-04', txns:1560, val:4200000, risk:0.12, allow:1420, esc:120, con:20, violations:1, status:'healthy', last:'8 mins ago' },
    { id:'collector-agent-09', txns:980, val:3100000, risk:0.53, allow:600, esc:300, con:80, violations:3, status:'warning', last:'12 mins ago' },
    { id:'retry-agent-06', txns:720, val:2800000, risk:0.18, allow:610, esc:90, con:20, violations:1, status:'healthy', last:'15 mins ago' }
  ],
  policyRules: [
    { id:'NL-001', text:'ESCALATE IF amount > 5000000', status:'active', hits:156, created:'2025-04-01' },
    { id:'NL-002', text:'CONTAIN IF action_type = "payout" AND amount > 10000000', status:'active', hits:23, created:'2025-04-02' },
    { id:'NL-003', text:'ESCALATE IF model_risk > 0.8', status:'active', hits:89, created:'2025-03-15' },
    { id:'NL-004', text:'ESCALATE IF currency != "INR"', status:'active', hits:12, created:'2025-04-05' },
    { id:'NL-005', text:'CONTAIN IF recipient = "unknown" AND amount > 1000000', status:'active', hits:7, created:'2025-04-06' },
    { id:'NL-006', text:'ESCALATE IF action_type = "retry" AND amount > 2000000', status:'disabled', hits:0, created:'2025-04-07' }
  ],
  auditRecords: [
    { id:1042, intent:'INT-a3f2c1', agent:'checkout-agent-01', action:'checkout', amount:250000, risk:0.03, decision:'ALLOW', reason:'Low risk — within baseline', jti:'jti_8a2f3c', tx:'tx_RZP_001', ts:'2025-04-08 14:32:01' },
    { id:1041, intent:'INT-b7e4d9', agent:'payment-agent-07', action:'payout', amount:8500000, risk:0.91, decision:'CONTAIN', reason:'Severe behavioral anomaly', jti:null, tx:null, ts:'2025-04-08 14:31:45' },
    { id:1040, intent:'INT-c1d5a8', agent:'trading-agent-03', action:'payout', amount:5200000, risk:0.62, decision:'ESCALATE', reason:'Amount exceeds NL threshold', jti:null, tx:null, ts:'2025-04-08 14:31:12' },
    { id:1039, intent:'INT-d9f2b3', agent:'checkout-agent-01', action:'checkout', amount:180000, risk:0.06, decision:'ALLOW', reason:'Low risk — within baseline', jti:'jti_7c3e1d', tx:'tx_RZP_002', ts:'2025-04-08 14:30:58' },
    { id:1038, intent:'INT-e4a1c7', agent:'refund-agent-04', action:'refund', amount:45000, risk:0.11, decision:'ALLOW', reason:'Refund within limits', jti:'jti_2d5f8a', tx:'tx_RZP_003', ts:'2025-04-08 14:30:22' },
    { id:1037, intent:'INT-f8b3d2', agent:'retry-agent-06', action:'retry', amount:3200000, risk:0.35, decision:'ESCALATE', reason:'Retry amount exceeds threshold', jti:null, tx:null, ts:'2025-04-08 14:29:45' },
    { id:1036, intent:'INT-a2c4e6', agent:'checkout-agent-01', action:'checkout', amount:89000, risk:0.02, decision:'ALLOW', reason:'Low risk — within baseline', jti:'jti_4f7a2b', tx:'tx_RZP_004', ts:'2025-04-08 14:29:10' },
    { id:1035, intent:'INT-b5d7f9', agent:'payment-agent-07', action:'payout', amount:7200000, risk:0.88, decision:'CONTAIN', reason:'Amount 4σ above mean', jti:null, tx:null, ts:'2025-04-08 14:28:33' }
  ],
  invariants: { unauthorized_executions:0, duplicate_executions:0, unsafe_allows:0, audit_chain_breaks:0, fail_open_incidents:0 },
  securityTests: 241,
  fraudEvents: [
    { id:1, intent:'INT-b7e4d9', agent:'payment-agent-07', amount:8500000, risk:0.91, type:'abuse_burst', reason:'Velocity x31 + new recipient', investigated:false },
    { id:2, intent:'INT-b5d7f9', agent:'payment-agent-07', amount:7200000, risk:0.88, type:'amount_anomaly', reason:'Amount 4σ above baseline', investigated:false },
    { id:3, intent:'INT-x8c2a1', agent:'trading-agent-03', amount:12000000, risk:0.95, type:'slow_abuse', reason:'Gradual recipient rotation', investigated:true },
    { id:4, intent:'INT-y3d4b2', agent:'retry-agent-06', amount:4800000, risk:0.72, type:'privilege_esc', reason:'Action type mismatch', investigated:true },
    { id:5, intent:'INT-z1e5c3', agent:'payment-agent-07', amount:9100000, risk:0.93, type:'abuse_burst', reason:'Off-hours high velocity', investigated:true }
  ],
  liveFeed: [
    { agent:'checkout-agent-01', action:'checkout', amount:89000, risk:0.02, decision:'ALLOW', time:'14:32:01', detail:'merch_myntra → ₹890' },
    { agent:'payment-agent-07', action:'payout', amount:8500000, risk:0.91, decision:'CONTAIN', time:'14:31:45', detail:'vendor_new_99 → ₹85,000' },
    { agent:'trading-agent-03', action:'payout', amount:5200000, risk:0.62, decision:'ESCALATE', time:'14:31:12', detail:'vendor_amz_12 → ₹52,000' },
    { agent:'checkout-agent-01', action:'checkout', amount:180000, risk:0.06, decision:'ALLOW', time:'14:30:58', detail:'merch_amazon → ₹1,800' },
    { agent:'refund-agent-04', action:'refund', amount:45000, risk:0.11, decision:'ALLOW', time:'14:30:22', detail:'cust_9281 → ₹450' },
    { agent:'retry-agent-06', action:'retry', amount:3200000, risk:0.35, decision:'ESCALATE', time:'14:29:45', detail:'vendor_swiggy → ₹32,000' },
    { agent:'arb-bot-12', action:'payout', amount:6100000, risk:0.61, decision:'ESCALATE', time:'14:29:10', detail:'vendor_arb_44 → ₹61,000' },
    { agent:'collector-agent-09', action:'checkout', amount:2800000, risk:0.53, decision:'ESCALATE', time:'14:28:33', detail:'merch_collect_12 → ₹28,000' }
  ],
  observability: {
    reqRate: { labels:['00','04','08','12','16','20'], vals:[120,80,350,980,1200,520] },
    errorRate: { labels:['00','04','08','12','16','20'], vals:[0.1,0.05,0.2,0.15,0.3,0.1] },
    latencyP50: [12,14,11,13,15,10,11],
    latencyP95: [24,26,22,25,28,20,21],
    latencyP99: [28,32,26,30,35,24,25],
    latencyLabels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
  },
  scenarios: [
    { name:'Velocity Burst Attack', desc:'Simulate 50 rapid-fire payout requests from a single agent to test velocity detection and auto-escalation.', type:'Attack', samples:50, difficulty:'Hard' },
    { name:'Gradual Recipient Rotation', desc:'Slowly shift payout recipients over 200 transactions to test behavioral drift detection.', type:'Evasion', samples:200, difficulty:'Expert' },
    { name:'Normal Operations', desc:'Baseline simulation with 500 standard checkout and refund operations to verify allow rate.', type:'Baseline', samples:500, difficulty:'Easy' },
    { name:'Amount Escalation', desc:'Progressive amount increases from ₹1,000 to ₹1Cr to test threshold and anomaly detection.', type:'Attack', samples:100, difficulty:'Medium' },
    { name:'New Agent Onboarding', desc:'Simulate a previously unseen agent making its first 25 transactions with increasing amounts.', type:'Edge Case', samples:25, difficulty:'Medium' },
    { name:'Multi-Agent Coordination', desc:'Coordinated attack across 5 agents with complementary patterns to test cross-agent detection.', type:'Attack', samples:150, difficulty:'Expert' }
  ]
};
