const App={
  pages:{
    'overview':      {m:OverviewPage,         t:'Overview',           s:'Real-time overview of authorization control plane'},
    'live-auth':     {m:LiveAuthPage,          t:'Live Authorization', s:'Real-time feed of authorization decisions'},
    'agents':        {m:AgentsPage,            t:'Agents',             s:'Track behavioral drift, risk scores, and policy violations per agent'},
    'risk-intelligence':{m:RiskIntelligencePage,t:'Risk Intelligence', s:'Fraud events, decision trends, financial impact, and volume forecasting'},
    'audit-ledger':  {m:AuditLedgerPage,       t:'Audit Ledger',       s:'Immutable ledger of all evaluated intents and security invariants'},
    'policy-studio': {m:PolicyStudioPage,      t:'Policy Studio',      s:'Manage natural-language policy rules for the authorization pipeline'},
    'demo-scenarios':{m:DemoScenariosPage,     t:'Demo Scenarios',     s:'Simulate real-world attack scenarios and test detection accuracy'},
    'security-center':{m:SecurityCenterPage,   t:'Security Center',    s:'Security invariants, threat model coverage, and penetration test results'},
    'observability': {m:ObservabilityPage,      t:'Observability',      s:'Metrics, traces, logs, and dependency health monitoring'},
    'settings':      {m:SettingsPage,           t:'Settings',           s:'Configure profile, notifications, security, and system parameters'}
  },
  async init(){
    window.addEventListener('hashchange',()=>this.route());
    if(!location.hash||location.hash==='#/') location.hash='#/login';
    else this.route();
  },
  async route(){
    const h=(location.hash.replace('#/','')||'login').split('?')[0];
    if(h==='login'){document.getElementById('app').innerHTML=LoginPage.render();LoginPage.mount();document.title='Sentinel — Sign In';return}
    
    // Fetch real data before rendering page
    await D.init();
    
    const p=this.pages[h];
    if(!p){location.hash='#/overview';return}
    const pageEl=document.getElementById('app');
    pageEl.style.opacity='0';
    setTimeout(()=>{
      pageEl.innerHTML=`<div class="app-shell">${Sidebar.render(h)}<div class="main-wrap">${Header.render(p.t,p.s)}<div class="page fade-in">${p.m.render()}</div></div></div>`;
      pageEl.style.opacity='1';
      Sidebar.bind();
      p.m.mount();
      document.title='Sentinel — '+p.t;
    },80);
  }
};
document.addEventListener('DOMContentLoaded',()=>App.init());
