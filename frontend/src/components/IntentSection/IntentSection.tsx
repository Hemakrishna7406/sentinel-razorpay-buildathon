import gsap from 'gsap';
import { useRef } from 'react';
import { useGSAP } from '../../animations/gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

export default function IntentSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

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
        }
      }
    );
  }, { scope: sectionRef });

  return (
    <section ref={sectionRef} className="h-[200vh] w-full relative border-t border-panel bg-ink">
      <div ref={contentRef} className="h-screen w-full flex flex-col items-center justify-center px-6">
        <div className="max-w-4xl w-full flex flex-col md:flex-row-reverse gap-12 items-center">
          
          <div className="flex-1 space-y-6">
            <div className="inline-block px-3 py-1 border border-muted/30 rounded-full font-mono text-xs text-muted">
              02 // THE INTENT
            </div>
            <h2 className="font-display text-4xl md:text-5xl text-text">
              What Are They <br/> Actually Doing?
            </h2>
            <p className="text-muted text-lg">
              Sentinel intercepts the payload before execution, translating raw API calls into a semantic intent graph. 
            </p>
          </div>

          <div className="flex-1 bg-panel/50 border border-panel rounded-xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-drift/20 to-drift/80"></div>
            <div className="space-y-4 font-mono text-sm">
              <div className="flex justify-between items-center border-b border-muted/20 pb-2">
                <span className="text-muted">SENTINEL EXTRACTION</span>
                <span className="text-drift">ANALYZING</span>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted">Target Entity</span>
                  <span className="text-text">acc_9X8Y7Z</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Action</span>
                  <span className="text-text">Payout Creation</span>
                </div>
                <div className="flex justify-between border-t border-muted/20 pt-2 mt-2">
                  <span className="text-muted">Semantic Meaning</span>
                  <span className="text-drift">Transfer funds to unverified external account</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
