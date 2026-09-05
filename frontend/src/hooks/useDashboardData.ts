import { useQuery } from '@tanstack/react-query';

export interface DashboardMetrics {
  total_executions: number;
  blocked_executions: number;
  escalated_executions: number;
  allowed_executions: number;
  avg_behavioral_risk: number;
  avg_latency_ms: number;
  active_agents: number;
  mcp_invocations: number;
}

export interface RiskTrendPoint {
  timestamp: string;
  behavioral_risk: number;
  semantic_risk: number;
  hour: string;
}

export interface RecentAlert {
  id: string;
  timestamp: string;
  agent_id: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  decision: 'ALLOW' | 'ESCALATE' | 'CONTAIN';
  behavioral_risk: number;
  intent_summary: string;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  risk_trend: RiskTrendPoint[];
  recent_alerts: RecentAlert[];
  last_updated: string;
}

async function fetchDashboardData(): Promise<DashboardData> {
  const response = await fetch('/api/analytics/dashboard/executive');

  if (!response.ok) {
    throw new Error('Failed to fetch dashboard data');
  }

  return response.json();
}

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard', 'executive'],
    queryFn: fetchDashboardData,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 20000,
    retry: 3,
  });
}

// Mock data generator for development/demo
export function generateMockDashboardData(): DashboardData {
  const now = new Date();

  return {
    metrics: {
      total_executions: 2847,
      blocked_executions: 124,
      escalated_executions: 89,
      allowed_executions: 2634,
      avg_behavioral_risk: 0.34,
      avg_latency_ms: 142,
      active_agents: 8,
      mcp_invocations: 4521,
    },
    risk_trend: Array.from({ length: 24 }, (_, i) => {
      const hour = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000);
      return {
        timestamp: hour.toISOString(),
        behavioral_risk: 0.2 + Math.random() * 0.6,
        semantic_risk: 0.15 + Math.random() * 0.5,
        hour: hour.toLocaleTimeString('en-US', { hour: '2-digit' }),
      };
    }),
    recent_alerts: [
      {
        id: '1',
        timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
        agent_id: 'agent-alpha-7',
        risk_level: 'high',
        decision: 'CONTAIN',
        behavioral_risk: 0.89,
        intent_summary: 'Attempted unauthorized file system access',
      },
      {
        id: '2',
        timestamp: new Date(now.getTime() - 12 * 60 * 1000).toISOString(),
        agent_id: 'agent-beta-3',
        risk_level: 'medium',
        decision: 'ESCALATE',
        behavioral_risk: 0.67,
        intent_summary: 'Unusual network request pattern detected',
      },
      {
        id: '3',
        timestamp: new Date(now.getTime() - 18 * 60 * 1000).toISOString(),
        agent_id: 'agent-gamma-1',
        risk_level: 'critical',
        decision: 'CONTAIN',
        behavioral_risk: 0.94,
        intent_summary: 'Privilege escalation attempt detected',
      },
      {
        id: '4',
        timestamp: new Date(now.getTime() - 25 * 60 * 1000).toISOString(),
        agent_id: 'agent-delta-5',
        risk_level: 'medium',
        decision: 'ESCALATE',
        behavioral_risk: 0.71,
        intent_summary: 'Data exfiltration pattern observed',
      },
      {
        id: '5',
        timestamp: new Date(now.getTime() - 32 * 60 * 1000).toISOString(),
        agent_id: 'agent-epsilon-2',
        risk_level: 'low',
        decision: 'ALLOW',
        behavioral_risk: 0.23,
        intent_summary: 'Standard API call with elevated parameters',
      },
    ],
    last_updated: now.toISOString(),
  };
}
