import { useState, useEffect } from 'react';
import type { SentinelExecutionEvent } from '../../hooks/useExecutionStream';
import { Server, ShieldCheck, Clock } from 'lucide-react';

export function MCPStatus({ activeEvent }: { activeEvent: SentinelExecutionEvent | null }) {
  const [providerInfo, setProviderInfo] = useState<any>(null);

  useEffect(() => {
    fetch('/execution/provider')
      .then(res => res.json())
      .then(data => setProviderInfo(data))
      .catch(console.error);
  }, []);

  const hasExecuted = activeEvent?.stage === 'RAZORPAY';

  return (
    <div className="bg-panel border border-muted/20 rounded-xl overflow-hidden flex flex-col h-full">
      <div className="bg-ink p-4 border-b border-muted/20 flex justify-between items-center">
        <h3 className="font-display font-bold text-text flex items-center gap-2">
          <Server size={18} className="text-purple-400" /> MCP CONNECTION
        </h3>
        <div className="flex items-center gap-1.5 font-mono text-[10px] bg-purple-500/10 text-purple-400 px-2 py-1 rounded border border-purple-500/20">
          <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse"></div>
          {providerInfo?.status || 'CONNECTED'}
        </div>
      </div>
      
      <div className="p-4 grid grid-cols-2 gap-4 flex-1">
        <div className="space-y-1">
          <div className="text-[10px] font-mono text-muted uppercase">Transport</div>
          <div className="text-sm font-medium text-text">{providerInfo?.transport || 'Streamable HTTP'}</div>
        </div>
        <div className="space-y-1">
          <div className="text-[10px] font-mono text-muted uppercase">Environment</div>
          <div className="text-sm font-medium text-text">{providerInfo?.environment?.toUpperCase() || 'TEST'}</div>
        </div>
        <div className="space-y-1">
          <div className="text-[10px] font-mono text-muted uppercase">Protocol</div>
          <div className="text-sm font-medium text-text">2025-06-18</div>
        </div>
        <div className="space-y-1">
          <div className="text-[10px] font-mono text-muted uppercase">Tools Discovered</div>
          <div className="text-sm font-medium text-text">{providerInfo?.available_tools || 42}</div>
        </div>
        <div className="space-y-1">
          <div className="text-[10px] font-mono text-muted uppercase">Sentinel Allowlist</div>
          <div className="text-sm font-medium text-text">2</div>
        </div>
      </div>

      {hasExecuted && (
        <div className="p-4 bg-purple-500/5 border-t border-purple-500/20 animate-in fade-in slide-in-from-bottom-2">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-mono text-purple-400 font-bold flex items-center gap-1">
              <ShieldCheck size={14} /> LAST EXECUTION
            </span>
            <span className="text-xs font-mono text-muted flex items-center gap-1">
              <Clock size={12} /> {activeEvent.latency_ms || 0} ms
            </span>
          </div>
          
          <div className="space-y-2 font-mono text-[10px]">
             <div className="flex justify-between border-b border-muted/10 pb-1">
               <span className="text-muted">Tool</span>
               <span className="text-text">{activeEvent.mcp_tool}</span>
             </div>
             <div className="flex justify-between border-b border-muted/10 pb-1">
               <span className="text-muted">Result</span>
               <span className="text-signal">{activeEvent.execution_status}</span>
             </div>
             <div className="flex justify-between pt-1">
               <span className="text-muted">Razorpay ID</span>
               <span className="text-purple-300 font-bold">{activeEvent.provider_reference}</span>
             </div>
          </div>
        </div>
      )}
    </div>
  );
}
