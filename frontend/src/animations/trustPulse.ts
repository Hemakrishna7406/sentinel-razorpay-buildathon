import { gsap, ScrollTrigger } from "./gsap";

export function setupDriftPulse(driftSection: HTMLElement, onUpdateProgress: (progress: number) => void) {
  return ScrollTrigger.create({
    trigger: driftSection,
    start: "top bottom",
    end: "bottom top",
    scrub: true,
    onUpdate: (self) => {
      onUpdateProgress(self.progress);
    },
  });
}

export function interpolatePulseValues(progress: number) {
  // progress goes 0 to 1 as drift section passes
  const amplitude = gsap.utils.interpolate(1, 3.5, progress);
  const color = gsap.utils.interpolate("#4C8DFF", "#E5484D", progress);
  return { amplitude, color };
}
