import { useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface MagneticButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export default function MagneticButton({
  children,
  className = '',
  onClick,
  variant = 'primary'
}: MagneticButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!buttonRef.current) return;

    const rect = buttonRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    setPosition({ x: x * 0.3, y: y * 0.3 });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  const baseClasses = variant === 'primary'
    ? 'bg-sentinel text-white hover:bg-sentinel-bright shadow-lg hover:shadow-sentinel/50'
    : 'border border-border-light text-text-primary hover:bg-background-elevated hover:border-sentinel/50';

  return (
    <motion.button
      ref={buttonRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 150, damping: 15, mass: 0.1 }}
      className={`px-6 py-3 font-semibold rounded-lg transition-all duration-300 flex items-center gap-2 relative overflow-hidden group ${baseClasses} ${className}`}
    >
      {/* Glow effect on hover */}
      {variant === 'primary' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-sentinel-bright via-sentinel to-sentinel-deep opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          style={{ filter: 'blur(8px)' }}
        />
      )}
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
}
