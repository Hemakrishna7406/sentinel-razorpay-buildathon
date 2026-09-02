const LiveAuthPage={
  ch:[],
  intv:null,
  render(){
    const feed=D.liveFeed;
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div class="stat-body"><div class="stat-val">327</div><div class="stat-lbl">Requests / Second</div></div></div>
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="stat-body"><div class="stat-val">28ms</div><div class="stat-lbl">Avg Latency</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg></div><div class="stat-body"><div class="stat-val">24.1%</div><div class="stat-lbl">Escalation Rate</div></div></div>
      <div class="stat-card"><div class="stat-icon rd"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><div class="stat-body"><div class="stat-val">3.6%</div><div class="stat-lbl">Contain Rate</div></div></div>
    </div>
    <div class="g-23">
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Live Throughput</span><div style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.5s infinite"></span><span style="font-size:.65rem;color:var(--green);font-weight:600">LIVE</span></div></div>
          <div class="chart-wrap" style="height:200px"><canvas id="ch-live-throughput"></canvas></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Authorization Feed</span><span style="font-size:.65rem;color:var(--text-tertiary)">${feed.length} recent decisions</span></div>
          <div class="card-scroll">
            ${feed.map(f=>{
              const cls=f.decision==='ALLOW'?'allow':f.decision==='ESCALATE'?'escalate':'contain';
              return `<div class="feed-item"><div class="feed-icon ${cls}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">${f.decision==='ALLOW'?'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>':f.decision==='ESCALATE'?'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/>':'<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'}</svg></div><div class="feed-body"><div class="feed-head"><span class="feed-agent">${f.agent}</span><span class="feed-time">${f.time}</span></div><div class="feed-detail">${f.action} · ${f.detail}</div><div class="feed-tags"><span class="badge badge-${cls}">${f.decision}</span><span class="badge badge-neutral">Risk: ${f.risk.toFixed(2)}</span></div></div></div>`;
            }).join('')}
          </div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Decision Breakdown</span></div>
          <div class="chart-wrap" style="height:180px;display:flex;align-items:center;justify-content:center"><div style="position:relative;width:160px;height:160px"><canvas id="ch-live-donut"></canvas><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center"><div style="font-size:1.25rem;font-weight:800">327</div><div style="font-size:.6rem;color:var(--text-tertiary)">RPS</div></div></div></div>
          <div style="display:flex;justify-content:center;gap:16px;margin-top:8px"><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--green)"></span>Allow</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--amber)"></span>Escalate</span><span style="display:flex;align-items:center;gap:4px;font-size:.65rem"><span style="width:8px;height:8px;border-radius:50%;background:var(--red)"></span>Contain</span></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Active Agents</span></div>
          ${D.agents.slice(0,5).map(a=>`<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--border-light)"><div style="width:8px;height:8px;border-radius:50%;background:var(--${a.status==='healthy'?'green':a.status==='warning'?'amber':'red'})"></div><span style="flex:1;font-size:.7rem;font-weight:500">${a.id}</span><span class="badge badge-${a.status==='healthy'?'healthy':a.status==='warning'?'warning':'critical'}">${a.status}</span></div>`).join('')}
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const labels=['30s','25s','20s','15s','10s','5s','Now'];
    const data=[280,310,295,340,330,315,327];
    this.ch.push(C.line('ch-live-throughput',labels,[C.areaDS('RPS',data,C.colors.blue)],{scales:{y:{min:200}}}));
    this.ch.push(C.doughnut('ch-live-donut',['Allow','Escalate','Contain'],[72.3,24.1,3.6],[C.colors.green,C.colors.amber,C.colors.red]));
  }
};
