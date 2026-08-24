import { useState, useEffect, useCallback } from 'react';

export type ExecutionStage = 'INTENT' | 'BEHAVIOR' | 'POLICY' | 'CAPABILITY' | 'MCP' | 'RAZORPAY' | 'VERIFICATION' | 'AUDIT';

export interface SentinelExecutionEvent {
  event_id: string;
  timestamp: string;
  intent_id: string;
  agent_id: string;
  stage: ExecutionStage;
  behavioral_risk?: number;
  semantic_risk?: number;
  policy_decision?: 'ALLOW' | 'ESCALATE' | 'CONTAIN';
  capability_issued?: boolean;
  mcp_tool?: string;
  mcp_invocation?: boolean;
  execution_status?: 'PENDING' | 'SUCCESS' | 'BLOCKED' | 'FAILED';
  provider_reference?: string;
  latency_ms?: number;
  reason_codes?: string[];
}

export function useExecutionStream(url: string = '/api/execution/stream') {
  const [events, setEvents] = useState<SentinelExecutionEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [activeIntent, setActiveIntent] = useState<SentinelExecutionEvent | null>(null);

  useEffect(() => {
    // Only fetch if running via Vite proxy or directly on port
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsed: SentinelExecutionEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev.slice(-99), parsed]); // Keep last 100 events
        
        // Update active intent state (combine events for same intent)
        setActiveIntent((prev) => {
          if (!prev || prev.intent_id !== parsed.intent_id) return parsed;
          return { ...prev, ...parsed }; // merge the latest stage updates
        });
        
      } catch (e) {
        console.error("Failed to parse SSE event", e);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE Error:", error);
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, [url]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setActiveIntent(null);
  }, []);

  return { events, activeIntent, isConnected, clearEvents };
}
