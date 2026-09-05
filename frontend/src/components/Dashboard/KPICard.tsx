import { useRef } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { useMouseGlow } from '../../hooks/useMouseGlow';
import { useAnimatedCounter } from '../../hooks/useAnimatedCounter';

interface KPICardProps {
  title: string;
  value: number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'signal' | 'allow' | 'contain' | 'escalate';
  delay?: number;
  format?: 'number' | 'percentage' | 'milliseconds';
}

const colorClasses = {
  signal: {
    icon: 'text-signal',
    glow: 'rgba(76, 141, 255, 0.15)',
    border: 'border-signal/20',
  },
  allow: {
    icon: 'text-allow',
    glow: 'rgba(16, 185, 129, 0.15)',
    border: 'border-allow/20',
  },
  contain: {
    icon: 'text-contain',
    glow: 'rgba(229, 72, 77, 0.15)',
    border: 'border-contain/20',
  },
  escalate: {
    icon: 'text-escalate',
    glow: 'rgba(245, 166, 35, 0.15)',
    border: 'border-escalate/20',
  },
};

export function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  color = 'signal',
  delay = 0,
  format = 'number',
}: KPICardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const { mousePosition, isHovering } = useMouseGlow(cardRef);
  const animatedValue = useAnimatedCounter(value, 1200, delay);

  const formatValue = (val: number) => {
    switch (format) {
      case 'percentage':
        return `${val.toFixed(1)}%`;
      case 'milliseconds':
        return `${val}ms`;
      default:
        return val.toLocaleString();
    }
  };

  const colors = colorClasses[color];

  const hoverBorderClass = {
    signal: 'hover:border-signal/40',
    allow: 'hover:border-allow/40',
    contain: 'hover:border-contain/40',
    escalate: 'hover:border-escalate/40',
  }[color];

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: delay / 1000 }}
      className={`relative bg-panel/60 backdrop-blur-xl border ${colors.border} ${hoverBorderClass} rounded-2xl p-6 overflow-hidden group transition-colors`}
    >
      {/* Mouse tracking glow effect */}
      {isHovering && (
        <div
          className="absolute pointer-events-none transition-opacity duration-300"
          style={{
            left: mousePosition.x,
            top: mousePosition.y,
            width: '300px',
            height: '300px',
            transform: 'translate(-50%, -50%)',
            background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
          }}
        />
      )}

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl ${colors.icon}`} style={{ backgroundColor: colors.glow }}>
            <Icon size={24} />
          </div>
          {trend && trendValue && (
            <div
              className={`text-xs font-mono px-2 py-1 rounded-full ${
                trend === 'up'
                  ? 'bg-allow/10 text-allow'
                  : trend === 'down'
                  ? 'bg-contain/10 text-contain'
                  : 'bg-muted/10 text-muted'
              }`}
            >
              {trendValue}
            </div>
          )}
        </div>

        {/* Value */}
        <div className="mb-2">
          <motion.div
            className="text-4xl font-display font-bold text-text"
            initial={{ scale: 0.5 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: delay / 1000 + 0.2 }}
          >
            {formatValue(animatedValue)}
          </motion.div>
        </div>

        {/* Title & Subtitle */}
        <div>
          <div className="text-sm font-medium text-text mb-1">{title}</div>
          {subtitle && (
            <div className="text-xs font-mono text-muted uppercase">
              {subtitle}
            </div>
          )}
        </div>
      </div>

      {/* Glassmorphism overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
    </motion.div>
  );
}
