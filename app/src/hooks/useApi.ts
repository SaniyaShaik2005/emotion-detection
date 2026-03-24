import { useState, useCallback, useEffect } from 'react';
import type { Call, EmotionLog, AgentAnalytics } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

// Generic fetch hook
function useApiFetch<T>(url: string): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchData = useCallback(async () => {
    if (!url) {
      setData(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}${url}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshKey]);

  const refetch = useCallback(() => {
    setRefreshKey(prev => prev + 1);
  }, []);

  return { data, isLoading, error, refetch };
}

// Get all calls
export function useCalls(limit: number = 100, offset: number = 0): ApiState<{ calls: Call[]; total: number }> {
  return useApiFetch<{ calls: Call[]; total: number }>(`/api/calls?limit=${limit}&offset=${offset}`);
}

// Get single call with emotions
export function useCall(callId: string | null): ApiState<{ call: Call; emotions: EmotionLog[] }> {
  return useApiFetch<{ call: Call; emotions: EmotionLog[] }>(callId ? `/api/calls/${callId}` : '');
}

// Get call emotions
export function useCallEmotions(callId: string | null): ApiState<{ call_id: string; emotions: EmotionLog[] }> {
  return useApiFetch<{ call_id: string; emotions: EmotionLog[] }>(callId ? `/api/calls/${callId}/emotions` : '');
}

// Get agent analytics
export function useAgentAnalytics(agentName?: string, days: number = 30): ApiState<{ analytics: AgentAnalytics[] }> {
  const queryParams = new URLSearchParams();
  if (agentName) queryParams.append('agent_name', agentName);
  queryParams.append('days', days.toString());
  
  return useApiFetch<{ analytics: AgentAnalytics[] }>(`/api/analytics/agents?${queryParams.toString()}`);
}

// Health check
export function useHealth(): ApiState<{ status: string; model_loaded: boolean; timestamp: string }> {
  return useApiFetch<{ status: string; model_loaded: boolean; timestamp: string }>('/health');
}

// Analytics summary
export function useAnalyticsSummary(days: number = 30): ApiState<{
  total_calls: number;
  completed_calls: number;
  total_agents: number;
  avg_call_duration: number;
  top_emotion: string;
  positive_sentiment_rate: number;
  emotion_distribution: Record<string, number>;
}> {
  return useApiFetch(`/api/analytics/summary?days=${days}`);
}

// Emotions trend
export function useEmotionsTrend(days: number = 7): ApiState<{ trend: Record<string, number | string>[] }> {
  return useApiFetch(`/api/analytics/emotions-trend?days=${days}`);
}

// Manual API functions for mutations
export async function endCall(callId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/calls/${callId}/end`, {
    method: 'POST'
  });
  
  if (!response.ok) {
    throw new Error('Failed to end call');
  }
}

export async function startCall(agentName: string, customerName: string): Promise<{ call_id: string; start_time: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/calls/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_name: agentName, customer_name: customerName })
  });
  
  if (!response.ok) {
    throw new Error('Failed to start call');
  }
  
  return response.json();
}

export async function deleteCall(callId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/calls/${callId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete call record');
  }
}

export async function exportCall(callId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/calls/${callId}/export`);
  
  if (!response.ok) {
    throw new Error('Failed to export call data');
  }
  
  return response.json();
}

export async function getTranscript(callId: string): Promise<{ transcript: string }> {
  const response = await fetch(`${API_BASE_URL}/api/calls/${callId}/transcript`);
  
  if (!response.ok) {
    throw new Error('Failed to get call transcript');
  }
  
  return response.json();
}
