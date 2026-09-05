import { useState, useEffect, useCallback, useRef } from 'react';

export interface SSEEvent<T = unknown> {
  data: T;
  id?: string;
  event?: string;
  timestamp: number;
}

export interface UseSSEOptions {
  reconnect?: boolean;
  reconnectInterval?: number;
  reconnectAttempts?: number;
}

export function useSSE<T = unknown>(
  url: string,
  options: UseSSEOptions = {}
) {
  const {
    reconnect = true,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
  } = options;

  const [events, setEvents] = useState<SSEEvent<T>[]>([]);
  const [latestEvent, setLatestEvent] = useState<SSEEvent<T> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  const connect = useCallback(() => {
    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const sseEvent: SSEEvent<T> = {
            data,
            id: event.lastEventId,
            timestamp: Date.now(),
          };

          setLatestEvent(sseEvent);
          setEvents((prev) => [...prev.slice(-99), sseEvent]); // Keep last 100
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        setIsConnected(false);
        setError(new Error('SSE connection failed'));
        eventSource.close();

        if (reconnect && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      setIsConnected(false);
    }
  }, [url, reconnect, reconnectInterval, reconnectAttempts]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestEvent(null);
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  }, []);

  return {
    events,
    latestEvent,
    isConnected,
    error,
    clearEvents,
    disconnect,
    reconnect: connect,
  };
}
