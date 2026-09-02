const DemoScenariosPage={
  render(){
    const sc=D.scenarios;
    const diffColors={Easy:'var(--green)',Medium:'var(--amber)',Hard:'var(--red)',Expert:'var(--red)'};
    const typeBg={Attack:'rd',Evasion:'am',Baseline:'gn','Edge Case':'bl'};
    return `
    <div class="g-row" style="gap:16px">
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg></div><div class="stat-body"><div class="stat-val">${sc.length}</div><div class="stat-lbl">Available Scenarios</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-val">1,025</div><div class="stat-lbl">Total Samples</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="stat-body"><div class="stat-val">~45s</div><div class="stat-lbl">Avg Runtime</div></div></div>
    </div>
    <div style="margin-bottom:20px"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px"><h3 style="font-size:.875rem;font-weight:600">Select a Scenario</h3><div style="display:flex;gap:8px"><select class="form-input form-select" style="height:30px;font-size:.65rem;padding:0 28px 0 8px"><option>All Types</option><option>Attack</option><option>Evasion</option><option>Baseline</option><option>Edge Case</option></select></div></div>
    <div class="g-3 mb-0">${sc.map(s=>{
      const tb=typeBg[s.type]||'bl';
      return `<div class="scenario-card" data-scenario="${s.name}"><div class="scenario-header"><div class="scenario-icon" style="background:var(--${tb==='rd'?'red':tb==='am'?'amber':tb==='gn'?'green':'blue'}-bg)"><svg viewBox="0 0 24 24" fill="none" stroke="var(--${tb==='rd'?'red':tb==='am'?'amber':tb==='gn'?'green':'blue'})" stroke-width="2" stroke-linecap="round">${s.type==='Attack'?'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/>':s.type==='Evasion'?'<circle cx="12" cy="12" r="10"/><path d="M8 12s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>':s.type==='Baseline'?'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>':'<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'}</svg></div><div class="scenario-title">${s.name}</div></div><div class="scenario-desc">${s.desc}</div><div class="scenario-meta"><span>Type: <strong>${s.type}</strong></span><span>Samples: <strong>${s.samples}</strong></span><span>Difficulty: <strong style="color:${diffColors[s.difficulty]}">${s.difficulty}</strong></span></div></div>`;
    }).join('')}</div></div>
    <div class="card">
      <div class="card-head"><span class="card-t">Simulation Output</span><span style="font-size:.65rem;color:var(--text-tertiary)">Select a scenario above to run</span></div>
      <div id="sim-output" style="min-height:120px">
        <div class="empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:40px;height:40px;margin-bottom:12px"><polygon points="5 3 19 12 5 21 5 3"/></svg><div style="font-size:.75rem;color:var(--text-tertiary)">Click a scenario card to simulate</div></div>
      </div>
    </div>`;
  },
  mount(){
    document.querySelectorAll('.scenario-card').forEach(card=>{
      card.addEventListener('click',()=>{
        const name=card.dataset.scenario;
        const out=document.getElementById('sim-output');
        const total=Math.floor(Math.random()*200)+50;
        const allowed=Math.floor(total*0.65);
        const escalated=Math.floor(total*0.28);
        const contained=total-allowed-escalated;
        const avgRisk=(Math.random()*0.4+0.2).toFixed(3);
        out.innerHTML=`<div style="display:flex;gap:16px;margin-bottom:16px">
          <div class="metric-tile" style="flex:1"><div class="metric-tile-val">${total}</div><div class="metric-tile-lbl">Total</div></div>
          <div class="metric-tile" style="flex:1"><div class="metric-tile-val" style="color:var(--green)">${allowed}</div><div class="metric-tile-lbl">Allowed</div></div>
          <div class="metric-tile" style="flex:1"><div class="metric-tile-val" style="color:var(--amber)">${escalated}</div><div class="metric-tile-lbl">Escalated</div></div>
          <div class="metric-tile" style="flex:1"><div class="metric-tile-val" style="color:var(--red)">${contained}</div><div class="metric-tile-lbl">Contained</div></div>
          <div class="metric-tile" style="flex:1"><div class="metric-tile-val">${avgRisk}</div><div class="metric-tile-lbl">Avg Risk</div></div>
        </div>
        <div style="padding:12px;background:var(--green-bg);border-radius:var(--radius-md);font-size:.7rem;color:var(--green);font-weight:500;text-align:center">✓ Scenario "${name}" completed — ${contained} threats contained, 0 false opens</div>`;
      });
    });
  }
};
