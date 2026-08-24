import { useState, useCallback } from 'react';

export type DemoScenario = 'normal' | 'abuse-burst' | 'privilege-violation' | 'real-test-order';

export function useDemoScenario(baseUrl: string = '/api/demo/scenarios') {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggerScenario = useCallback(async (scenario: DemoScenario) => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await fetch(`${baseUrl}/${scenario}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to trigger scenario: ${response.statusText}`);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsRunning(false);
    }
  }, [baseUrl]);

  return { triggerScenario, isRunning, error };
}
