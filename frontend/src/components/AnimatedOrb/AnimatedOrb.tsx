import { motion } from 'framer-motion';

interface AnimatedOrbProps {
  color: string;
  size: number;
  duration: number;
  delay?: number;
  className?: string;
}

export default function AnimatedOrb({
  color,
  size,
  duration,
  delay = 0,
  className = ''
}: AnimatedOrbProps) {
  return (
    <motion.div
      className={`absolute rounded-full blur-3xl ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: color,
      }}
      animate={{
        x: [0, 100, -50, 0],
        y: [0, -50, 100, 0],
        scale: [1, 1.2, 0.8, 1],
        opacity: [0.3, 0.6, 0.4, 0.3],
      }}
      transition={{
        duration,
        delay,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  );
}
