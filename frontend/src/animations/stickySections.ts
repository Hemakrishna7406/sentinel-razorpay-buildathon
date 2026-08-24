import { ScrollTrigger } from "./gsap";

export function createStickySection(sectionElement: HTMLElement, visualElement: HTMLElement) {
  return ScrollTrigger.create({
    trigger: sectionElement,
    start: "top top",
    end: "bottom bottom",
    pin: visualElement,
    pinSpacing: false,
  });
}
