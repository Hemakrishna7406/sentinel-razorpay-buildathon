import { useRef } from 'react';
import { useGSAP, gsap } from '../../animations/gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { animateCounter } from '../../animations/counters';

export default function DecisionSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const counterRef = useRef<HTMLSpanElement>(null);

  useGSAP(() => {
    ScrollTrigger.create({
      trigger: sectionRef.current,
      start: "top top",
      end: "+=100%",
      pin: contentRef.current,
      pinSpacing: true,
      scrub: true,
    });
    
    gsap.fromTo(contentRef.current, 
      { opacity: 0, scale: 0.98 },
      {
        opacity: 1, 
        scale: 1,
        ease: "cubic-bezier(0.23, 1, 0.32, 1)",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 70%",
          end: "top 30%",
          scrub: true,
          onEnter: () => {
            if (counterRef.current) {
              animateCounter(counterRef.current, 12, false);
            }
          }
        }
      }
    );
  }, { scope: sectionRef });

  return (
    <section ref={sectionRef} className="h-[200vh] w-full relative border-t border-panel bg-ink">
      <div ref={contentRef} className="h-screen w-full flex flex-col items-center justify-center px-6">
        <div className="max-w-4xl w-full flex flex-col md:flex-row gap-12 items-center">
          
          <div className="flex-1 space-y-6">
            <div className="inline-block px-3 py-1 border border-contain/30 rounded-full font-mono text-xs text-contain">
              04 // DECISION
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-text">
              Zero-Trust <br/> Verification
            </h2>
            <p className="text-muted text-lg">
              Sentinel isolates the transaction, forcing the agent to cryptographically prove its intent before execution is permitted.
            </p>
          </div>

          <div className="flex-1 bg-panel border border-contain/40 rounded-xl p-8 shadow-2xl relative overflow-hidden w-full">
            <div className="absolute top-0 left-0 w-full h-1 bg-contain"></div>
            <div className="space-y-6 font-mono text-sm">
              <div className="flex justify-between items-center border-b border-muted/20 pb-2">
                <span className="text-muted">EVALUATION TIME</span>
                <span className="text-contain"><span ref={counterRef}>0</span>ms</span>
              </div>
              
              <div className="space-y-4">
                <div className="p-3 bg-ink/50 border border-muted/20 rounded">
                  <div className="flex justify-between mb-1">
                    <span className="text-muted">Policy: Vendor Allowlist</span>
                    <span className="text-contain">FAILED</span>
                  </div>
                  <div className="w-full bg-ink rounded-full h-1">
                    <div className="bg-contain h-1 rounded-full w-full"></div>
                  </div>
                </div>

                <div className="p-3 bg-ink/50 border border-muted/20 rounded">
                  <div className="flex justify-between mb-1">
                    <span className="text-muted">Policy: Velocity Limits</span>
                    <span className="text-contain">FAILED</span>
                  </div>
                  <div className="w-full bg-ink rounded-full h-1">
                    <div className="bg-contain h-1 rounded-full w-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
