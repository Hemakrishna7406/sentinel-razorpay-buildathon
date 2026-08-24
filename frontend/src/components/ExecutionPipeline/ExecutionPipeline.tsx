import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import type { SentinelExecutionEvent, ExecutionStage } from '../../hooks/useExecutionStream';
import { CheckCircle2, XCircle, Clock, ShieldAlert } from 'lucide-react';

const STAGES: ExecutionStage[] = ['INTENT', 'BEHAVIOR', 'POLICY', 'CAPABILITY', 'MCP', 'RAZORPAY'];

export function ExecutionPipeline({ activeEvent }: { activeEvent: SentinelExecutionEvent | null }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const signalRef = useRef<HTMLDivElement>(null);

  // GSAP animation logic
  useEffect(() => {
    if (!activeEvent || !signalRef.current) return;

    const currentStageIndex = STAGES.indexOf(activeEvent.stage);
    if (currentStageIndex === -1) return;

    // Calculate percentage based on nodes. 5 intervals between 6 nodes.
    const percentage = (currentStageIndex / (STAGES.length - 1)) * 100;
    
    gsap.to(signalRef.current, {
      left: `${percentage}%`,
      duration: 0.5,
      ease: 'power2.out',
    });

  }, [activeEvent]);

  const renderStatusIcon = (stage: ExecutionStage) => {
    if (!activeEvent) return <Clock className="text-muted/30" size={16} />;
    
    const stageIndex = STAGES.indexOf(stage);
    const currentIndex = STAGES.indexOf(activeEvent.stage);
    
    if (stageIndex > currentIndex) {
      return <Clock className="text-muted/30" size={16} />;
    }
    
    if (stage === 'POLICY' && activeEvent.policy_decision === 'CONTAIN') {
      return <ShieldAlert className="text-contain" size={16} />;
    }
    if (stage === 'MCP' && activeEvent.execution_status === 'BLOCKED') {
      return <XCircle className="text-contain" size={16} />;
    }
    
    if (stageIndex <= currentIndex) {
      return <CheckCircle2 className="text-signal" size={16} />;
    }
    return null;
  };

  return (
    <div className="bg-panel border border-muted/20 p-6 rounded-xl" ref={containerRef}>
      <h2 className="font-display font-bold text-lg text-text mb-8">Zero-Trust Execution Pipeline</h2>
      
      <div className="relative pt-6 pb-2">
        {/* The Track */}
        <div className="absolute top-10 left-4 right-4 h-1 bg-ink rounded-full overflow-hidden border border-muted/10">
           {/* Boundary Marker */}
           <div className="absolute left-[80%] top-0 bottom-0 w-1 bg-contain/50 z-10" />
        </div>

        {/* The Signal (Animated) */}
        <div 
          ref={signalRef}
          className="absolute top-9 w-3 h-3 bg-signal rounded-full shadow-[0_0_15px_#4C8DFF] z-20 -ml-1.5 transition-shadow"
          style={{ left: '0%' }}
        />

        <div className="flex justify-between relative z-30">
          {STAGES.map((stage, idx) => {
            const isActive = activeEvent?.stage === stage;
            const isPast = activeEvent && STAGES.indexOf(activeEvent.stage) >= idx;
            const isBlocked = activeEvent && ['CONTAIN', 'ESCALATE'].includes(activeEvent.policy_decision || '') && idx > STAGES.indexOf('POLICY');

            return (
              <div key={stage} className={`flex flex-col items-center w-24 gap-3 ${isBlocked ? 'opacity-20' : ''}`}>
                <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center bg-panel transition-colors duration-300
                  ${isActive ? 'border-signal shadow-[0_0_20px_rgba(76,141,255,0.2)]' : isPast ? 'border-signal/50' : 'border-muted/20'}
                `}>
                  {renderStatusIcon(stage)}
                </div>
                <div className="text-center">
                  <div className={`text-xs font-mono font-bold ${isActive ? 'text-signal' : isPast ? 'text-text' : 'text-muted/50'}`}>
                    {stage}
                  </div>
                  {idx === 4 && (
                    <div className="text-[10px] text-contain mt-1 border border-contain/30 bg-contain/5 px-1 rounded">
                      ZERO-TRUST
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {activeEvent?.execution_status === 'BLOCKED' && (
        <div className="mt-8 p-4 bg-contain/10 border border-contain/30 rounded-lg flex items-center justify-between animate-in fade-in slide-in-from-bottom-2">
           <div className="flex items-center gap-3">
              <ShieldAlert className="text-contain" size={24} />
              <div>
                <div className="font-bold text-contain">Execution Blocked</div>
                <div className="text-xs font-mono text-contain/70">
                  {activeEvent.reason_codes?.join(', ') || 'Security boundary enforced.'}
                </div>
              </div>
           </div>
           <div className="text-right">
              <div className="text-xs font-mono text-muted uppercase">MCP Calls</div>
              <div className="font-display font-bold text-3xl text-text">0</div>
           </div>
        </div>
      )}
    </div>
  );
}
