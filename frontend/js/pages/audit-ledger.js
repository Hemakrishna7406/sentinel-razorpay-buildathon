const AuditLedgerPage={
  render(){
    const inv=D.invariants, rec=D.auditRecords;
    return `
    <div class="g-row" style="gap:16px">
      <div class="stat-card"><div class="stat-icon bl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="stat-body"><div class="stat-val">98,765</div><div class="stat-lbl">Total Records</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-val" style="color:var(--green)">✓ PASS</div><div class="stat-lbl">Chain Integrity</div></div></div>
      <div class="stat-card"><div class="stat-icon gn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div><div class="stat-body"><div class="stat-val" style="color:var(--green)">0</div><div class="stat-lbl">Security Violations</div></div></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-head"><span class="card-t">Execution Pipeline</span><span style="font-size:.6rem;color:var(--text-tertiary)">Zero-trust: any failure → ESCALATE or CONTAIN</span></div>
      <div class="pipeline">${D.pipeline.map((p,i)=>`${i>0?'<span class="pipe-arrow">→</span>':''}<div class="pipe-stage ok"><div class="pipe-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:16px;height:16px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="pipe-name">${p.name}</div><div class="pipe-val">${typeof p.count==='number'?p.count.toLocaleString():p.count}</div></div>`).join('')}</div>
    </div>
    <div class="g-23">
      <div class="card">
        <div class="card-head"><span class="card-t">Immutable Audit Ledger</span><div style="display:flex;gap:8px"><select class="form-input form-select" style="height:28px;font-size:.65rem;padding:0 28px 0 8px"><option>All Decisions</option><option>ALLOW</option><option>ESCALATE</option><option>CONTAIN</option></select></div></div>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>ID</th><th>Intent</th><th>Agent</th><th>Action</th><th>Amount</th><th>Risk</th><th>Decision</th><th>Reason</th><th>Cap. JTI</th><th>TX ID</th><th>Timestamp</th></tr></thead><tbody>${rec.map(r=>{
          const bc=r.decision==='ALLOW'?'badge-allow':r.decision==='ESCALATE'?'badge-escalate':'badge-contain';
          const rc=r.risk<0.15?'var(--green)':r.risk<0.5?'var(--amber)':'var(--red)';
          return `<tr><td class="tbl-mono">${r.id}</td><td class="tbl-mono">${r.intent}</td><td style="font-size:.65rem">${r.agent}</td><td>${r.action}</td><td>₹${(r.amount/100).toLocaleString()}</td><td><span style="color:${rc};font-weight:600">${r.risk.toFixed(2)}</span></td><td><span class="badge ${bc}">${r.decision}</span></td><td style="max-width:140px;overflow:hidden;text-overflow:ellipsis" title="${r.reason}">${r.reason}</td><td class="tbl-mono">${r.jti||'—'}</td><td class="tbl-mono">${r.tx||'—'}</td><td style="font-size:.6rem;color:var(--text-tertiary);white-space:nowrap">${r.ts}</td></tr>`;
        }).join('')}</tbody></table></div>
      </div>
      <div>
        <div class="card" style="margin-bottom:20px">
          <div class="card-head"><span class="card-t">Security Invariants</span><span class="badge badge-allow">All Clear</span></div>
          ${Object.entries(inv).map(([k,v])=>`<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border-light)"><span style="font-size:.7rem;font-weight:500">${k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</span><span style="font-size:.8125rem;font-weight:700;color:var(--green)">${v}</span></div>`).join('')}
          <div style="margin-top:14px;padding:10px;background:var(--green-bg);border-radius:var(--radius-md);text-align:center;font-size:.65rem;color:var(--green);font-weight:600">✓ Zero-trust guarantee: Never fails open to ALLOW</div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-t">Audit Chain</span></div>
          <div style="text-align:center;padding:16px 0"><div style="font-size:2rem;font-weight:800;color:var(--green)">✓ PASS</div><div style="font-size:.75rem;color:var(--text-secondary);margin-top:4px">98,765 records verified</div><div style="font-size:.65rem;color:var(--text-tertiary);margin-top:2px">0 invalid records</div></div>
          <div class="divider"></div>
          <div style="font-size:.65rem;color:var(--text-tertiary);line-height:1.6">Each audit record contains a SHA-256 hash of the previous record, forming an immutable chain.</div>
        </div>
      </div>
    </div>`;
  },
  mount(){}
};
