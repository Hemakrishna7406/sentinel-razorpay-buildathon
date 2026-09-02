const RiskIntelligencePage={
  ch:[],
  render(){
    const fe=D.fraudEvents;
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon rd"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></div><div class="stat-body"><div class="stat-val">${fe.length}</div><div class="stat-lbl">Fraud Events (7d)</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><div class="stat-body"><div class="stat-val">₹4.2Cr</div><div class="stat-lbl">Value Prevented</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div><div class="stat-body"><div class="stat-val">847%</div><div class="stat-lbl">ROI</div></div></div>
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg></div><div class="stat-body"><div class="stat-val">97.2%</div><div class="stat-lbl">Detection Rate</div></div></div>
    </div>
    <div class="g-23">
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Decision Trends (7d)</span><div style="display:flex;gap:6px"><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.green}"></span>ALLOW</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.amber}"></span>ESCALATE</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.red}"></span>CONTAIN</span></div></div>
          <div class="chart-wrap" style="height:220px"><canvas id="ch-risk-trends"></canvas></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Fraud Events</span><select class="form-input form-select" style="height:28px;font-size:.65rem;padding:0 28px 0 8px"><option>All Types</option><option>abuse_burst</option><option>amount_anomaly</option><option>slow_abuse</option><option>privilege_esc</option></select></div>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Intent ID</th><th>Agent</th><th>Amount</th><th>Risk</th><th>Type</th><th>Reason</th><th>Status</th></tr></thead><tbody>${fe.map(f=>`<tr><td class="tbl-mono">${f.intent}</td><td style="font-size:.65rem">${f.agent}</td><td>₹${(f.amount/100).toLocaleString()}</td><td><span style="color:var(--red);font-weight:600">${f.risk.toFixed(2)}</span></td><td><span class="badge badge-contain">${f.type}</span></td><td style="max-width:160px;overflow:hidden;text-overflow:ellipsis" title="${f.reason}">${f.reason}</td><td>${f.investigated?'<span class="badge badge-allow">✓ Done</span>':'<span class="badge badge-warning">Pending</span>'}</td></tr>`).join('')}</tbody></table></div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Financial Summary</span></div>
          <div style="display:flex;flex-direction:column;gap:14px">
            <div><div style="font-size:.65rem;color:var(--text-tertiary)">Total Value Processed</div><div style="font-size:1.125rem;font-weight:700">₹284Cr</div></div>
            <div class="divider" style="margin:0"></div>
            <div><div style="font-size:.65rem;color:var(--text-tertiary)">Total Transactions</div><div style="font-size:.875rem;font-weight:600">89,432</div></div>
            <div><div style="font-size:.65rem;color:var(--text-tertiary)">Fraud Prevented</div><div style="font-size:.875rem;font-weight:600;color:var(--red)">₹4.2Cr</div></div>
            <div><div style="font-size:.65rem;color:var(--text-tertiary)">Operational Cost</div><div style="font-size:.875rem;font-weight:600">₹1,25,000</div></div>
            <div class="divider" style="margin:0"></div>
            <div style="padding:12px;background:var(--green-bg);border-radius:var(--radius-md);text-align:center"><div style="font-size:.65rem;color:var(--text-tertiary)">Return on Investment</div><div style="font-size:1.5rem;font-weight:800;color:var(--green)">847%</div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Risk Distribution</span></div>
          <div class="chart-wrap" style="height:160px"><canvas id="ch-risk-dist2"></canvas></div>
          <div style="display:flex;justify-content:center;gap:12px;margin-top:8px"><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--green)"></span>Low</span><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--amber)"></span>Med</span><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--red)"></span>High</span></div>
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const t=D.authTimeline;
    this.ch.push(C.line('ch-risk-trends',t.labels,[C.lineDS('Allow',t.allow,C.colors.green),C.lineDS('Escalate',t.escalate,C.colors.amber),C.lineDS('Contain',t.contain,C.colors.red)]));
    this.ch.push(C.doughnut('ch-risk-dist2',['Low','Medium','High'],[72,20,8],[C.colors.green,C.colors.amber,C.colors.red]));
  }
};
