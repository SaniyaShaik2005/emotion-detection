// Types for Emotion Detection Dashboard

export interface EmotionPrediction {
  emotion: string;
  confidence: number;
  probabilities: Record<string, number>;
  timestamp: string;
  time_offset: number;
  chunk_id: number;
  is_speech: boolean;
  audio_energy?: number;
}

export interface Call {
  id: number;
  call_id: string;
  agent_name: string;
  customer_name: string;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  status: 'active' | 'completed' | 'failed';
  dominant_emotion?: string;
  emotion_distribution?: Record<string, number>;
  avg_confidence?: number;
}

export interface EmotionLog {
  id: number;
  call_id: string;
  timestamp: string;
  time_offset_seconds: number;
  emotion: string;
  confidence: number;
  all_probabilities: Record<string, number>;
  is_speech: boolean;
  audio_energy?: number;
}

export interface AgentAnalytics {
  id: number;
  agent_name: string;
  date: string;
  total_calls: number;
  total_duration_seconds: number;
  avg_call_duration: number;
  positive_emotion_ratio: number;
  negative_emotion_ratio: number;
  avg_customer_satisfaction: number;
}

export interface CallSession {
  callId: string;
  isActive: boolean;
  startTime?: Date;
  emotionHistory: EmotionPrediction[];
}

export const EMOTION_COLORS: Record<string, string> = {
  neutral: '#94a3b8',
  happy: '#22c55e',
  sad: '#3b82f6',
  angry: '#ef4444',
  fearful: '#a855f7',
  disgust: '#f97316',
  surprised: '#eab308',
  silence: '#64748b',
  error: '#1f2937',
  confused: '#06b6d4',
  frustrated: '#dc2626'
};

export const EMOTION_ICONS: Record<string, string> = {
  neutral: '😐',
  happy: '😊',
  sad: '😢',
  angry: '😠',
  fearful: '😨',
  disgust: '🤢',
  surprised: '😲',
  silence: '🔇',
  confused: '😕',
  frustrated: '😤'
};
