import { useRef } from 'react';
import { useGSAP, gsap } from '../../animations/gsap';
import { Link } from 'react-router-dom';

export default function ContainmentSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.fromTo(contentRef.current, 
      { opacity: 0, y: 50 },
      {
        opacity: 1, 
        y: 0,
        ease: "cubic-bezier(0.23, 1, 0.32, 1)",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 60%",
          end: "top 20%",
          scrub: true,
        }
      }
    );
  }, { scope: sectionRef });

  return (
    <section ref={sectionRef} className="py-32 w-full relative border-t border-contain/30 bg-ink flex justify-center px-6">
      <div ref={contentRef} className="max-w-3xl w-full text-center space-y-8 py-16">
        <div className="inline-block px-3 py-1 border border-contain/30 rounded-full font-mono text-xs text-contain mb-4">
          05 // CONTAINMENT
        </div>
        <h2 className="font-display text-5xl md:text-6xl text-text font-bold">
          Risk Isolated. <br/> Money Secured.
        </h2>
        <p className="text-muted text-xl max-w-xl mx-auto">
          The payload is dropped. The agent is paused. Human operators are alerted with a full semantic audit log.
        </p>
        
        <div className="pt-8">
          <Link to="/dashboard" className="inline-block bg-text text-ink px-8 py-4 rounded-lg font-mono tracking-widest text-sm font-bold btn-interactive hover:bg-white shadow-[0_0_30px_rgba(232,236,247,0.15)]">
            ENTER SENTINEL DASHBOARD
          </Link>
        </div>
      </div>
    </section>
  );
}
