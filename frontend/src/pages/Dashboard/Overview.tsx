/**
 * Sentinel Dashboard - Overview Page
 *
 * Premium execution control room with:
 * - Animated KPI cards with rolling counters
 * - Live SSE execution stream with flash animations
 * - Risk trend charts with Recharts
 * - Recent alerts with glow effects
 * - Glassmorphism UI elements
 * - Mouse-tracking glow effects on cards
 * - Animated background gradients
 *
 * Data Sources:
 * - SSE Stream: /api/execution/stream (real-time events)
 * - Analytics: /api/analytics/dashboard/executive (dashboard metrics)
 * - Falls back to mock data if backend unavailable
 */

import { motion } from 'framer-motion';
import {
  Activity,
  ShieldAlert,
  TrendingUp,
  Users,
  Zap,
  Clock
} from 'lucide-react';
import { useExecutionStream } from '../../hooks/useExecutionStream';
import { useDashboardData, generateMockDashboardData } from '../../hooks/useDashboardData';
import { KPICard } from '../../components/Dashboard/KPICard';
import { LiveExecutionStream } from '../../components/Dashboard/LiveExecutionStream';
import { RiskTrendChart } from '../../components/Dashboard/RiskTrendChart';
import { RecentAlerts } from '../../components/Dashboard/RecentAlerts';
import { AnimatedBackground } from '../../components/Dashboard/AnimatedBackground';
import { ExecutionPipeline } from '../../components/ExecutionPipeline/ExecutionPipeline';

export default function Overview() {
  const { events, activeIntent, isConnected } = useExecutionStream('/api/execution/stream');

  // Use real data if available, otherwise use mock data for demo
  const { data: dashboardData } = useDashboardData();
  const data = dashboardData || generateMockDashboardData();

  const isAnomalous =
    activeIntent?.policy_decision === 'CONTAIN' ||
    activeIntent?.execution_status === 'BLOCKED';

  return (
    <div className="min-h-screen bg-background relative">
      <AnimatedBackground />
      {/* Glassmorphism Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-muted/20 relative"
      >
        <div className="max-w-[1600px] mx-auto px-8 py-6">
          <div className="flex justify-between items-end">
            <div>
              <h1 className="font-display text-4xl font-bold text-text mb-2">
                Execution Control Room
              </h1>
              <p className="text-muted font-mono text-sm">
                SENTINEL-CORE // LIVE GOVERNANCE
              </p>
            </div>

            <div className="flex gap-4">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-2 font-mono text-xs bg-panel/60 backdrop-blur-xl border border-muted/20 px-4 py-2 rounded-xl"
              >
                <span className="text-muted">SSE:</span>
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-signal animate-pulse' : 'bg-muted'
                  }`}
                />
                <span className={isConnected ? 'text-signal' : 'text-muted'}>
                  {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
                </span>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.05 }}
                className={`flex items-center gap-2 font-mono text-xs bg-panel/60 backdrop-blur-xl border px-4 py-2 rounded-xl transition-all duration-500 ${
                  isAnomalous
                    ? 'border-contain/40 shadow-[0_0_20px_rgba(229,72,77,0.2)]'
                    : 'border-muted/20'
                }`}
              >
                <span className="text-muted">SYSTEM:</span>
                <div
                  className={`w-2 h-2 rounded-full ${
                    isAnomalous ? 'bg-contain' : 'bg-signal animate-pulse'
                  }`}
                />
                <span
                  className={isAnomalous ? 'text-contain font-bold' : 'text-signal'}
                >
                  {isAnomalous ? 'INTERCEPTED' : 'OPERATIONAL'}
                </span>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.header>

      <div className="max-w-[1600px] mx-auto px-8 py-8 space-y-8 relative z-10">
        {/* KPI Cards - Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Total Executions"
            value={data.metrics.total_executions}
            subtitle="24H VOLUME"
            icon={Activity}
            color="signal"
            trend="up"
            trendValue="+12.5%"
            delay={0}
          />
          <KPICard
            title="Blocked"
            value={data.metrics.blocked_executions}
            subtitle="SECURITY CONTAINMENT"
            icon={ShieldAlert}
            color="contain"
            trend="down"
            trendValue="-3.2%"
            delay={100}
          />
          <KPICard
            title="Active Agents"
            value={data.metrics.active_agents}
            subtitle="MONITORED INSTANCES"
            icon={Users}
            color="signal"
            delay={200}
          />
          <KPICard
            title="Avg Latency"
            value={data.metrics.avg_latency_ms}
            subtitle="RESPONSE TIME"
            icon={Clock}
            color="allow"
            format="milliseconds"
            trend="down"
            trendValue="-8ms"
            delay={300}
          />
        </div>

        {/* Main Pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <ExecutionPipeline activeEvent={activeIntent} />
        </motion.div>

        {/* Bento Grid - Analytics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Live Stream - spans 1 column */}
          <div className="lg:col-span-1">
            <LiveExecutionStream events={events} isConnected={isConnected} />
          </div>

          {/* Risk Chart - spans 2 columns */}
          <div className="lg:col-span-2">
            <RiskTrendChart data={data.risk_trend} />
          </div>
        </div>

        {/* Recent Alerts */}
        <RecentAlerts alerts={data.recent_alerts} />

        {/* Secondary KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard
            title="Escalated"
            value={data.metrics.escalated_executions}
            subtitle="FLAGGED FOR REVIEW"
            icon={TrendingUp}
            color="escalate"
            delay={100}
          />
          <KPICard
            title="Allowed"
            value={data.metrics.allowed_executions}
            subtitle="APPROVED EXECUTIONS"
            icon={Activity}
            color="allow"
            trend="up"
            trendValue="+5.8%"
            delay={200}
          />
          <KPICard
            title="MCP Invocations"
            value={data.metrics.mcp_invocations}
            subtitle="TOOL CALLS"
            icon={Zap}
            color="signal"
            trend="up"
            trendValue="+18.3%"
            delay={300}
          />
        </div>

        {/* Footer Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="text-center py-8"
        >
          <p className="text-xs font-mono text-muted">
            Last updated: {new Date(data.last_updated).toLocaleString()} •
            Sentinel v2.0 • Zero-Trust Execution Framework
          </p>
        </motion.div>
      </div>
    </div>
  );
}
