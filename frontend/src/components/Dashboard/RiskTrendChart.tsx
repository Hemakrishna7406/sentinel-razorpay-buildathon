import { useRef } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';
import { useMouseGlow } from '../../hooks/useMouseGlow';
import type { RiskTrendPoint } from '../../hooks/useDashboardData';

interface RiskTrendChartProps {
  data: RiskTrendPoint[];
}

export function RiskTrendChart({ data }: RiskTrendChartProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const { mousePosition, isHovering } = useMouseGlow(cardRef);

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-panel border border-muted/20 rounded-lg p-3 shadow-xl backdrop-blur-xl">
        <p className="text-xs font-mono text-muted mb-2">
          {payload[0].payload.hour}
        </p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-contain" />
            <span className="text-xs text-text">
              Behavioral: {(payload[0].value * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-escalate" />
            <span className="text-xs text-text">
              Semantic: {(payload[1].value * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="relative bg-panel/60 backdrop-blur-xl border border-muted/20 rounded-2xl overflow-hidden"
    >
      {/* Mouse tracking glow */}
      {isHovering && (
        <div
          className="absolute pointer-events-none transition-opacity duration-300 z-0"
          style={{
            left: mousePosition.x,
            top: mousePosition.y,
            width: '300px',
            height: '300px',
            transform: 'translate(-50%, -50%)',
            background: 'radial-gradient(circle, rgba(76, 141, 255, 0.1) 0%, transparent 70%)',
          }}
        />
      )}

      <div className="relative z-10">
        {/* Header */}
        <div className="p-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-signal/10">
              <TrendingUp size={20} className="text-signal" />
            </div>
            <div>
              <h3 className="font-display font-bold text-lg text-text">
                Risk Trend Analysis
              </h3>
              <p className="text-xs font-mono text-muted">
                24-HOUR BEHAVIORAL PATTERN
              </p>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="px-4 pb-6">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart
              data={data}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="behavioralGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#E5484D" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#E5484D" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="semanticGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F5A623" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#F5A623" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" opacity={0.3} />
              <XAxis
                dataKey="hour"
                stroke="#6B7592"
                fontSize={11}
                fontFamily="IBM Plex Mono"
                tickLine={false}
              />
              <YAxis
                stroke="#6B7592"
                fontSize={11}
                fontFamily="IBM Plex Mono"
                tickLine={false}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="behavioral_risk"
                stroke="#E5484D"
                strokeWidth={2}
                fill="url(#behavioralGradient)"
                animationDuration={1500}
                animationBegin={200}
              />
              <Area
                type="monotone"
                dataKey="semantic_risk"
                stroke="#F5A623"
                strokeWidth={2}
                fill="url(#semanticGradient)"
                animationDuration={1500}
                animationBegin={400}
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-contain" />
              <span className="text-xs font-mono text-muted">Behavioral Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-escalate" />
              <span className="text-xs font-mono text-muted">Semantic Risk</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
