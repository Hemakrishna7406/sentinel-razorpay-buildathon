import { SentinelExecutionEvent } from '../../hooks/useExecutionStream';
import { Lock, CheckCircle2, XCircle } from 'lucide-react';

export function CapabilityToken({ activeEvent }: { activeEvent: SentinelExecutionEvent | null }) {
  const isIssued = activeEvent?.capability_issued === true;
  const isDenied = activeEvent?.capability_issued === false;
  
  if (!activeEvent || activeEvent.stage === 'INTENT' || activeEvent.stage === 'BEHAVIOR' || activeEvent.stage === 'POLICY' && !isIssued && !isDenied) {
    return (
      <div className="bg-panel border border-muted/20 p-5 rounded-xl h-full flex flex-col items-center justify-center text-muted opacity-50">
        <Lock size={32} className="mb-3" />
        <div className="font-mono text-sm uppercase tracking-widest">Awaiting Policy</div>
      </div>
    );
  }

  if (isDenied) {
    return (
      <div className="bg-contain/5 border border-contain/20 p-5 rounded-xl h-full relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <XCircle size={120} className="text-contain" />
        </div>
        <h3 className="font-display font-bold text-contain text-lg mb-4 flex items-center gap-2">
          <XCircle size={18} /> Capability Denied
        </h3>
        <div className="space-y-3 font-mono text-xs relative z-10">
          <div className="flex justify-between border-b border-contain/10 pb-1">
            <span className="text-contain/70">AGENT</span>
            <span className="text-contain">{activeEvent.agent_id}</span>
          </div>
          <div className="flex justify-between border-b border-contain/10 pb-1">
            <span className="text-contain/70">REASON</span>
            <span className="text-contain text-right">{activeEvent.reason_codes?.[0] || 'Policy containment'}</span>
          </div>
          <div className="flex justify-between border-b border-contain/10 pb-1">
            <span className="text-contain/70">STATUS</span>
            <span className="text-contain font-bold">BLOCKED</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-panel to-ink border border-signal/30 p-5 rounded-xl h-full relative overflow-hidden group shadow-[0_0_20px_rgba(76,141,255,0.05)]">
      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <Lock size={120} className="text-signal" />
      </div>
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <h3 className="font-display font-bold text-text text-lg flex items-center gap-2">
          <CheckCircle2 size={18} className="text-signal" /> Capability Issued
        </h3>
        <div className="px-2 py-0.5 bg-signal/10 border border-signal/20 text-signal text-[10px] font-mono rounded">
          EXACT-ACTION AUTH
        </div>
      </div>
      
      <div className="space-y-3 font-mono text-xs relative z-10">
        <div className="flex justify-between border-b border-muted/10 pb-1">
          <span className="text-muted">ACTION</span>
          <span className="text-signal font-bold">{activeEvent.mcp_tool || 'create_order'}</span>
        </div>
        <div className="flex justify-between border-b border-muted/10 pb-1">
          <span className="text-muted">TRANSACTION</span>
          <span className="text-text">{activeEvent.intent_id}</span>
        </div>
        <div className="flex justify-between border-b border-muted/10 pb-1">
          <span className="text-muted">AGENT</span>
          <span className="text-text">{activeEvent.agent_id}</span>
        </div>
        <div className="flex justify-between border-b border-muted/10 pb-1">
          <span className="text-muted">EXPIRES</span>
          <span className="text-text">00:00:59</span>
        </div>
        <div className="flex justify-between pt-1">
          <span className="text-muted">STATUS</span>
          <span className="text-signal flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-signal rounded-full animate-pulse"></div> VALID
          </span>
        </div>
      </div>
    </div>
  );
}
