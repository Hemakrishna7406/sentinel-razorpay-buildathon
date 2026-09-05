import { useEffect, useRef, useState } from 'react';
import { useInView, motion, useSpring, useTransform } from 'framer-motion';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  formatFn?: (value: number) => string;
  className?: string;
}

export default function AnimatedCounter({
  value,
  duration = 1.5,
  formatFn,
  className = '',
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const [displayValue, setDisplayValue] = useState('0');

  const spring = useSpring(0, {
    duration: duration * 1000,
    bounce: 0,
  });

  const rounded = useTransform(spring, (latest) => {
    if (formatFn) return formatFn(latest);
    if (latest >= 1_000_000_000) return `${(latest / 1_000_000_000).toFixed(1)}B`;
    if (latest >= 1_000_000) return `${(latest / 1_000_000).toFixed(1)}M`;
    if (latest >= 1_000) return `${(latest / 1_000).toFixed(1)}K`;
    return Math.round(latest).toLocaleString();
  });

  useEffect(() => {
    if (isInView) {
      spring.set(value);
    }
  }, [isInView, value, spring]);

  useEffect(() => {
    const unsubscribe = rounded.on('change', (v) => setDisplayValue(v));
    return unsubscribe;
  }, [rounded]);

  return (
    <motion.span
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 10 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4 }}
    >
      {displayValue}
    </motion.span>
  );
}
