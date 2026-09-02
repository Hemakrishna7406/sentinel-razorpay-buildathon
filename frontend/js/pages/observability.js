const ObservabilityPage={
  ch:[],
  render(){
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div class="stat-body"><div class="stat-val">327</div><div class="stat-lbl">Requests/sec</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="stat-body"><div class="stat-val">28ms</div><div class="stat-lbl">p50 Latency</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="stat-body"><div class="stat-val">35ms</div><div class="stat-lbl">p99 Latency</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-val">0.12%</div><div class="stat-lbl">Error Rate</div></div></div>
    </div>
    <div class="g-2">
      <div class="card">
        <div class="card-head"><span class="card-t">Request Rate</span></div>
        <div class="chart-wrap" style="height:200px"><canvas id="ch-obs-req"></canvas></div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Authorization Latency (p50 / p95 / p99)</span><div style="display:flex;gap:8px"><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.green}"></span>p50</span><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.blue}"></span>p95</span><span style="display:flex;align-items:center;gap:4px;font-size:.6rem"><span style="width:8px;height:8px;border-radius:50%;background:${C.colors.amber}"></span>p99</span></div></div>
        <div class="chart-wrap" style="height:200px"><canvas id="ch-obs-latency"></canvas></div>
      </div>
    </div>
    <div class="g-2">
      <div class="card">
        <div class="card-head"><span class="card-t">Error Rate</span></div>
        <div class="chart-wrap" style="height:180px"><canvas id="ch-obs-error"></canvas></div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Dependency Health</span></div>
        ${D.infra.map(i=>`<div class="infra-item"><div class="infra-dot" style="background:var(--green)"></div><div style="flex:1"><div class="infra-name">${i.name}</div><div class="infra-sub">${i.sub}</div></div><div class="infra-ms">${i.ms} ms</div><span class="badge badge-healthy">UP</span></div>`).join('')}
      </div>
    </div>
    <div class="g-2 mb-0">
      <div class="card">
        <div class="card-head"><span class="card-t">Active Traces</span></div>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Trace ID</th><th>Operation</th><th>Duration</th><th>Status</th><th>Spans</th></tr></thead><tbody>
          <tr><td class="tbl-mono">tr-a1b2c3</td><td>evaluate_intent</td><td>24ms</td><td><span class="badge badge-allow">OK</span></td><td>7</td></tr>
          <tr><td class="tbl-mono">tr-d4e5f6</td><td>evaluate_intent</td><td>31ms</td><td><span class="badge badge-allow">OK</span></td><td>7</td></tr>
          <tr><td class="tbl-mono">tr-g7h8i9</td><td>evaluate_intent</td><td>128ms</td><td><span class="badge badge-warning">SLOW</span></td><td>7</td></tr>
          <tr><td class="tbl-mono">tr-j0k1l2</td><td>razorpay_execute</td><td>340ms</td><td><span class="badge badge-allow">OK</span></td><td>3</td></tr>
          <tr><td class="tbl-mono">tr-m3n4o5</td><td>evaluate_intent</td><td>22ms</td><td><span class="badge badge-allow">OK</span></td><td>7</td></tr>
        </tbody></table></div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Recent Logs</span></div>
        <div class="card-scroll" style="font-family:var(--mono);font-size:.6rem;line-height:1.8;color:var(--text-secondary)">
          <div><span style="color:var(--text-tertiary)">14:32:01</span> <span style="color:var(--green)">INFO</span> evaluate_intent intent=INT-a3f2c1 decision=ALLOW risk=0.03 latency=24ms</div>
          <div><span style="color:var(--text-tertiary)">14:31:45</span> <span style="color:var(--red)">WARN</span> evaluate_intent intent=INT-b7e4d9 decision=CONTAIN risk=0.91 latency=31ms</div>
          <div><span style="color:var(--text-tertiary)">14:31:12</span> <span style="color:var(--amber)">WARN</span> evaluate_intent intent=INT-c1d5a8 decision=ESCALATE risk=0.62 latency=28ms</div>
          <div><span style="color:var(--text-tertiary)">14:30:58</span> <span style="color:var(--green)">INFO</span> evaluate_intent intent=INT-d9f2b3 decision=ALLOW risk=0.06 latency=22ms</div>
          <div><span style="color:var(--text-tertiary)">14:30:22</span> <span style="color:var(--green)">INFO</span> evaluate_intent intent=INT-e4a1c7 decision=ALLOW risk=0.11 latency=19ms</div>
          <div><span style="color:var(--text-tertiary)">14:29:45</span> <span style="color:var(--amber)">WARN</span> evaluate_intent intent=INT-f8b3d2 decision=ESCALATE risk=0.35 latency=26ms</div>
          <div><span style="color:var(--text-tertiary)">14:29:10</span> <span style="color:var(--green)">INFO</span> capability_issued jti=jti_4f7a2b agent=checkout-agent-01 ttl=5s</div>
          <div><span style="color:var(--text-tertiary)">14:28:33</span> <span style="color:var(--red)">WARN</span> evaluate_intent intent=INT-b5d7f9 decision=CONTAIN risk=0.88 latency=35ms</div>
          <div><span style="color:var(--text-tertiary)">14:28:10</span> <span style="color:var(--green)">INFO</span> audit_chain_verify status=PASS records=98765</div>
          <div><span style="color:var(--text-tertiary)">14:27:55</span> <span style="color:var(--green)">INFO</span> model_health status=loaded version=xgb-v2.1 features=15</div>
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const o=D.observability;
    this.ch.push(C.line('ch-obs-req',o.reqRate.labels,[C.areaDS('RPS',o.reqRate.vals,C.colors.blue)]));
    this.ch.push(C.line('ch-obs-latency',o.latencyLabels,[C.lineDS('p50',o.latencyP50,C.colors.green),C.lineDS('p95',o.latencyP95,C.colors.blue),C.lineDS('p99',o.latencyP99,C.colors.amber)]));
    this.ch.push(C.line('ch-obs-error',o.errorRate.labels,[C.areaDS('Error %',o.errorRate.vals,C.colors.red)],{scales:{y:{max:0.5}}}));
  }
};
