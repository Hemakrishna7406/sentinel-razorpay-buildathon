import React, { useRef, useLayoutEffect } from 'react';
import { setupLandingChoreography } from '../../animations/landingScenes';
import TrustPulse from '../../components/TrustPulse/TrustPulse';
import { ShieldAlert, ArrowDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const containerRef = useRef<HTMLDivElement>(null);
  const signalRef = useRef<HTMLDivElement>(null);
  const pulseRef = useRef<any>(null);
  const navigate = useNavigate();

  useLayoutEffect(() => {
    if (!containerRef.current) return;
    const ctx = setupLandingChoreography(containerRef.current, signalRef, pulseRef);
    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="bg-ink min-h-[700vh] relative overflow-hidden text-text font-sans">
      
      {/* The Central Signal */}
      <div 
        ref={signalRef}
        className="fixed left-1/2 top-10 w-4 h-4 -ml-2 rounded-full bg-signal shadow-[0_0_20px_#4C8DFF] z-50 pointer-events-none"
      />

      {/* Zero-Trust Boundary Marker (Visible only in later scenes) */}
      <div className="fixed left-1/2 top-[88vh] w-32 -ml-16 h-1 bg-contain/50 shadow-[0_0_15px_rgba(229,72,77,0.5)] z-40" />

      {/* Scene 1: WHY? */}
      <section id="scene-1" className="h-screen flex items-center justify-center relative">
        <div className="scene-1-text opacity-0 translate-y-12 text-center max-w-3xl px-6">
          <h1 className="text-6xl font-display font-bold mb-6 tracking-tight">Authorized doesn't mean safe.</h1>
          <p className="text-xl text-muted">An AI agent can stay perfectly within its permissions while its behavior drifts into critical risk.</p>
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 animate-bounce opacity-50">
            <ArrowDown size={32} />
          </div>
        </div>
      </section>

      {/* Scene 2: WHAT? */}
      <section id="scene-2" className="h-screen flex items-center justify-start pl-20 relative">
        <div className="max-w-xl">
          <div className="text-signal font-mono text-xs mb-2">02 // PROFILING</div>
          <h2 className="text-5xl font-display font-bold mb-4">Know the Agent</h2>
          <p className="text-lg text-muted">Sentinel continuously profiles baseline behavior. We don't just look at what the agent is doing, we look at how it usually behaves.</p>
        </div>
      </section>

      {/* Scene 3: HOW? */}
      <section id="scene-3" className="h-screen flex items-center justify-end pr-20 relative">
        <div className="max-w-xl text-right">
          <div className="text-signal font-mono text-xs mb-2">03 // DETECTION</div>
          <h2 className="text-5xl font-display font-bold mb-4">Detect the Drift</h2>
          <p className="text-lg text-muted">Dual-engine risk fusion analyzes contextual anomalies and semantic deviations in milliseconds.</p>
          <div className="mt-8 opacity-20 pointer-events-none">
             <TrustPulse amplitude={0.1} />
          </div>
        </div>
      </section>

      {/* Scene 4: DECISION */}
      <section id="scene-4" className="h-screen flex items-center justify-start pl-20 relative">
        <div className="max-w-xl">
          <div className="text-signal font-mono text-xs mb-2">04 // DECISION</div>
          <h2 className="text-5xl font-display font-bold mb-4">Risk meets Policy</h2>
          <p className="text-lg text-muted">Natural language policies define the acceptable bounds of agent autonomy. When behavior drifts, policy enforces containment.</p>
        </div>
      </section>

      {/* Scene 5: AUTHORIZATION */}
      <section id="scene-5" className="h-screen flex items-center justify-end pr-20 relative">
        <div className="max-w-xl text-right">
          <div className="text-signal font-mono text-xs mb-2">05 // AUTHORIZATION</div>
          <h2 className="text-5xl font-display font-bold mb-4">Exact-Action Capabilities</h2>
          <p className="text-lg text-muted">A dynamic capability token is issued, cryptographically locking the authorized Razorpay Tool, amount, and recipient.</p>
        </div>
      </section>

      {/* Scene 6: CONTAINMENT */}
      <section id="scene-6" className="h-screen flex items-center justify-center relative">
         <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
           <TrustPulse amplitude={1.0} />
         </div>
         
         <div className="contain-text opacity-0 scale-50 text-center relative z-20">
           <ShieldAlert size={80} className="text-contain mx-auto mb-6" />
           <h2 className="text-7xl font-display font-bold text-contain mb-4">MCP CALLS: 0</h2>
           <p className="text-2xl text-contain/80">The Zero-Trust Boundary halts execution.</p>
           <p className="text-lg text-muted mt-2">Financial mutation is prevented before it reaches Razorpay.</p>
         </div>
      </section>

      {/* Scene 7: PROOF */}
      <section id="scene-7" className="h-screen flex flex-col items-center justify-center relative">
         <div className="text-center max-w-3xl px-6 mb-12">
           <h2 className="text-5xl font-display font-bold mb-6">Real Test Execution.</h2>
           <p className="text-xl text-muted">See Sentinel orchestrate the zero-trust boundary live.</p>
         </div>
         <button 
           onClick={() => navigate('/dashboard')}
           className="px-8 py-4 bg-signal text-ink font-bold font-display rounded-lg text-xl hover:bg-signal/90 transition-transform hover:scale-105"
         >
           Enter Control Room
         </button>
      </section>

    </div>
  );
}
