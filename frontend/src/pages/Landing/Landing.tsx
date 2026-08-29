import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield,
  ArrowRight,
  Eye,
  Scale,
  Gavel,
  Lock,
  Database,
  Activity,
  Zap,
  Server,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
} from 'lucide-react';

// ─── NAVIGATION ─────────────────────────────────────────────────────────────
function Nav() {
  const navigate = useNavigate();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sentinel flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="font-display font-bold text-text-primary text-lg tracking-tight">Sentinel</span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-text-secondary">
          <a href="#product" className="hover:text-text-primary transition-colors">Product</a>
          <a href="#architecture" className="hover:text-text-primary transition-colors">Architecture</a>
          <a href="#security" className="hover:text-text-primary transition-colors">Security</a>
          <a href="#docs" className="hover:text-text-primary transition-colors">Docs</a>
          <a href="#pricing" className="hover:text-text-primary transition-colors">Pricing</a>
        </nav>

        <div className="flex items-center gap-3">
          <button className="px-4 py-2 text-sm font-medium text-text-primary border border-border-light rounded-lg hover:bg-background-elevated transition-colors">
            Book a Demo
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-sentinel text-white text-sm font-semibold rounded-lg hover:bg-sentinel-bright transition-colors flex items-center gap-2"
          >
            Open Dashboard <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}

