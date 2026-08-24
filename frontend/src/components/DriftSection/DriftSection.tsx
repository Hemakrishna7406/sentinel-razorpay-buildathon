import gsap from 'gsap';
import { useRef } from 'react';
import { useGSAP } from '../../animations/gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import type { TrustPulseRef } from '../TrustPulse/TrustPulse';
import { interpolatePulseValues } from '../../animations/trustPulse';

export default function DriftSection({ pulseRef }: { pulseRef: React.RefObject<TrustPulseRef | null> }) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const driftCardRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    ScrollTrigger.create({
      trigger: sectionRef.current,
      start: "top top",
      end: "+=150%", // Longer pin for drama
      pin: contentRef.current,
      pinSpacing: true,
      scrub: true,
      onUpdate: (self) => {
        // Only deform if pulse is hooked up
        if (pulseRef.current) {
          const { amplitude, color } = interpolatePulseValues(self.progress);
          pulseRef.current.setAmplitude(amplitude);
          pulseRef.current.setColor(color);
        }
      }
    });
    
    // Animate content entrance
    gsap.fromTo(driftCardRef.current, 
      { opacity: 0, scale: 0.98, y: 30 },
      {
        opacity: 1, 
        scale: 1,
        y: 0,
        ease: "cubic-bezier(0.23, 1, 0.32, 1)",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 70%",
          end: "top 40%",
          scrub: true,
        }
      }
    );
  }, { scope: sectionRef });

  return (
    <section ref={sectionRef} className="h-[250vh] w-full relative border-t border-panel bg-ink">
      <div ref={contentRef} className="h-screen w-full flex flex-col items-center justify-center px-6 pointer-events-none">
        
        {/* We place the card higher so the TrustPulse below can visually deform wildly */}
        <div ref={driftCardRef} className="max-w-4xl w-full flex flex-col md:flex-row gap-12 items-center pointer-events-auto">
          
          <div className="flex-1 space-y-6">
            <div className="inline-block px-3 py-1 border border-drift/30 rounded-full font-mono text-xs text-drift">
              03 // THE DRIFT
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-text">
              When Behavior <br/> Breaks Pattern
            </h2>
            <p className="text-muted text-lg">
              Sentinel detects when semantic meaning deviates from historical boundaries. As risk increases, the waveform deforms instantly.
            </p>
          </div>

          <div className="flex-1 bg-panel border border-drift/40 rounded-xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-drift"></div>
            <div className="space-y-4 font-mono text-sm">
              <div className="flex justify-between items-center border-b border-muted/20 pb-2">
                <span className="text-muted">RISK SCORE</span>
                <span className="text-drift font-bold text-lg">94%</span>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted">Confidence</span>
                  <span className="text-drift">HIGH ANOMALY</span>
                </div>
                <div className="flex justify-between text-muted border-t border-muted/20 pt-2 mt-2">
                  <span>&gt; Unseen payout target</span>
                </div>
                <div className="flex justify-between text-muted">
                  <span>&gt; Velocity breach (3x avg)</span>
                </div>
                <div className="flex justify-between text-muted">
                  <span>&gt; Bypassed approval steps</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
