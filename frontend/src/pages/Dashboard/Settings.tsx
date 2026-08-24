import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <header>
        <h1 className="font-display text-3xl font-bold text-text">Platform Settings</h1>
        <p className="text-muted font-mono text-sm mt-1">GLOBAL CONFIGURATION</p>
      </header>

      <div className="bg-panel border border-muted/20 rounded-xl p-12 flex flex-col items-center justify-center text-center">
        <SettingsIcon size={48} className="text-muted mb-4" />
        <h2 className="text-xl font-bold text-text mb-2">System Settings</h2>
        <p className="text-muted max-w-md">
          Global configuration, API keys, and Razorpay Gateway integration parameters are managed via the secure environment variables (.env).
        </p>
      </div>
    </div>
  );
}
