import gsap from 'gsap';
import { useRef } from 'react';
import { useGSAP } from '../../animations/gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

export default function AgentSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // Pin the content while scrolling through the section
    ScrollTrigger.create({
      trigger: sectionRef.current,
      start: "top top",
      end: "+=100%", // Pin for 1 viewport height of scrolling
      pin: contentRef.current,
      pinSpacing: true,
      scrub: true,
    });
    
    // Fade in elements smoothly as it enters
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
        }
      }
    );
  }, { scope: sectionRef });

  return (
    <section ref={sectionRef} className="h-[200vh] w-full relative border-t border-panel bg-ink">
      <div ref={contentRef} className="h-screen w-full flex flex-col items-center justify-center px-6">
        <div className="max-w-4xl w-full flex flex-col md:flex-row gap-12 items-center">
          
          <div className="flex-1 space-y-6">
            <div className="inline-block px-3 py-1 border border-muted/30 rounded-full font-mono text-xs text-muted">
              01 // THE AGENT
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-text">
              Speed Without <br/> Supervision
            </h2>
            <p className="text-muted text-lg">
              Autonomous agents execute transactions at machine speed. They navigate APIs, negotiate prices, and move money in milliseconds.
            </p>
          </div>

          <div className="flex-1 bg-panel/50 border border-panel rounded-xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-signal/20 to-signal/80"></div>
            <div className="space-y-4 font-mono text-sm">
              <div className="flex justify-between items-center border-b border-muted/20 pb-2">
                <span className="text-muted">STATUS</span>
                <span className="text-signal flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-signal animate-pulse"></span>
                  EXECUTING
                </span>
              </div>
              <div className="space-y-2 text-muted">
                <p>&gt; Analyzing vendor invoice INV-8492...</p>
                <p>&gt; Vendor matched: Razorpay Merchants</p>
                <p className="text-text">&gt; PROPOSING PAYOUT: $14,500.00</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
