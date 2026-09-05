import { useRef } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { useMouseGlow } from '../../hooks/useMouseGlow';
import type { RecentAlert } from '../../hooks/useDashboardData';

interface RecentAlertsProps {
  alerts: RecentAlert[];
}

const riskLevelConfig = {
  critical: {
    color: 'contain',
    icon: Shield,
    glow: 'shadow-[0_0_20px_rgba(229,72,77,0.3)]',
    border: 'border-contain/30',
    bg: 'bg-contain/5',
  },
  high: {
    color: 'contain',
    icon: AlertTriangle,
    glow: 'shadow-[0_0_15px_rgba(229,72,77,0.2)]',
    border: 'border-contain/20',
    bg: 'bg-contain/5',
  },
  medium: {
    color: 'escalate',
    icon: AlertTriangle,
    glow: '',
    border: 'border-escalate/20',
    bg: 'bg-escalate/5',
  },
  low: {
    color: 'muted',
    icon: CheckCircle2,
    glow: '',
    border: 'border-muted/10',
    bg: 'bg-ink/50',
  },
};

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const { mousePosition, isHovering } = useMouseGlow(cardRef);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
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
        <div className="p-6 pb-4 border-b border-muted/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-signal/10">
              <Shield size={20} className="text-signal" />
            </div>
            <div>
              <h3 className="font-display font-bold text-lg text-text">
                Recent Alerts
              </h3>
              <p className="text-xs font-mono text-muted">
                HIGH-PRIORITY EVENTS
              </p>
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-muted/20 scrollbar-track-transparent">
          {alerts.length === 0 ? (
            <div className="text-center py-12 text-muted text-sm">
              No recent alerts
            </div>
          ) : (
            alerts.map((alert, index) => {
              const config = riskLevelConfig[alert.risk_level];
              const Icon = config.icon;

              return (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className={`p-4 rounded-lg border ${config.border} ${config.bg} ${config.glow} transition-all hover:scale-[1.02]`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg mt-0.5" style={{
                      backgroundColor: config.color === 'contain' ? 'rgba(229, 72, 77, 0.1)' :
                                     config.color === 'escalate' ? 'rgba(245, 166, 35, 0.1)' :
                                     config.color === 'allow' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(107, 117, 146, 0.1)'
                    }}>
                      <Icon size={16} style={{
                        color: config.color === 'contain' ? '#E5484D' :
                               config.color === 'escalate' ? '#F5A623' :
                               config.color === 'allow' ? '#10B981' : '#6B7280'
                      }} />
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Header */}
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono px-2 py-0.5 rounded-full uppercase" style={{
                            backgroundColor: config.color === 'contain' ? 'rgba(229, 72, 77, 0.1)' :
                                           config.color === 'escalate' ? 'rgba(245, 166, 35, 0.1)' :
                                           config.color === 'muted' ? 'rgba(107, 117, 146, 0.1)' : 'rgba(107, 117, 146, 0.1)',
                            color: config.color === 'contain' ? '#E5484D' :
                                   config.color === 'escalate' ? '#F5A623' :
                                   config.color === 'muted' ? '#6B7592' : '#6B7592'
                          }}>
                            {alert.risk_level}
                          </span>
                          <span className="text-xs font-mono px-2 py-0.5 rounded-full border" style={{
                            borderColor: config.color === 'contain' ? 'rgba(229, 72, 77, 0.2)' :
                                        config.color === 'escalate' ? 'rgba(245, 166, 35, 0.2)' :
                                        config.color === 'muted' ? 'rgba(107, 117, 146, 0.2)' : 'rgba(107, 117, 146, 0.2)',
                            color: config.color === 'contain' ? '#E5484D' :
                                   config.color === 'escalate' ? '#F5A623' :
                                   config.color === 'muted' ? '#6B7592' : '#6B7592'
                          }}>
                            {alert.decision}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted">
                          <Clock size={12} />
                          {formatTimestamp(alert.timestamp)}
                        </div>
                      </div>

                      {/* Content */}
                      <p className="text-sm text-text mb-2 line-clamp-2">
                        {alert.intent_summary}
                      </p>

                      {/* Footer */}
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono text-muted">
                          {alert.agent_id}
                        </span>
                        <div className="flex items-center gap-1">
                          <span className="text-muted">Risk:</span>
                          <span
                            className={`font-bold ${
                              alert.behavioral_risk > 0.8
                                ? 'text-contain'
                                : alert.behavioral_risk > 0.5
                                ? 'text-escalate'
                                : 'text-allow'
                            }`}
                          >
                            {(alert.behavioral_risk * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </motion.div>
  );
}
