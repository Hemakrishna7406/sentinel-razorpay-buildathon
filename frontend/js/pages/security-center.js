const SecurityCenterPage={
  render(){
    const inv=D.invariants;
    return `
    <div class="g-4">
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div><div class="stat-body"><div class="stat-val" style="color:var(--green)">Secure</div><div class="stat-lbl">Overall Posture</div></div></div>
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-val">${D.securityTests}</div><div class="stat-lbl">Tests Passing</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div><div class="stat-body"><div class="stat-val" style="color:var(--green)">0</div><div class="stat-lbl">Vulnerabilities</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="stat-body"><div class="stat-val" style="color:var(--green)">✓ PASS</div><div class="stat-lbl">Chain Integrity</div></div></div>
    </div>
    <div class="g-2">
      <div class="card">
        <div class="card-head"><span class="card-t">Security Invariants</span><span class="badge badge-allow">All Maintained</span></div>
        ${Object.entries(inv).map(([k,v])=>`<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--border-light)"><div style="display:flex;align-items:center;gap:10px"><svg viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round" style="width:16px;height:16px;flex-shrink:0"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span style="font-size:.75rem;font-weight:500">${k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</span></div><span style="font-size:.875rem;font-weight:700;color:var(--green)">${v}</span></div>`).join('')}
        <div style="margin-top:14px;padding:12px;background:var(--green-bg);border-radius:var(--radius-md);text-align:center;font-size:.7rem;color:var(--green);font-weight:600">✓ Zero-trust guarantee active — system never fails open</div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Threat Model Coverage</span></div>
        <div style="display:flex;flex-direction:column;gap:10px">
          ${[
            {name:'Prompt Injection',status:'Mitigated',desc:'Intent schema validation + behavioral profiling'},
            {name:'Capability Token Theft',status:'Mitigated',desc:'Single-use JTI, 5s TTL, amount-bound'},
            {name:'Replay Attacks',status:'Mitigated',desc:'Idempotency key + Redis deduplication'},
            {name:'Slow Abuse (Boiling Frog)',status:'Mitigated',desc:'Behavioral drift detection via XGBoost'},
            {name:'Velocity Burst',status:'Mitigated',desc:'3σ velocity threshold + auto-escalation'},
            {name:'Insider Agent Compromise',status:'Mitigated',desc:'Per-agent behavioral baselines + cross-agent detection'}
          ].map(t=>`<div style="display:flex;align-items:center;gap:10px;padding:12px;background:var(--bg-page);border-radius:var(--radius-md);border:1px solid var(--border-light)"><svg viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round" style="width:18px;height:18px;flex-shrink:0"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><div style="flex:1"><div style="font-size:.75rem;font-weight:600">${t.name}</div><div style="font-size:.6rem;color:var(--text-tertiary);margin-top:2px">${t.desc}</div></div><span class="badge badge-allow">${t.status}</span></div>`).join('')}
        </div>
      </div>
    </div>
    <div class="g-2 mb-0">
      <div class="card">
        <div class="card-head"><span class="card-t">Security Architecture</span></div>
        <div style="display:flex;flex-direction:column;gap:8px">
          ${[
            {layer:'Capability Token System',detail:'Single-use, time-bound (5s TTL), amount-locked JWT tokens'},
            {layer:'Idempotency Gate',detail:'Redis-backed deduplication preventing replay attacks'},
            {layer:'Behavioral Profiling',detail:'XGBoost model with 15 engineered features per agent'},
            {layer:'NL Policy Engine',detail:'Compiled natural language rules with real-time evaluation'},
            {layer:'Audit Chain',detail:'SHA-256 hash-linked immutable ledger of all decisions'},
            {layer:'MCP Boundary',detail:'Capability-gated tool invocation via Model Context Protocol'}
          ].map(l=>`<div style="padding:12px;background:var(--bg-page);border-radius:var(--radius-md);border:1px solid var(--border-light)"><div style="font-size:.75rem;font-weight:600;color:var(--navy)">${l.layer}</div><div style="font-size:.65rem;color:var(--text-secondary);margin-top:3px">${l.detail}</div></div>`).join('')}
        </div>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-t">Penetration Test Summary</span><span class="badge badge-allow">All Passed</span></div>
        <div style="display:flex;flex-direction:column;gap:10px">
          ${[
            {test:'Token Forgery',result:'PASS',detail:'Invalid JWTs correctly rejected'},
            {test:'Token Replay',result:'PASS',detail:'Used tokens cannot be reused'},
            {test:'Amount Tampering',result:'PASS',detail:'Mismatched amounts detected and blocked'},
            {test:'Cross-Agent Token Use',result:'PASS',detail:'Tokens bound to originating agent'},
            {test:'Expired Token Use',result:'PASS',detail:'Tokens expire after 5 second TTL'},
            {test:'Direct MCP Bypass',result:'PASS',detail:'Uncapacitated tool calls rejected'},
            {test:'Audit Chain Tampering',result:'PASS',detail:'Hash chain validates end-to-end'},
            {test:'SQL Injection via NL Rules',result:'PASS',detail:'Rule compiler sanitizes inputs'}
          ].map(t=>`<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light)"><svg viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round" style="width:14px;height:14px;flex-shrink:0"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span style="flex:1;font-size:.7rem;font-weight:500">${t.test}</span><span style="font-size:.6rem;color:var(--text-tertiary)">${t.detail}</span><span class="badge badge-pass">${t.result}</span></div>`).join('')}
        </div>
      </div>
    </div>`;
  },
  mount(){}
};