// ─── HERO SECTION ───────────────────────────────────────────────────────────
function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative pt-32 pb-24 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-sentinel/10 blur-[120px] rounded-full" />
      </div>

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        {/* Left sidebar with numbered steps */}
        <div className="absolute left-6 top-32 hidden lg:block">
          <div className="space-y-8 text-text-muted">
            {[
              { n: '01', label: 'INTENT ARRIVES', desc: 'An AI agent requests to perform a financial action' },
              { n: '02', label: 'BEHAVIOR OBSERVATION', desc: 'Sentinel captures behavioral signals and compares with established baselines' },
              { n: '03', label: 'RISK BUILDUP', desc: 'Risk score rises as anomalies compound across multiple behavioral dimensions' },
              { n: '04', label: 'POLICY EVALUATION', desc: 'Deterministic policies are evaluated against the observed behavior' },
              { n: '05', label: 'DECISION', desc: 'Sentinel makes a deterministic authorization decision' },
              { n: '06', label: 'DECISION', desc: 'Sentinel makes a deterministic authorization decision' },
              { n: '07', label: 'EXECUTION ATTEMPT', desc: 'Agent attempts to execute the action through the execution adapter' },
              { n: '08', label: 'CONTAINMENT', desc: 'Unauthorized execution is blocked at the boundary' },
              { n: '09', label: 'AUDIT RECORD', desc: 'Every decision is immutably recorded with cryptographic integrity' },
            ].slice(0, 6).map(({ n, label }) => (
              <div key={n} className="flex items-start gap-3 group cursor-pointer">
                <div className="w-12 shrink-0">
                  <div className="text-[10px] font-bold text-sentinel tabular-nums">{n}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-text-secondary group-hover:text-text-primary transition-colors">
                    {label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main content */}
        <div className="lg:pl-40">
          <div className="text-center mb-16">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-6">
              AI AGENT AUTHORIZATION & CONTAINMENT LAYER
            </div>
            <h1 className="text-display-lg md:text-display-xl font-display font-bold text-text-primary leading-none mb-8 tracking-tight">
              YOUR AGENTS<br />
              CAN ACT.<br />
              <span className="block mt-2">THEY SHOULD NOT</span><br />
              <span className="block mt-2">ACT WITHOUT</span><br />
              <span className="block mt-2">BEING <span className="text-sentinel">VERIFIED.</span></span>
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto mb-12">
              Sentinel continuously evaluates autonomous financial intents against behavioral baselines, deterministic policy, and execution constraints.
            </p>
          </div>

          {/* Security Flow Visualization */}
          <div className="relative">
            <div className="flex items-center justify-center gap-8 mb-12">
              {/* AI Agent */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                className="flex flex-col items-center"
              >
                <div className="w-16 h-16 rounded-xl bg-background-elevated border border-border-light flex items-center justify-center mb-2">
                  <Server className="w-8 h-8 text-sentinel" />
                </div>
                <div className="text-xs font-semibold text-text-secondary">AI AGENT</div>
                <div className="text-[10px] text-text-muted font-mono mt-1">payment-agent-6c</div>
                <div className="text-[10px] text-text-muted font-mono">payroll_execute</div>
                <div className="text-[10px] text-text-muted font-mono">recipient: 481</div>
                <div className="text-[10px] text-text-muted font-mono">₹5,48,32</div>
              </motion.div>

              {/* Arrow */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6 }}
              >
                <ArrowRight className="w-6 h-6 text-sentinel" />
              </motion.div>

              {/* Intent */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.6 }}
                className="flex flex-col items-center"
              >
                <div className="w-16 h-16 rounded-xl bg-background-elevated border border-border-light flex items-center justify-center mb-2">
                  <Activity className="w-8 h-8 text-sentinel" />
                </div>
                <div className="text-xs font-semibold text-text-secondary">INTENT</div>
              </motion.div>

              {/* Arrow */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.6 }}
              >
                <ArrowRight className="w-6 h-6 text-sentinel" />
              </motion.div>

              {/* Sentinel Shield - Central piece */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8, duration: 0.8 }}
                className="flex flex-col items-center relative"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-sentinel/20 blur-2xl rounded-full animate-pulse-slow" />
                  <div className="w-32 h-32 rounded-2xl bg-background-elevated border-2 border-sentinel flex items-center justify-center mb-3 relative z-10">
                    <Shield className="w-16 h-16 text-sentinel drop-shadow-[0_0_15px_rgba(76,141,255,0.5)]" />
                  </div>
                </div>
                <div className="text-xs font-bold text-sentinel uppercase tracking-wider">Sentinel Security Field</div>
              </motion.div>

              {/* Arrow */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.0, duration: 0.6 }}
              >
                <ArrowRight className="w-6 h-6 text-sentinel" />
              </motion.div>

              {/* Execution */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.2, duration: 0.6 }}
                className="flex flex-col items-center"
              >
                <div className="w-16 h-16 rounded-xl bg-background-elevated border border-border-light flex items-center justify-center mb-2">
                  <Zap className="w-8 h-8 text-sentinel" />
                </div>
                <div className="text-xs font-semibold text-text-secondary">EXECUTION</div>
                <div className="text-[10px] text-text-muted mt-1">Payment Gateway</div>
              </motion.div>
            </div>

            {/* Four stages below */}
            <div className="grid grid-cols-4 gap-4 max-w-4xl mx-auto">
              {[
                { icon: Eye, label: 'OBSERVE' },
                { icon: Scale, label: 'EVALUATE' },
                { icon: Gavel, label: 'DECIDE' },
                { icon: Lock, label: 'ENFORCE' },
              ].map(({ icon: Icon, label }, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.4 + i * 0.1, duration: 0.4 }}
                  className="flex flex-col items-center"
                >
                  <div className="w-10 h-10 rounded-lg bg-background-elevated border border-border-light flex items-center justify-center mb-2">
                    <Icon className="w-5 h-5 text-sentinel" />
                  </div>
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{label}</div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex items-center justify-center gap-4 mt-16">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-3 bg-sentinel text-white font-semibold rounded-lg hover:bg-sentinel-bright transition-colors flex items-center gap-2"
            >
              Run Live Simulation <ArrowRight className="w-4 h-4" />
            </button>
            <button className="px-6 py-3 border border-border-light text-text-primary font-semibold rounded-lg hover:bg-background-elevated transition-colors">
              Explore Architecture
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── METRICS STRIP ──────────────────────────────────────────────────────────
function MetricsStrip() {
  const metrics = [
    { value: '97.2%', label: 'Expected Precision', sublabel: 'Detection rate' },
    { value: '<30ms', label: 'Decision Path', sublabel: 'Authorization latency' },
    { value: '5s', label: 'Token Lifetime', sublabel: 'Temporal scope' },
    { value: '100%', label: 'Fail Closed', sublabel: 'Security guarantee' },
    { value: '165+', label: 'Security Tests', sublabel: 'Validation coverage' },
    { value: '327 pps', label: 'Benchmark Throughput', sublabel: 'CPU baseline' },
  ];

  return (
    <div className="border-y border-border bg-background-elevated py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
          {metrics.map(({ value, label, sublabel }) => (
            <div key={label} className="text-center">
              <div className="text-3xl font-bold text-text-primary tabular-nums mb-1">{value}</div>
              <div className="text-xs font-semibold text-text-secondary">{label}</div>
              <div className="text-[10px] text-text-muted mt-0.5">{sublabel}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── BASELINE VS REAL-TIME ──────────────────────────────────────────────────
function BaselineComparisonSection() {
  return (
    <section className="py-24 bg-background">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            BEHAVIORAL OBSERVATION
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary mb-4">
            Real-time Anomaly Detection
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto">
            Sentinel continuously compares observed behavior against established baselines to detect drift.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Expected Baseline */}
          <div className="bg-background-card border border-border rounded-xl p-6">
            <div className="text-[10px] font-bold uppercase tracking-wider text-sentinel mb-4">
              EXPECTED BASELINE
            </div>
            <div className="space-y-3">
              {[
                { label: 'Amount', value: '₹8K - ₹20K' },
                { label: 'Recipient', value: 'Known' },
                { label: 'Velocity', value: 'Normal' },
                { label: 'Time', value: 'Business Hours' },
                { label: 'History', value: 'Frequent' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-border-light last:border-0">
                  <span className="text-sm text-text-muted">{label}</span>
                  <span className="text-sm font-mono text-text-secondary">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Observed Real-Time */}
          <div className="bg-background-card border border-contain rounded-xl p-6 relative">
            <div className="text-[10px] font-bold uppercase tracking-wider text-contain mb-4">
              OBSERVED REAL-TIME
            </div>
            <div className="space-y-3">
              {[
                { label: 'Amount', value: '₹52,400', alert: true },
                { label: 'Recipient', value: 'Unknown', alert: true },
                { label: 'Velocity', value: 'Elevated', alert: true },
                { label: 'Time', value: 'Off pattern', alert: true },
                { label: 'History', value: 'First time', alert: true },
              ].map(({ label, value, alert }) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-border-light last:border-0">
                  <span className="text-sm text-text-muted">{label}</span>
                  <span className={`text-sm font-mono font-semibold ${alert ? 'text-contain' : 'text-text-secondary'}`}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
            <div className="absolute top-2 right-2">
              <div className="w-2 h-2 rounded-full bg-contain animate-pulse-slow" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── RISK SCORE GAUGE ───────────────────────────────────────────────────────
function RiskScoreSection() {
  return (
    <section className="py-24 bg-background-elevated border-y border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            RISK SCORE
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary">
            Multi-dimensional Risk Fusion
          </h2>
        </div>

        <div className="max-w-3xl mx-auto bg-background-card border border-border rounded-xl p-12">
          <div className="flex items-center justify-center gap-16">
            {/* Risk gauge visualization */}
            <div className="relative">
              <div className="w-48 h-48 rounded-full border-8 border-background-elevated relative flex items-center justify-center">
                <div className="absolute inset-0 rounded-full" style={{
                  background: `conic-gradient(from 180deg, #10B981 0deg, #F5A623 120deg, #E5484D 240deg, #E5484D 360deg)`,
                }} />
                <div className="absolute inset-4 rounded-full bg-background-card flex flex-col items-center justify-center">
                  <div className="text-5xl font-bold text-contain tabular-nums">92</div>
                  <div className="text-xs font-bold text-contain uppercase tracking-wider mt-1">HIGH RISK</div>
                </div>
              </div>
            </div>

            {/* Score breakdown */}
            <div className="space-y-4">
              {[
                { level: 31, label: 'Low Risk', color: 'text-allow' },
                { level: 47, label: 'Medium', color: 'text-escalate' },
                { level: 63, label: 'High', color: 'text-escalate' },
                { level: 78, label: 'Critical', color: 'text-contain' },
              ].map(({ level, label, color }) => (
                <div key={label} className="flex items-center gap-4">
                  <div className="w-12 text-right">
                    <span className={`text-2xl font-bold tabular-nums ${color}`}>{level}</span>
                  </div>
                  <div className="flex-1">
                    <div className="h-2 bg-background-elevated rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${color.replace('text', 'bg')}`}
                        style={{ width: `${(level / 100) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-20 text-sm text-text-muted">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── POLICY MATCH ───────────────────────────────────────────────────────────
function PolicyMatchSection() {
  return (
    <section className="py-24 bg-background">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            POLICY MATCH
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary">
            Deterministic Authorization
          </h2>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Policy */}
          <div className="bg-background-card border border-border rounded-xl p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 className="w-5 h-5 text-sentinel" />
              <div className="text-sm font-bold text-text-primary uppercase tracking-wider">
                HIGH VALUE TRANSFER
              </div>
            </div>
            <div className="text-sm text-text-secondary mb-4">
              <span className="font-mono">amount &gt; ₹50,000</span>
            </div>
          </div>

          {/* Decision paths */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-allow-bg border border-allow rounded-xl p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-allow/20 flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="w-6 h-6 text-allow" />
              </div>
              <div className="text-xs font-bold text-allow uppercase tracking-wider mb-1">ALLOW</div>
              <div className="text-[10px] text-text-muted">Low Risk</div>
            </div>

            <div className="bg-escalate-bg border border-escalate rounded-xl p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-escalate/20 flex items-center justify-center mx-auto mb-3">
                <AlertTriangle className="w-6 h-6 text-escalate" />
              </div>
              <div className="text-xs font-bold text-escalate uppercase tracking-wider mb-1">ESCALATE</div>
              <div className="text-[10px] text-text-muted">Medium Risk</div>
            </div>

            <div className="bg-contain-bg border-2 border-contain rounded-xl p-5 text-center relative">
              <div className="absolute inset-0 bg-contain/5 rounded-xl" />
              <div className="relative">
                <div className="w-12 h-12 rounded-full bg-contain/20 flex items-center justify-center mx-auto mb-3">
                  <XCircle className="w-6 h-6 text-contain" />
                </div>
                <div className="text-xs font-bold text-contain uppercase tracking-wider mb-1">CONTAIN</div>
                <div className="text-[10px] text-contain">High Risk</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── ARCHITECTURE ───────────────────────────────────────────────────────────
function ArchitectureSection() {
  return (
    <section id="architecture" className="py-24 bg-background-elevated border-y border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            SENTINEL ARCHITECTURE
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary mb-6">
            A Deterministic Boundary for Autonomous Finance
          </h2>
          <p className="text-text-secondary max-w-3xl mx-auto">
            Sentinel provides a zero-trust execution layer that sits between AI agents and financial systems. Every action is verified, authorized, and auditable.
          </p>
        </div>

        {/* Pipeline diagram */}
        <div className="bg-background-card border border-border rounded-xl p-8 mb-8">
          <div className="flex items-center justify-between gap-4">
            {[
              { icon: Server, label: 'AI AGENT' },
              { icon: Activity, label: 'BEHAVIORAL\nRISK ENGINE' },
              { icon: FileText, label: 'POLICY\nENGINE' },
              { icon: Scale, label: 'DECISION\nENGINE' },
              { icon: Lock, label: 'CAPABILITY\nTOKEN' },
              { icon: Zap, label: 'EXECUTION\nADAPTER' },
              { icon: Database, label: 'AUDIT\nLEDGER' },
            ].map(({ icon: Icon, label }, i, arr) => (
              <div key={label} className="flex items-center gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-lg bg-background-elevated border border-border-light flex items-center justify-center mb-2">
                    <Icon className="w-6 h-6 text-sentinel" />
                  </div>
                  <div className="text-[9px] font-bold text-text-muted uppercase text-center whitespace-pre-line leading-tight">
                    {label}
                  </div>
                </div>
                {i < arr.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-sentinel/50" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="text-center">
          <a href="#docs" className="text-sentinel font-semibold text-sm hover:underline inline-flex items-center gap-2">
            View Full Architecture <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </section>
  );
}

// ─── SECURITY & COMPLIANCE ──────────────────────────────────────────────────
function SecuritySection() {
  return (
    <section id="security" className="py-24 bg-background">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            BUILT FOR FINANCIAL INFRASTRUCTURE
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary mb-4">
            Security by Design.<br />Performance by Default.
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto">
            Production-ready security controls with enterprise-grade performance and reliability.
          </p>
        </div>

        <div className="grid grid-cols-4 gap-6 mb-12">
          {[
            { value: '99.99%', label: 'System Uptime' },
            { value: '<30ms', label: 'P99 Latency' },
            { value: '24/7', label: 'Threat Monitoring' },
            { value: 'SOC 2', label: 'Compliant' },
          ].map(({ value, label }) => (
            <div key={label} className="bg-background-card border border-border rounded-xl p-6 text-center">
              <div className="text-3xl font-bold text-text-primary mb-2 tabular-nums">{value}</div>
              <div className="text-xs text-text-muted">{label}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            'ISO 27001 Certified',
            '256-bit Encryption',
            'RBAC Access Control',
            'Zero Trust Architecture',
          ].map((feature) => (
            <div key={feature} className="bg-background-card border border-border rounded-lg p-4 text-center">
              <div className="text-sm font-semibold text-text-primary">{feature}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── FINAL CTA ──────────────────────────────────────────────────────────────
function FinalCTA() {
  const navigate = useNavigate();

  return (
    <section className="py-24 bg-background-elevated border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-sentinel mb-4">
            READY TO SECURE YOUR AI AGENTS?
          </div>
          <h2 className="text-4xl font-display font-bold text-text-primary mb-6">
            Into the future of secure autonomous finance.<br />
            Run a simulation or explore the dashboard.
          </h2>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-4 bg-sentinel text-white font-bold rounded-lg hover:bg-sentinel-bright transition-colors text-lg flex items-center gap-2"
            >
              Run Live Simulation <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-4 border border-border-light text-text-primary font-bold rounded-lg hover:bg-background-card transition-colors text-lg"
            >
              Open Dashboard
            </button>
          </div>
        </div>

        {/* Dashboard preview metrics */}
        <div className="grid grid-cols-4 gap-4 max-w-4xl mx-auto mt-16">
          {[
            { value: '24,853', label: 'Sentinel Decisions', change: '+2,069' },
            { value: '22,761', label: 'Intents Processed', change: '+1,892' },
            { value: '2,092', label: 'Average Risk Score', change: '-89' },
            { value: '18ms', label: 'Response Time', change: 'Stable' },
          ].map(({ value, label, change }) => (
            <div key={label} className="bg-background-card border border-border rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-text-primary tabular-nums mb-1">{value}</div>
              <div className="text-xs text-text-muted mb-2">{label}</div>
              <div className="text-[10px] text-sentinel">{change}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Landing() {
  return (
    <div className="bg-background text-text-primary min-h-screen font-sans">
      <Nav />
      <HeroSection />
      <MetricsStrip />
      <BaselineComparisonSection />
      <RiskScoreSection />
      <PolicyMatchSection />
      <ArchitectureSection />
      <SecuritySection />
      <FinalCTA />
    </div>
  );
}
