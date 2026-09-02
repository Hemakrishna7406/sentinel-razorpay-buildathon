const OverviewPage={
  ch:[],
  render(){
    const k=D.kpis, fmt=v=>v>=10000000?'₹'+(v/10000000).toFixed(1)+'Cr':v>=100000?'₹'+(v/100000).toFixed(1)+'L':'₹'+(v/100).toLocaleString();
    const arrow=v=>v>=0?`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>`;
    const infraIcons = {
      'API Service': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;color:var(--navy)"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>`,
      'Kafka': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;color:var(--navy)"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>`,
      'Redis': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;color:var(--red)"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
      'PostgreSQL': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;color:var(--blue)"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`
    };
    const infraPaths = {
      'API Service': 'M0 15 L10 10 L20 15 L30 5 L40 15 L50 12 L60 8',
      'Kafka': 'M0 12 L10 8 L20 12 L30 6 L40 16 L50 12 L60 8',
      'Redis': 'M0 14 L10 10 L20 14 L30 8 L40 16 L50 10 L60 10',
      'PostgreSQL': 'M0 16 L10 10 L20 15 L30 5 L40 15 L50 10 L60 8'
    };
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon nv"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div class="stat-body"><div class="stat-val">${k.totalRequests.toLocaleString()}</div><div class="stat-lbl">Total Requests</div><div class="stat-change up">${arrow(k.reqChange)} ${k.reqChange}% vs 24h ago</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg></div><div class="stat-body"><div class="stat-val">${(k.allowRate*100).toFixed(1)}%</div><div class="stat-lbl">Allow Rate</div><div class="stat-change up">${arrow(k.allowChange)} ${k.allowChange}% vs 24h ago</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="stat-body"><div class="stat-val">${(k.escalateRate*100).toFixed(1)}%</div><div class="stat-lbl">Escalate Rate</div><div class="stat-change up">${arrow(k.escChange)} ${k.escChange}% vs 24h ago</div></div></div>
      <div class="stat-card"><div class="stat-icon rd"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><div class="stat-body"><div class="stat-val">${(k.containRate*100).toFixed(1)}%</div><div class="stat-lbl">Contain Rate</div><div class="stat-change down">${arrow(k.conChange)} ${Math.abs(k.conChange)}% vs 24h ago</div></div></div>
    </div>
    <div class="g-23">
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Authorization Decisions Over Time</span><div style="display:flex;gap:12px;align-items:center"><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.green}"></span> ALLOW</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.amber}"></span> ESCALATE</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.red}"></span> CONTAIN</span><span class="card-pill active">24H</span></div></div>
          <div class="chart-wrap" style="height:220px"><canvas id="ch-auth-time"></canvas></div>
        </div>
        <div class="g-2 mb-0">
          <div class="card">
            <div class="card-head"><span class="card-t">Risk Distribution</span></div>
            <div style="display:flex;align-items:center;gap:24px">
              <div class="chart-wrap" style="width:160px;height:160px;position:relative;flex-shrink:0"><canvas id="ch-risk-dist"></canvas><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center"><div style="font-size:1.25rem;font-weight:800">${k.totalRequests.toLocaleString()}</div><div style="font-size:.6rem;color:var(--text-tertiary)">Total</div></div></div>
              <div style="display:flex;flex-direction:column;gap:10px;flex:1">
                <div style="display:flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:${C.colors.green};flex-shrink:0"></span><span style="font-size:.7rem;flex:1">Low (0 - 0.1)</span><strong style="font-size:.75rem">${D.riskDistribution.low}%</strong></div>
                <div style="display:flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:${C.colors.amber};flex-shrink:0"></span><span style="font-size:.7rem;flex:1">Medium (0.1 - 0.85)</span><strong style="font-size:.75rem">${D.riskDistribution.medium}%</strong></div>
                <div style="display:flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:${C.colors.red};flex-shrink:0"></span><span style="font-size:.7rem;flex:1">High (0.85+)</span><strong style="font-size:.75rem">${D.riskDistribution.high}%</strong></div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-head"><span class="card-t">System Notifications</span><span class="card-link">See All</span></div>
            ${D.notifications.map(n=>`<div class="alert-item"><div class="alert-dot ${n.dot}"></div><div class="alert-body"><div class="alert-title">${n.title}</div><div class="alert-desc">${n.desc}</div></div><div class="alert-time">${n.time}</div></div>`).join('')}
          </div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Core Authorization Health</span></div>
          <div class="gauge"><div style="width:180px;height:100px;position:relative"><canvas id="ch-health"></canvas><div class="gauge-val"><div class="gauge-num">${k.systemHealth}%</div></div></div><div style="color:var(--green);font-size:.75rem;font-weight:600;margin-top:4px">Healthy</div><div style="font-size:.6rem;color:var(--text-tertiary);margin-top:2px">System Integrity Score</div></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Quick Actions</span></div>
          <div class="qa-item" data-page="demo-scenarios"><div class="qa-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg></div><div class="qa-body"><div class="qa-title">Run Demo Scenario</div><div class="qa-desc">Simulate real-world attack scenarios</div></div><span class="qa-arrow">›</span></div>
          <div class="qa-item" data-page="policy-studio"><div class="qa-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><div class="qa-body"><div class="qa-title">Create Policy Rule</div><div class="qa-desc">Add natural language policy rule</div></div><span class="qa-arrow">›</span></div>
          <div class="qa-item" data-page="audit-ledger"><div class="qa-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="qa-body"><div class="qa-title">View Audit Ledger</div><div class="qa-desc">Explore immutable audit records</div></div><span class="qa-arrow">›</span></div>
          <div class="qa-item" data-page="demo-scenarios"><div class="qa-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div class="qa-body"><div class="qa-title">Run Simulation</div><div class="qa-desc">Test with synthetic data</div></div><span class="qa-arrow">›</span></div>
        </div>
      </div>
    </div>
    <div class="g-3">
      <div class="card">
        <div class="card-head"><span class="card-t">Infrastructure Health</span></div>
        ${D.infra.map(i=>`
          <div class="infra-item">
            <div class="infra-icon">${infraIcons[i.name] || ''}</div>
            <div style="flex:0 0 100px">
              <div class="infra-name">${i.name}</div>
              <div class="infra-sub">${i.sub}</div>
            </div>
            <div class="infra-chart">
              <svg width="60" height="20" viewBox="0 0 60 20" fill="none" style="display:block;width:100%;height:100%">
                <path d="${infraPaths[i.name]}" stroke="var(--green)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="30" cy="${infraPaths[i.name].split(' ')[7]}" r="1.5" fill="var(--green)"/>
              </svg>
            </div>
            <div class="infra-ms">${i.ms} ms</div>
          </div>
        `).join('')}
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Top Risky Agents</span><span class="card-link">See All</span></div>
        ${D.topRiskyAgents.map(a=>`<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width:16px;height:16px;flex-shrink:0;color:var(--text-tertiary)"><circle cx="12" cy="7" r="4"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/></svg><span style="flex:1;font-size:.7rem;font-weight:500">${a.id}</span><div class="risk-bar"><div class="risk-track"><div class="risk-fill ${a.level==='high'?'high':'med'}" style="width:${a.risk*100}%"></div></div><span class="risk-num" style="color:var(--${a.level==='high'?'red':'amber'})">${a.risk.toFixed(2)}</span></div><span class="badge badge-${a.level==='high'?'high':'medium'}">${a.level.charAt(0).toUpperCase()+a.level.slice(1)}</span></div>`).join('')}
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Recent Anomalies</span><span class="card-link">See All</span></div>
        ${D.anomalies.map(a=>`<div class="alert-item"><div class="alert-dot ${a.sev==='high'?'red':'amber'}"></div><div class="alert-body"><div class="alert-title">${a.type}</div><div class="alert-desc">${a.agent}</div></div><div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px"><div class="alert-time">${a.time}</div><span class="badge badge-${a.sev==='high'?'high':'medium'}">${a.sev.charAt(0).toUpperCase()+a.sev.slice(1)}</span></div></div>`).join('')}
      </div>
    </div>
    <div class="g-23 mb-0">
      <div class="card">
        <div class="card-head"><span class="card-t">Drill Down: Authorization Pipeline</span></div>
        <div class="pipeline">
          ${D.pipeline.map((p,i)=>`${i>0?'<span class="pipe-arrow">→</span>':''}<div class="pipe-stage ok"><div class="pipe-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:16px;height:16px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="pipe-name">${p.name}</div><div class="pipe-val">${typeof p.count==='number'?p.count.toLocaleString():p.count}</div></div>`).join('')}
        </div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">System Security Posture</span></div>
        <div style="display:flex;align-items:center;gap:20px">
          <div style="width:64px;height:64px;border-radius:var(--radius-lg);background:var(--green-bg);display:flex;align-items:center;justify-content:center;flex-shrink:0"><svg viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round" style="width:32px;height:32px"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div>
          <div style="flex:1">
            <div class="posture-check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span>All invariants maintained</span></div>
            <div class="posture-check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span>Zero tolerance active</span></div>
            <div class="posture-check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span>${D.securityTests} security tests passing</span></div>
            <div class="posture-check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span>Audit chain is valid</span></div>
          </div>
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const t=D.authTimeline;
    this.ch.push(C.line('ch-auth-time',t.labels,[C.areaDS('Allow',t.allow,C.colors.green),C.areaDS('Escalate',t.escalate,C.colors.amber),C.areaDS('Contain',t.contain,C.colors.red)]));
    this.ch.push(C.doughnut('ch-risk-dist',['Low','Medium','High'],[D.riskDistribution.low,D.riskDistribution.medium,D.riskDistribution.high],[C.colors.green,C.colors.amber,C.colors.red]));
    this.ch.push(C.gauge('ch-health',D.kpis.systemHealth,100,C.colors.green));
    document.querySelectorAll('.qa-item[data-page]').forEach(q=>q.addEventListener('click',()=>location.hash='#/'+q.dataset.page));
  }
};
