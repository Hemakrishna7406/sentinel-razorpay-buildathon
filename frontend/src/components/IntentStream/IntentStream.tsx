import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import type { EvaluationResult } from '../../types';

interface IntentStreamProps {
  latestMessage: EvaluationResult | null;
  isAnomalous: boolean;
}

export function IntentStream({ latestMessage, isAnomalous }: IntentStreamProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const coreRef = useRef<HTMLDivElement>(null);
  const ringsRef = useRef<HTMLDivElement[]>([]);

  // Initial setup animation
  useEffect(() => {
    if (!containerRef.current) return;

    gsap.to(ringsRef.current, {
      scale: 2,
      opacity: 0,
      duration: 3,
      stagger: {
        each: 1,
        repeat: -1,
      },
      ease: "none",
    });

    gsap.to(coreRef.current, {
      scale: 1.05,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut"
    });
  }, []);

  // React to incoming messages
  useEffect(() => {
    if (!latestMessage || !containerRef.current) return;

    // Spawn a particle that flies into the core
    const particle = document.createElement('div');
    particle.className = `absolute w-3 h-3 rounded-full ${
      isAnomalous ? 'bg-contain shadow-[0_0_15px_rgba(229,72,77,0.8)]' : 'bg-signal shadow-[0_0_10px_rgba(76,141,255,0.6)]'
    }`;
    
    // Start from a random edge
    const angle = Math.random() * Math.PI * 2;
    const distance = 200;
    const startX = Math.cos(angle) * distance;
    const startY = Math.sin(angle) * distance;
    
    gsap.set(particle, { x: startX, y: startY, opacity: 0 });
    containerRef.current.appendChild(particle);

    // Animate into core
    gsap.to(particle, {
      x: 0,
      y: 0,
      opacity: 1,
      duration: 0.6,
      ease: "power2.in",
      onComplete: () => {
        // Core impact effect
        gsap.to(coreRef.current, {
          scale: isAnomalous ? 1.4 : 1.2,
          backgroundColor: isAnomalous ? '#E5484D' : '#4C8DFF',
          duration: 0.1,
          yoyo: true,
          repeat: 1,
          onComplete: () => {
             gsap.to(coreRef.current, { backgroundColor: 'transparent', duration: 0.5 });
          }
        });

        // Flash rings if anomalous
        if (isAnomalous) {
           gsap.to(ringsRef.current, {
             borderColor: 'rgba(229,72,77,0.5)',
             duration: 0.1,
             yoyo: true,
             repeat: 3,
             onComplete: () => {
               gsap.to(ringsRef.current, { borderColor: 'rgba(76,141,255,0.2)', duration: 1 });
             }
           });
        }
        
        particle.remove();
      }
    });

  }, [latestMessage, isAnomalous]);

  return (
    <div ref={containerRef} className="absolute inset-0 flex items-center justify-center overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
      
      {/* Expanding Radar Rings */}
      {[0, 1, 2].map((i) => (
        <div 
          key={i}
          ref={(el) => { if (el) ringsRef.current[i] = el; }}
          className="absolute w-32 h-32 rounded-full border border-signal/20 opacity-0"
        />
      ))}
      
      {/* Core Sentinel Node */}
      <div 
        ref={coreRef}
        className={`relative z-10 w-24 h-24 rounded-full border-2 ${
          isAnomalous ? 'border-contain/80 bg-contain/10' : 'border-signal/50 bg-signal/5'
        } backdrop-blur-sm flex items-center justify-center transition-colors duration-300`}
      >
        <div className={`w-12 h-12 rounded-full border border-dashed ${
          isAnomalous ? 'border-contain' : 'border-signal/70'
        } animate-[spin_4s_linear_infinite]`} />
      </div>

      {/* Status Text overlay */}
      <div className={`absolute bottom-6 font-mono text-sm tracking-widest ${
        isAnomalous ? 'text-contain font-bold drop-shadow-[0_0_8px_rgba(229,72,77,0.8)]' : 'text-signal/70'
      }`}>
        {isAnomalous ? 'THREAT INTERCEPTED' : (latestMessage ? `ANALYZING: ${latestMessage.action.toUpperCase()}` : 'AWAITING PAYLOAD')}
      </div>
    </div>
  );
}
