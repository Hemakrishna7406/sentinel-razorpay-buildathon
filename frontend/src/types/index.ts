export type SentinelDecision = 'ALLOWED' | 'CONTAINED' | 'EVALUATING';

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
