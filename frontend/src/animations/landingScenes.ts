import type React from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export function setupLandingChoreography(
  container: HTMLDivElement,
  signalRef: React.RefObject<HTMLDivElement | null>,
  pulseRef: React.RefObject<{ setAmplitude: (value: number) => void } | null>
) {
  const ctx = gsap.context(() => {
    
    // Scene 1: WHY?
    ScrollTrigger.create({
      trigger: "#scene-1",
      start: "top center",
      onEnter: () => {
         gsap.to(".scene-1-text", { opacity: 1, y: 0, duration: 1 });
      },
      onLeaveBack: () => {
         gsap.to(".scene-1-text", { opacity: 0, y: 50, duration: 0.5 });
      }
    });

    // Central Signal Timeline
    const signalTl = gsap.timeline({
      scrollTrigger: {
        trigger: container,
        start: "top top",
        end: "bottom bottom",
        scrub: 1,
      }
    });

    // Move signal through the pipeline down the page
    if (signalRef.current) {
      signalTl.to(signalRef.current, { y: '20vh', ease: 'none' }) // Scene 2
              .to(signalRef.current, { y: '40vh', ease: 'none' }) // Scene 3
              .to(signalRef.current, { y: '60vh', ease: 'none' }) // Scene 4
              .to(signalRef.current, { y: '80vh', ease: 'none' }) // Scene 5
              .to(signalRef.current, { y: '90vh', scale: 2, ease: 'none' }); // Scene 6 (Containment)
    }
    
    // Scene 6: Containment (Trust Pulse collapse)
    ScrollTrigger.create({
       trigger: "#scene-6",
       start: "top center",
       onEnter: () => {
          gsap.to(".contain-text", { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.7)" });
          if (pulseRef.current) {
             pulseRef.current.setAmplitude(1.0); // High risk
          }
       },
       onLeaveBack: () => {
          gsap.to(".contain-text", { opacity: 0, scale: 0.5, duration: 0.5 });
          if (pulseRef.current) {
             pulseRef.current.setAmplitude(0.1); // Nominal
          }
       }
    });

  }, container);

  return ctx;
}
