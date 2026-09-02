const Sidebar = {
  ic: {
    logo:`<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="14" stroke="#2563EB" stroke-width="2"/><path d="M22 12c0 0-2.5-2-6-2s-6 3-6 5c0 4 4 5 6 5s6 1 6 4c0 1.5-2.5 4-6 4s-6-2-6-2" stroke="#2563EB" stroke-width="2" stroke-linecap="round"/><circle cx="16" cy="6" r="1.5" fill="#2563EB"/><circle cx="16" cy="28" r="1.5" fill="#2563EB"/></svg>`,
    overview:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="4" rx="1.5"/><rect x="14" y="10" width="7" height="11" rx="1.5"/><rect x="3" y="13" width="7" height="8" rx="1.5"/></svg>`,
    liveAuth:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    agents:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    risk:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    audit:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>`,
    policy:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>`,
    demo:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
    security:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
    observability:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    settings:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`
  },
  nav:[
    {id:'overview', icon:'overview', label:'Overview'},
    {id:'live-auth', icon:'liveAuth', label:'Live Authorization'},
    {id:'agents', icon:'agents', label:'Agents'},
    {id:'risk-intelligence', icon:'risk', label:'Risk Intelligence'},
    {id:'audit-ledger', icon:'audit', label:'Audit Ledger'},
    {id:'policy-studio', icon:'policy', label:'Policy Studio'},
    {id:'demo-scenarios', icon:'demo', label:'Demo Scenarios'},
    {id:'security-center', icon:'security', label:'Security Center'},
    {id:'observability', icon:'observability', label:'Observability'},
    {id:'settings', icon:'settings', label:'Settings'}
  ],
  render(active){
    return `<aside class="sidebar"><div class="sidebar-brand">${this.ic.logo}<span>SENTINEL</span></div><nav class="sidebar-nav">${this.nav.map(n=>`<button class="sidebar-item${active===n.id?' active':''}" data-page="${n.id}">${this.ic[n.icon]}${n.label}</button>`).join('')}</nav><div class="sidebar-bottom"><div class="sidebar-user"><div class="sidebar-avatar">AM</div><div class="sidebar-user-info"><div class="sidebar-user-name">Alicia Morgan</div><div class="sidebar-user-role">Security Engineer</div></div><svg viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.4)" stroke-width="2" style="width:14px;height:14px"><path d="M6 9l6 6 6-6"/></svg></div><div class="sidebar-status"><div class="sidebar-status-dot"></div><span class="sidebar-status-text">All Systems Operational</span></div></div></aside>`;
  },
  bind(){
    document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>location.hash='#/'+b.dataset.page));
  }
};
