import { Activity, ShieldAlert, Zap, Server } from 'lucide-react';
import { useExecutionStream } from '../../hooks/useExecutionStream';
import { ExecutionPipeline } from '../../components/ExecutionPipeline/ExecutionPipeline';
import { DemoControls } from '../../components/DemoControls/DemoControls';
import { CapabilityToken } from '../../components/CapabilityToken/CapabilityToken';
import { MCPStatus } from '../../components/MCPStatus/MCPStatus';
import { RiskIntelligence } from '../../components/RiskIntelligence/RiskIntelligence';
import TrustPulse from '../../components/TrustPulse/TrustPulse';
import { useMemo } from 'react';

export default function Overview() {
  const { activeIntent, events, isConnected } = useExecutionStream();

  const isAnomalous = activeIntent?.policy_decision === 'CONTAIN' || activeIntent?.execution_status === 'BLOCKED';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      {/* HEADER & SYSTEM STATUS */}
      <header className="flex justify-between items-end">
        <div>
          <h1 className="font-display text-3xl font-bold text-text">Execution Control Room</h1>
          <p className="text-muted font-mono text-sm mt-1">SENTINEL-CORE // LIVE GOVERNANCE</p>
        </div>
        
        <div className="flex gap-4">
          <div className="flex items-center gap-2 font-mono text-xs bg-panel border border-muted/20 px-3 py-1.5 rounded-md">
            <span className="text-muted">MCP:</span>
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-signal' : 'bg-muted'}`}></div>
            <span className={isConnected ? 'text-signal' : 'text-muted'}>
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          
          <div className="flex items-center gap-2 font-mono text-xs bg-panel border border-muted/20 px-3 py-1.5 rounded-md transition-colors duration-500" style={{ borderColor: isAnomalous ? '#E5484D' : '' }}>
            <span className="text-muted">SYSTEM:</span>
            <div className={`w-1.5 h-1.5 rounded-full ${isAnomalous ? 'bg-contain' : 'bg-signal animate-pulse'}`}></div>
            <span className={isAnomalous ? 'text-contain font-bold' : 'text-signal'}>
              {isAnomalous ? 'INTERCEPTED' : 'OPERATIONAL'}
            </span>
          </div>
        </div>
      </header>

      {/* DEMO CONTROLS */}
      <DemoControls />

      {/* HERO PIPELINE */}
      <ExecutionPipeline activeEvent={activeIntent} />

      {/* DETAILS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* RISK & TRUST */}
        <div className="lg:col-span-2 space-y-6">
          <RiskIntelligence activeEvent={activeIntent} />
          
          <div className="bg-panel border border-muted/20 rounded-xl overflow-hidden p-6 relative">
            <h3 className="font-display font-bold text-lg text-text mb-2">Trust Pulse</h3>
            <p className="text-xs font-mono text-muted mb-4">BEHAVIORAL DRIFT VISUALIZATION</p>
            <div className="absolute inset-0 bg-gradient-to-r from-panel via-transparent to-panel z-10 pointer-events-none" />
            <TrustPulse amplitude={activeIntent?.behavioral_risk || 0} />
          </div>
        </div>

        {/* SECURITY & EXECUTION */}
        <div className="space-y-6 flex flex-col">
          <div className="flex-1">
            <CapabilityToken activeEvent={activeIntent} />
          </div>
          <div className="flex-1">
            <MCPStatus activeEvent={activeIntent} />
          </div>
        </div>
      </div>

    </div>
  );
}
