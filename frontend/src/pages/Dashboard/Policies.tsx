import { ShieldAlert } from 'lucide-react';

export default function Policies() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <header>
        <h1 className="font-display text-3xl font-bold text-text">Security Policies</h1>
        <p className="text-muted font-mono text-sm mt-1">NL COMPILER & RULES ENGINE</p>
      </header>

      <div className="bg-panel border border-muted/20 rounded-xl p-12 flex flex-col items-center justify-center text-center">
        <ShieldAlert size={48} className="text-muted mb-4" />
        <h2 className="text-xl font-bold text-text mb-2">Policy Engine Configuration</h2>
        <p className="text-muted max-w-md">
          Natural language policy compilation and XGBoost threshold tuning are currently locked in this environment. Contact your Sentinel administrator to request access.
        </p>
      </div>
    </div>
  );
}
