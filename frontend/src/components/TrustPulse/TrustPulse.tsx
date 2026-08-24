import gsap from 'gsap';
import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useGSAP } from '../../animations/gsap';

export interface TrustPulseRef {
  setAmplitude: (val: number) => void;
  setColor: (color: string) => void;
}

interface TrustPulseProps {
  amplitude?: number;
}

const TrustPulse = forwardRef<TrustPulseRef, TrustPulseProps>(({ amplitude = 0 }, ref) => {
  const pathRef = useRef<SVGPathElement>(null);
  
  // High-performance GSAP updater
  const updateAmplitude = (a: number) => {
    if (!pathRef.current) return;
    const p1 = 100 - 50 * a;
    const p2 = 100 + 50 * a;
    const newPath = `M0,100 L300,100 L320,${p1} L350,${p2} L380,100 L600,100 L620,${p1} L650,${p2} L680,100 L1000,100`;
    
    gsap.to(pathRef.current, {
      attr: { d: newPath },
      duration: 0.5,
      ease: 'power2.out',
    });
    
    gsap.to(pathRef.current, {
      stroke: a > 0.8 ? '#E5484D' : '#4C8DFF',
      duration: 0.5,
    });
  };

  useImperativeHandle(ref, () => ({
    setAmplitude: updateAmplitude,
    setColor: (color: string) => {
      if (pathRef.current) {
        gsap.to(pathRef.current, { stroke: color, duration: 0.2 });
      }
    },
  }));
  
  // Declarative React prop updater
  useEffect(() => {
    updateAmplitude(amplitude);
  }, [amplitude]);

  useGSAP(() => {
    if (pathRef.current) {
      const length = pathRef.current.getTotalLength();
      pathRef.current.style.strokeDasharray = `${length}`;
      pathRef.current.style.strokeDashoffset = `${length}`;
      
      gsap.to(pathRef.current, {
        strokeDashoffset: 0,
        duration: 3,
        ease: "none",
        repeat: -1,
      });
    }
  }, []);

  return (
    <div className="w-full h-64 flex items-center justify-center relative">
      <svg width="100%" height="100%" viewBox="0 0 1000 200" preserveAspectRatio="none">
        <path 
          ref={pathRef}
          d="M0,100 L300,100 L320,100 L350,100 L380,100 L600,100 L620,100 L650,100 L680,100 L1000,100" 
          fill="none" 
          stroke="#4C8DFF" 
          strokeWidth="3" 
          vectorEffect="non-scaling-stroke" 
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {amplitude > 0.8 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500 pointer-events-none">
           <span className="font-display font-bold text-4xl text-contain drop-shadow-[0_0_10px_rgba(229,72,77,0.8)]">28%</span>
           <span className="text-sm font-mono text-contain mt-1">TRUST COLLAPSED</span>
        </div>
      )}
      {amplitude <= 0.8 && amplitude > 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
           <span className="font-display font-bold text-4xl text-signal drop-shadow-[0_0_10px_rgba(76,141,255,0.8)]">94%</span>
           <span className="text-sm font-mono text-signal mt-1">NOMINAL BEHAVIOR</span>
        </div>
      )}
    </div>
  );
});

export default TrustPulse;
