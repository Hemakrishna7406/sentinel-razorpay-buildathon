const AgentsPage={
  ch:[],
  render(){
    const agents=D.agents;
    const el=agents.filter(a=>a.risk>0.5).length;
    const tv=agents.reduce((s,a)=>s+a.violations,0);
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div class="stat-body"><div class="stat-val">${agents.length}</div><div class="stat-lbl">Total Active Agents</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></div><div class="stat-body"><div class="stat-val">${el}</div><div class="stat-lbl">Elevated Risk</div></div></div>
      <div class="stat-card"><div class="stat-icon rd"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div><div class="stat-body"><div class="stat-val">${tv}</div><div class="stat-lbl">Policy Violations</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-val">97.2%</div><div class="stat-lbl">Detection Accuracy</div></div></div>
    </div>
    <div class="g-23">
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Agent Risk Distribution</span></div>
          <div class="chart-wrap" style="height:250px"><canvas id="ch-agent-risk"></canvas></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Agent Monitoring</span><div style="display:flex;gap:8px"><select class="form-input form-select" style="height:30px;font-size:.65rem;padding:0 28px 0 8px"><option>All Agents</option><option>Healthy</option><option>Warning</option><option>Critical</option></select></div></div>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Agent ID</th><th>Transactions</th><th>Risk Score</th><th>Allow</th><th>Escalate</th><th>Contain</th><th>Violations</th><th>Status</th><th>Last Active</th></tr></thead><tbody>${agents.map(a=>{
            const lv=a.risk<0.15?'low':a.risk<0.5?'med':'high';
            const col=lv==='low'?'var(--green)':lv==='med'?'var(--amber)':'var(--red)';
            return `<tr><td class="tbl-mono">${a.id}</td><td>${a.txns.toLocaleString()}</td><td><div class="risk-bar"><div class="risk-track"><div class="risk-fill ${lv}" style="width:${Math.min(a.risk*100,100)}%"></div></div><span class="risk-num" style="color:${col}">${a.risk.toFixed(2)}</span></div></td><td>${a.allow.toLocaleString()}</td><td>${a.esc}</td><td>${a.con}</td><td>${a.violations>0?`<span style="color:var(--red);font-weight:600">${a.violations}</span>`:'0'}</td><td><span class="badge badge-${a.status==='healthy'?'healthy':a.status==='warning'?'warning':'critical'}">${a.status}</span></td><td style="font-size:.65rem;color:var(--text-tertiary)">${a.last}</td></tr>`;
          }).join('')}</tbody></table></div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Detection Accuracy</span></div>
          <div class="gauge"><div style="width:160px;height:88px;position:relative"><canvas id="ch-agent-acc"></canvas><div class="gauge-val"><div class="gauge-num" style="font-size:1.5rem">97.2%</div></div></div><div style="font-size:.6rem;color:var(--text-tertiary);margin-top:4px">Across all active agents</div></div>
          <div style="display:flex;justify-content:space-around;margin-top:16px;padding-top:14px;border-top:1px solid var(--border-light)"><div style="text-align:center"><div style="font-size:1rem;font-weight:700">28ms</div><div style="font-size:.6rem;color:var(--text-tertiary)">Avg Latency</div></div><div style="text-align:center"><div style="font-size:1rem;font-weight:700">327+</div><div style="font-size:.6rem;color:var(--text-tertiary)">RPS</div></div></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">AI Recommendations</span></div>
          <div class="alert-item"><div class="alert-dot red"></div><div class="alert-body"><div class="alert-title">Contain payment-agent-07</div><div class="alert-desc">12 violations, 0.78 avg risk. Behavioral drift exceeds threshold.</div></div></div>
          <div class="alert-item"><div class="alert-dot amber"></div><div class="alert-body"><div class="alert-title">Review trading-agent-03</div><div class="alert-desc">Recipient diversity dropped 40% — possible slow abuse pattern.</div></div></div>
          <div class="alert-item"><div class="alert-dot blue"></div><div class="alert-body"><div class="alert-title">Tighten arb-bot-12</div><div class="alert-desc">Consistent moderate risk. Adjust threshold to 0.12.</div></div></div>
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const agents=D.agents;
    this.ch.push(C.bar('ch-agent-risk',agents.map(a=>a.id.replace(/-agent-/,'-').replace(/-bot-/,'-')),[{label:'Risk',data:agents.map(a=>a.risk),backgroundColor:agents.map(a=>a.risk<0.15?C.colors.green+'80':a.risk<0.5?C.colors.amber+'80':C.colors.red+'80'),borderRadius:5,maxBarThickness:22}],{indexAxis:'y',scales:{x:{max:1,grid:{color:'rgba(0,0,0,.04)',drawBorder:false},ticks:{font:{family:'Inter',size:10},color:'#94A3B8'},border:{display:false}},y:{grid:{display:false},ticks:{font:{family:'Inter',size:9,weight:500},color:'#64748B'},border:{display:false}}}}));
    this.ch.push(C.gauge('ch-agent-acc',97.2,100,C.colors.green));
  }
};
