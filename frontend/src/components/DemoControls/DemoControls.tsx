import { useDemoScenario } from '../../hooks/useDemoScenario';
import { Play, AlertTriangle, ShieldX, TerminalSquare } from 'lucide-react';

export function DemoControls() {
  const { triggerScenario, isRunning } = useDemoScenario();

  return (
    <div className="bg-panel border border-muted/20 p-5 rounded-xl space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="font-display font-bold text-lg text-text">Demo Control Panel</h2>
        <div className="px-2 py-1 bg-amber-500/20 text-amber-500 text-xs font-mono rounded">
          DEMO SCENARIO MODE
        </div>
      </div>
      <p className="text-sm text-muted">
        Trigger backend events. Real financial mutations are blocked or routed to test APIs.
      </p>

      <div className="space-y-4">
        <div>
          <div className="text-xs font-mono text-muted uppercase mb-2 border-b border-muted/10 pb-1">Simulation</div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <button
              disabled={isRunning}
              onClick={() => triggerScenario('normal')}
              className="flex flex-col items-start p-3 bg-ink hover:bg-ink/80 border border-muted/20 rounded-lg transition-colors group disabled:opacity-50"
            >
              <Play className="text-signal mb-2 group-hover:scale-110 transition-transform" size={20} />
              <span className="font-bold text-sm text-text">Normal Order</span>
              <span className="text-xs text-muted text-left">Legitimate flow</span>
            </button>

            <button
              disabled={isRunning}
              onClick={() => triggerScenario('abuse-burst')}
              className="flex flex-col items-start p-3 bg-ink hover:bg-ink/80 border border-muted/20 rounded-lg transition-colors group disabled:opacity-50"
            >
              <AlertTriangle className="text-contain mb-2 group-hover:scale-110 transition-transform" size={20} />
              <span className="font-bold text-sm text-text">Abuse Burst</span>
              <span className="text-xs text-muted text-left">Behavioral drift</span>
            </button>

            <button
              disabled={isRunning}
              onClick={() => triggerScenario('privilege-violation')}
              className="flex flex-col items-start p-3 bg-ink hover:bg-ink/80 border border-muted/20 rounded-lg transition-colors group disabled:opacity-50"
            >
              <ShieldX className="text-drift mb-2 group-hover:scale-110 transition-transform" size={20} />
              <span className="font-bold text-sm text-text">Privilege Violation</span>
              <span className="text-xs text-muted text-left">Wrong MCP tool</span>
            </button>
          </div>
        </div>

        <div>
          <div className="text-xs font-mono text-purple-400 uppercase mb-2 border-b border-purple-400/20 pb-1">Razorpay Test Environment</div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <button
              disabled={isRunning}
              onClick={() => triggerScenario('real-test-order')}
              className="flex flex-col items-start p-3 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg transition-colors group disabled:opacity-50 lg:col-span-1"
            >
              <TerminalSquare className="text-purple-400 mb-2 group-hover:scale-110 transition-transform" size={20} />
              <span className="font-bold text-sm text-purple-100">Execute Test Order</span>
              <span className="text-xs text-purple-300/70 text-left">Real Gate 3 verification</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
