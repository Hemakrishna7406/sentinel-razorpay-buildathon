export type SentinelDecision = 'ALLOW' | 'ESCALATE' | 'CONTAIN' | 'EVALUATING';

export interface EvaluationResult {
  id: string;
  timestamp: string;
  action: string;
  decision: SentinelDecision;
  riskScore: number;
  latencyMs: number;
  reasons: string[];
  payload: Record<string, any>;
}
