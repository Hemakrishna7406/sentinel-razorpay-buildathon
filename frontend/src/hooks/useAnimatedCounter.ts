import { useEffect, useState, useRef } from 'react';

export function useAnimatedCounter(
  target: number,
  duration: number = 1000,
  delay: number = 0
) {
  const [count, setCount] = useState(0);
  const frameRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      const startValue = count;
      const startTime = Date.now();
      startTimeRef.current = startTime;

      const animate = () => {
        const now = Date.now();
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (easeOutCubic)
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const currentCount = startValue + (target - startValue) * easeProgress;

        setCount(Math.floor(currentCount));

        if (progress < 1) {
          frameRef.current = requestAnimationFrame(animate);
        } else {
          setCount(target);
        }
      };

      frameRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(timeoutId);
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [target, duration, delay]);

  return count;
}
