const PolicyStudioPage={
  ch:[],
  render(){
    const rules=D.policyRules;
    const active=rules.filter(r=>r.status==='active').length;
    const hits=rules.reduce((s,r)=>s+r.hits,0);
    return `
    <div class="g-row" style="gap:16px">
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div><div class="stat-body"><div class="stat-val">${active}</div><div class="stat-lbl">Active Rules</div></div></div>
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div class="stat-body"><div class="stat-val">${D.kpis.totalRequests.toLocaleString()}</div><div class="stat-lbl">Evaluations (24h)</div></div></div>
      <div class="stat-card"><div class="stat-icon am"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></div><div class="stat-body"><div class="stat-val">${hits}</div><div class="stat-lbl">Policy Escalations</div></div></div>
    </div>
    <div class="g-23">
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Add Policy Rule</span></div>
          <div style="display:flex;gap:10px"><input type="text" class="form-input" id="new-rule" placeholder='e.g. ESCALATE IF amount > 5000000' style="flex:1"><button class="btn btn-blue" id="add-rule-btn">Add Rule</button></div>
          <div class="policy-chips"><span class="policy-chip" data-r="ESCALATE IF amount > 5000000">ESCALATE IF amount > 5000000</span><span class="policy-chip" data-r="CONTAIN IF model_risk > 0.9">CONTAIN IF model_risk > 0.9</span><span class="policy-chip" data-r='ESCALATE IF currency != "INR"'>ESCALATE IF currency != "INR"</span></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Active Policy Rules</span></div>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Rule ID</th><th>Definition</th><th>Status</th><th>Hits</th><th>Created</th><th>Actions</th></tr></thead><tbody>${rules.map(r=>`<tr><td class="tbl-mono">${r.id}</td><td style="font-family:var(--mono);font-size:.6rem">${r.text}</td><td><span class="badge badge-${r.status==='active'?'active':'warning'}">${r.status}</span></td><td><strong>${r.hits}</strong></td><td style="font-size:.65rem;color:var(--text-tertiary)">${r.created}</td><td><button class="btn btn-danger btn-sm"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button></td></tr>`).join('')}</tbody></table></div>
        </div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Rule Hit Frequency</span></div>
          <div class="chart-wrap" style="height:200px"><canvas id="ch-rule-hits"></canvas></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Rule Simulator</span></div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <div class="form-group"><label class="form-label">Amount (₹)</label><input type="number" class="form-input" id="sim-amt" value="5500000"></div>
            <div class="form-group"><label class="form-label">Action Type</label><select class="form-input form-select" id="sim-action"><option>payout</option><option>checkout</option><option>refund</option><option>retry</option></select></div>
            <div class="form-group"><label class="form-label">Agent ID</label><input type="text" class="form-input" id="sim-agent" value="checkout-agent-01"></div>
            <button class="btn btn-blue" id="sim-btn" style="width:100%"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:14px;height:14px"><polygon points="5 3 19 12 5 21 5 3"/></svg>Test Rules</button>
            <div id="sim-result" style="display:none;padding:14px;border-radius:var(--radius-md);text-align:center"></div>
          </div>
        </div>
      </div>
    </div>`;
  },
  mount(){
    this.ch.forEach(c=>C.destroy(c)); this.ch=[];
    const active=D.policyRules.filter(r=>r.status==='active');
    this.ch.push(C.bar('ch-rule-hits',active.map(r=>r.id),[C.barDS('Hits',active.map(r=>r.hits),C.colors.blue+'70')]));
    document.querySelectorAll('.policy-chip').forEach(c=>c.addEventListener('click',()=>{document.getElementById('new-rule').value=c.dataset.r}));
    const simBtn=document.getElementById('sim-btn');
    if(simBtn) simBtn.addEventListener('click',()=>{
      const amt=parseInt(document.getElementById('sim-amt').value)||0;
      const res=document.getElementById('sim-result');
      let dec='ALLOW',reason='All rules passed.';
      if(amt>10000000){dec='CONTAIN';reason='Amount exceeds absolute limit (>₹1Cr).';}
      else if(amt>5000000){dec='ESCALATE';reason='Triggered NL-001: amount > 5000000.';}
      const cols={ALLOW:'var(--green)',ESCALATE:'var(--amber)',CONTAIN:'var(--red)'};
      const bgs={ALLOW:'var(--green-bg)',ESCALATE:'var(--amber-bg)',CONTAIN:'var(--red-bg)'};
      res.style.display='block';res.style.background=bgs[dec];res.style.border='1px solid '+cols[dec];
      res.innerHTML=`<div style="font-size:1rem;font-weight:700;color:${cols[dec]}">${dec}</div><div style="font-size:.65rem;color:var(--text-secondary);margin-top:4px">${reason}</div>`;
    });
  }
};
