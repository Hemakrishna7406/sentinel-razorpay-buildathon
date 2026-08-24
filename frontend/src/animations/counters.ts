import { gsap } from "./gsap";

export function animateCounter(element: HTMLElement, finalValue: number, formatString?: boolean) {
  const obj = { value: 0 };
  
  return gsap.to(obj, {
    value: finalValue,
    duration: 1.5,
    ease: "power2.out",
    scrollTrigger: {
      trigger: element,
      start: "top 75%",
      once: true,
    },
    onUpdate: () => {
      if (formatString) {
        element.innerText = obj.value.toFixed(1) + "%";
      } else {
        element.innerText = obj.value.toFixed(3);
      }
    }
  });
}
