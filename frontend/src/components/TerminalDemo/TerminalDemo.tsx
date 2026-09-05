import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface LogEntry {
  id: number;
  timestamp: string;
  agent: string;
  action: string;
  amount: string;
  decision: 'ALLOW' | 'CONTAIN' | 'ESCALATE';
  riskScore: number;
}

const mockLogs: Omit<LogEntry, 'id' | 'timestamp'>[] = [
  { agent: 'payment-agent-6c', action: 'payroll_execute', amount: '₹12,450', decision: 'ALLOW', riskScore: 18 },
  { agent: 'vendor-agent-2a', action: 'invoice_payment', amount: '₹8,900', decision: 'ALLOW', riskScore: 22 },
  { agent: 'payment-agent-6c', action: 'transfer_funds', amount: '₹52,400', decision: 'CONTAIN', riskScore: 92 },
  { agent: 'expense-agent-4b', action: 'approve_expense', amount: '₹3,200', decision: 'ALLOW', riskScore: 15 },
  { agent: 'payment-agent-6c', action: 'bulk_transfer', amount: '₹45,000', decision: 'ESCALATE', riskScore: 67 },
  { agent: 'refund-agent-1x', action: 'process_refund', amount: '₹6,750', decision: 'ALLOW', riskScore: 19 },
];

export default function TerminalDemo() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    if (!isPlaying) return;

    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex >= mockLogs.length) {
        currentIndex = 0;
        setLogs([]);
      }

      const newLog: LogEntry = {
        ...mockLogs[currentIndex],
        id: Date.now() + currentIndex,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      };

      setLogs((prev) => [...prev.slice(-5), newLog]);
      currentIndex++;
    }, 2000);

    return () => clearInterval(interval);
  }, [isPlaying]);

  const getDecisionIcon = (decision: LogEntry['decision']) => {
    switch (decision) {
      case 'ALLOW':
        return <CheckCircle2 className="w-4 h-4 text-allow" />;
      case 'CONTAIN':
        return <XCircle className="w-4 h-4 text-contain" />;
      case 'ESCALATE':
        return <AlertTriangle className="w-4 h-4 text-escalate" />;
    }
  };

  const getDecisionColor = (decision: LogEntry['decision']) => {
    switch (decision) {
      case 'ALLOW':
        return 'text-allow';
      case 'CONTAIN':
        return 'text-contain';
      case 'ESCALATE':
        return 'text-escalate';
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 30) return 'text-allow';
    if (score < 60) return 'text-escalate';
    return 'text-contain';
  };

  return (
    <div className="bg-background-elevated border border-border rounded-xl overflow-hidden shadow-2xl">
      {/* Terminal header */}
      <div className="bg-background-card border-b border-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-sentinel" />
          <span className="text-sm font-semibold text-text-primary">Sentinel Authorization Stream</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-contain" />
            <div className="w-3 h-3 rounded-full bg-escalate" />
            <div className="w-3 h-3 rounded-full bg-allow" />
          </div>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="ml-3 px-3 py-1 text-xs font-medium bg-background-elevated border border-border-light rounded hover:bg-background-card transition-colors"
          >
            {isPlaying ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      {/* Terminal content */}
      <div className="bg-[#0A0E1A] p-6 font-mono text-xs h-[320px] overflow-hidden">
        <AnimatePresence mode="popLayout">
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-3 pb-3 border-b border-border/30 last:border-0"
            >
              <div className="flex items-start gap-3">
                <span className="text-text-muted tabular-nums shrink-0">{log.timestamp}</span>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sentinel">{log.agent}</span>
                    <span className="text-text-muted">→</span>
                    <span className="text-text-secondary">{log.action}</span>
                    <span className="text-text-primary font-semibold">{log.amount}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      {getDecisionIcon(log.decision)}
                      <span className={`font-bold uppercase ${getDecisionColor(log.decision)}`}>
                        {log.decision}
                      </span>
                    </div>
                    <span className="text-text-muted">•</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-text-muted">Risk:</span>
                      <span className={`font-bold tabular-nums ${getRiskColor(log.riskScore)}`}>
                        {log.riskScore}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {logs.length === 0 && (
          <div className="text-text-muted text-center py-12">
            Waiting for authorization events...
          </div>
        )}
      </div>

      {/* Terminal footer stats */}
      <div className="bg-background-card border-t border-border px-4 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-allow animate-pulse" />
            <span className="text-text-muted">Stream Active</span>
          </div>
          <span className="text-text-muted">•</span>
          <span className="text-text-muted tabular-nums">{logs.length} events</span>
        </div>
        <div className="text-text-muted">
          Latency: <span className="text-sentinel font-semibold">~28ms</span>
        </div>
      </div>
    </div>
  );
}
