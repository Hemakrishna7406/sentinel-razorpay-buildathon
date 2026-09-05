import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, ShieldAlert, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import type { SentinelExecutionEvent } from '../../hooks/useExecutionStream';
import { useMouseGlow } from '../../hooks/useMouseGlow';

interface LiveExecutionStreamProps {
  events: SentinelExecutionEvent[];
  isConnected: boolean;
}

export function LiveExecutionStream({
  events,
  isConnected,
}: LiveExecutionStreamProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const { mousePosition, isHovering } = useMouseGlow(cardRef);
  const streamRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest event
  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [events]);

  const getEventIcon = (event: SentinelExecutionEvent) => {
    if (event.policy_decision === 'CONTAIN' || event.execution_status === 'BLOCKED') {
      return <ShieldAlert size={16} className="text-contain" />;
    }
    if (event.policy_decision === 'ESCALATE') {
      return <AlertTriangle size={16} className="text-escalate" />;
    }
    if (event.execution_status === 'SUCCESS') {
      return <CheckCircle2 size={16} className="text-allow" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  const getEventColor = (event: SentinelExecutionEvent) => {
    if (event.policy_decision === 'CONTAIN' || event.execution_status === 'BLOCKED') {
      return 'contain';
    }
    if (event.policy_decision === 'ESCALATE') {
      return 'escalate';
    }
    if (event.execution_status === 'SUCCESS') {
      return 'allow';
    }
    return 'muted';
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
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
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-signal/10">
                <Activity size={20} className="text-signal" />
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-text">
                  Live Execution Stream
                </h3>
                <p className="text-xs font-mono text-muted">
                  REAL-TIME SSE MONITORING
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-signal animate-pulse' : 'bg-muted'
                }`}
              />
              <span
                className={`text-xs font-mono ${
                  isConnected ? 'text-signal' : 'text-muted'
                }`}
              >
                {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
              </span>
            </div>
          </div>
        </div>

        {/* Stream */}
        <div
          ref={streamRef}
          className="p-4 space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-muted/20 scrollbar-track-transparent"
        >
          <AnimatePresence mode="popLayout">
            {events.length === 0 ? (
              <div className="text-center py-12 text-muted text-sm">
                Waiting for execution events...
              </div>
            ) : (
              events.slice(-10).map((event) => {
                const color = getEventColor(event);
                const isHighRisk =
                  event.policy_decision === 'CONTAIN' ||
                  event.execution_status === 'BLOCKED';

                return (
                  <motion.div
                    key={event.event_id}
                    initial={{ opacity: 0, x: -20, scale: 0.95 }}
                    animate={{
                      opacity: 1,
                      x: 0,
                      scale: 1,
                    }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.3 }}
                    className={`p-3 rounded-lg border transition-all ${
                      isHighRisk
                        ? 'border-contain/30 bg-contain/5 shadow-[0_0_20px_rgba(229,72,77,0.2)]'
                        : 'border-muted/10 bg-ink/50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">{getEventIcon(event)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-mono text-muted">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                          <span className="text-xs font-mono px-2 py-0.5 rounded-full" style={{
                            backgroundColor: color === 'contain' ? 'rgba(229, 72, 77, 0.1)' :
                                           color === 'escalate' ? 'rgba(245, 166, 35, 0.1)' :
                                           color === 'allow' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(107, 117, 146, 0.1)',
                            color: color === 'contain' ? '#E5484D' :
                                   color === 'escalate' ? '#F5A623' :
                                   color === 'allow' ? '#10B981' : '#6B7280'
                          }}>
                            {event.stage}
                          </span>
                        </div>
                        <div className="text-sm text-text mb-1">
                          Agent: <span className="font-mono">{event.agent_id}</span>
                        </div>
                        {event.behavioral_risk !== undefined && (
                          <div className="text-xs text-muted">
                            Risk: {(event.behavioral_risk * 100).toFixed(1)}%
                          </div>
                        )}
                        {event.policy_decision && (
                          <div className="text-xs font-bold mt-1" style={{
                            color: color === 'contain' ? '#E5484D' :
                                   color === 'escalate' ? '#F5A623' :
                                   color === 'allow' ? '#10B981' : '#6B7280'
                          }}>
                            {event.policy_decision}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
