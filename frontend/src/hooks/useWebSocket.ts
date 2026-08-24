import { useState, useEffect, useCallback } from 'react';
import type { EvaluationResult, SentinelDecision } from '../types';

interface UseWebSocketOptions {
  url: string; // The future WS endpoint (e.g. ws://localhost:8000/ws)
  mock?: boolean; // If true, generates fake traffic
}

export function useWebSocket({ url, mock = false }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<EvaluationResult[]>([]);
  const [latestMessage, setLatestMessage] = useState<EvaluationResult | null>(null);

  // MOCK DATA GENERATOR
  useEffect(() => {
    if (!mock) return;

    setIsConnected(true);

    const generateMockMessage = () => {
      const isAnomalous = Math.random() > 0.8;
      const decision: SentinelDecision = isAnomalous ? 'CONTAINED' : 'ALLOWED';
      const actions = ['Payout', 'Transfer', 'Refund', 'PaymentLink'];
      const action = actions[Math.floor(Math.random() * actions.length)];
      
      const newMsg: EvaluationResult = {
        id: `req_${Math.random().toString(36).substring(2, 8)}`,
        timestamp: new Date().toISOString(),
        action,
        decision,
        riskScore: isAnomalous ? Math.floor(Math.random() * 20) + 80 : Math.floor(Math.random() * 30),
        latencyMs: Math.floor(Math.random() * 15) + 5,
        reasons: isAnomalous ? ['Velocity breach', 'Unseen target'] : [],
        payload: { amount: Math.floor(Math.random() * 10000) }
      };

      setLatestMessage(newMsg);
      setMessages(prev => [newMsg, ...prev].slice(0, 50)); // keep last 50
    };

    // Generate a message every 2-5 seconds
    const scheduleNext = () => {
      const delay = Math.random() * 3000 + 2000;
      return setTimeout(() => {
        generateMockMessage();
        timerId = scheduleNext();
      }, delay);
    };

    let timerId = scheduleNext();

    return () => clearTimeout(timerId);
  }, [mock, url]);

  // FUTURE: REAL WEBSOCKET IMPLEMENTATION
  useEffect(() => {
    if (mock) return;
    
    let ws: WebSocket;
    let reconnectTimer: number;

    const connect = () => {
      try {
        ws = new WebSocket(url);
        
        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimer = window.setTimeout(connect, 3000);
        };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as EvaluationResult;
            setLatestMessage(data);
            setMessages(prev => [data, ...prev].slice(0, 50));
          } catch (e) {
            console.error('Failed to parse WS message', e);
          }
        };
      } catch (err) {
        console.error('WS Connection error:', err);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [mock, url]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLatestMessage(null);
  }, []);

  return {
    isConnected,
    messages,
    latestMessage,
    clearMessages
  };
}
