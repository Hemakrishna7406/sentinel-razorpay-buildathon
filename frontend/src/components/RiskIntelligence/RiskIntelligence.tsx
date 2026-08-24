import { SentinelExecutionEvent } from '../../hooks/useExecutionStream';
import { Activity, ShieldAlert, Cpu } from 'lucide-react';

export function RiskIntelligence({ activeEvent }: { activeEvent: SentinelExecutionEvent | null }) {
  const isHighRisk = (activeEvent?.behavioral_risk ?? 0) > 0.8;

  return (
    <div className="bg-panel border border-muted/20 p-5 rounded-xl flex flex-col justify-between h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-display font-bold text-text text-lg flex items-center gap-2">
          <Cpu size={18} className="text-signal" /> Risk Intelligence
        </h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Behavioral Engine */}
        <div className={`p-4 rounded-lg border ${isHighRisk ? 'border-contain/30 bg-contain/5' : 'border-muted/10 bg-ink'}`}>
           <div className="flex justify-between items-start mb-2">
             <div className="text-xs font-mono text-muted uppercase">Behavioral Engine</div>
             <div className="flex items-center gap-1.5 font-mono text-[10px] text-signal bg-signal/10 px-2 py-0.5 rounded">
               <div className="w-1.5 h-1.5 bg-signal rounded-full"></div> ACTIVE
             </div>
           </div>
           <div className="font-medium text-text mb-1">XGBoost</div>
           <div className="flex justify-between items-end">
             <div className="text-xs text-muted">v3.1</div>
             <div className={`text-2xl font-display font-bold ${isHighRisk ? 'text-contain' : 'text-signal'}`}>
               {activeEvent?.behavioral_risk?.toFixed(2) || '0.00'}
             </div>
           </div>
        </div>

        {/* Semantic Engine */}
        <div className="p-4 rounded-lg border border-muted/10 bg-ink">
           <div className="flex justify-between items-start mb-2">
             <div className="text-xs font-mono text-muted uppercase">Semantic Engine</div>
             <div className="flex items-center gap-1.5 font-mono text-[10px] text-drift bg-drift/10 px-2 py-0.5 rounded">
               <div className="w-1.5 h-1.5 bg-drift rounded-full"></div> SIMULATED
             </div>
           </div>
           <div className="font-medium text-text mb-1">Semantic Provider</div>
           <div className="flex justify-between items-end">
             <div className="text-xs text-muted">sim-v1</div>
             <div className="text-2xl font-display font-bold text-text">
               {activeEvent?.semantic_risk?.toFixed(2) || '0.00'}
             </div>
           </div>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-muted/10 flex justify-between items-center">
         <span className="text-xs font-mono text-muted uppercase">Dual-Engine Fusion</span>
         <span className={`text-sm font-bold flex items-center gap-2 ${isHighRisk ? 'text-contain' : 'text-signal'}`}>
           {isHighRisk ? <ShieldAlert size={16} /> : <Activity size={16} />}
           {isHighRisk ? 'HIGH RISK DETECTED' : 'LOW RISK'}
         </span>
      </div>
    </div>
  );
}
