import { useState, useRef, useCallback, useEffect } from 'react';
import type { EmotionPrediction } from '@/types';

interface WebSocketState {
  isConnected: boolean;
  isRecording: boolean;
  lastEmotion: EmotionPrediction | null;
  emotionHistory: EmotionPrediction[];
  error: string | null;
}

interface UseWebSocketReturn extends WebSocketState {
  startCall: (agentName: string, customerName: string) => Promise<string>;
  stopCall: () => void;
  connect: (callId: string) => void;
  disconnect: () => void;
}

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [lastEmotion, setLastEmotion] = useState<EmotionPrediction | null>(null);
  const [emotionHistory, setEmotionHistory] = useState<EmotionPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const callIdRef = useRef<string | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Start a new call session
  const startCall = useCallback(async (agentName: string, customerName: string): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/calls/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName, customer_name: customerName })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start call');
      }
      
      const data = await response.json();
      callIdRef.current = data.call_id;
      return data.call_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start call');
      throw err;
    }
  }, []);

  // Stop the current call
  const stopCall = useCallback(async () => {
    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // Stop stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Send stop message if still open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
    }

    // Always close WebSocket regardless of its state
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Always end call on server — even if WebSocket already dropped
    if (callIdRef.current) {
      try {
        await fetch(`${API_BASE_URL}/api/calls/${callIdRef.current}/end`, {
          method: 'POST'
        });
      } catch (err) {
        console.error('Failed to end call:', err);
      }
    }

    // Always reset state — this must run even if WS was already closed
    setIsRecording(false);
    setIsConnected(false);
    callIdRef.current = null;
  }, []);

  // Connect to WebSocket and start audio streaming
  const connect = useCallback(async (callId: string) => {
    try {
      setError(null);
      callIdRef.current = callId;
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      streamRef.current = stream;
      
      // Create WebSocket connection
      const ws = new WebSocket(`${WS_BASE_URL}/ws/stream/${callId}`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send configuration
        ws.send(JSON.stringify({
          action: 'config',
          sample_rate: 16000,
          format: 'pcm_16bit'
        }));
        
        // Start recording
        startRecording(stream, ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'emotion') {
          // Always add to history for charts
          setEmotionHistory(prev => [...prev, data]);
          // Show immediately — the backend already applies majority voting over
          // the last 3 predictions, so additional frontend smoothing is not needed
          // and caused a bug where alternating emotions got the display stuck.
          setLastEmotion(data);
        } else if (data.type === 'config_ack') {
          console.log('Configuration acknowledged:', data);
        }
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket connection error');
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsConnected(false);
      };
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      console.error('Connection error:', err);
    }
  }, []);

  // Start audio recording
  const startRecording = (stream: MediaStream, ws: WebSocket) => {
    // Create audio context for processing
    const audioContext = new AudioContext({ sampleRate: 16000 });
    audioContextRef.current = audioContext;
    
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    source.connect(processor);
    processor.connect(audioContext.destination);
    
    processor.onaudioprocess = (e) => {
      if (ws.readyState === WebSocket.OPEN) {
        // Get audio data
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Convert to 16-bit PCM
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32767));
        }
        
        // Send as binary
        ws.send(pcmData.buffer);
      }
    };
    
    setIsRecording(true);
  };

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    stopCall();
  }, [stopCall]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCall();
    };
  }, [stopCall]);

  return {
    isConnected,
    isRecording,
    lastEmotion,
    emotionHistory,
    error,
    startCall,
    stopCall,
    connect,
    disconnect
  };
}

// Alternative hook using MediaRecorder API (simpler but less control)
export function useMediaRecorderWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [lastEmotion, setLastEmotion] = useState<EmotionPrediction | null>(null);
  const [emotionHistory, setEmotionHistory] = useState<EmotionPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const callIdRef = useRef<string | null>(null);

  const startCall = useCallback(async (agentName: string, customerName: string): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/calls/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName, customer_name: customerName })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start call');
      }
      
      const data = await response.json();
      callIdRef.current = data.call_id;
      return data.call_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start call');
      throw err;
    }
  }, []);

  const stopCall = useCallback(async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
      
      if (callIdRef.current) {
        try {
          await fetch(`${API_BASE_URL}/api/calls/${callIdRef.current}/end`, {
            method: 'POST'
          });
        } catch (err) {
          console.error('Failed to end call:', err);
        }
      }
      
      wsRef.current.close();
    }
    
    setIsRecording(false);
    setIsConnected(false);
    callIdRef.current = null;
  }, []);

  const connect = useCallback(async (callId: string) => {
    try {
      setError(null);
      callIdRef.current = callId;
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const ws = new WebSocket(`${WS_BASE_URL}/ws/stream/${callId}`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Start recording with timeslice for chunked sending
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus',
          audioBitsPerSecond: 16000
        });
        mediaRecorderRef.current = mediaRecorder;
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            event.data.arrayBuffer().then(buffer => {
              ws.send(buffer);
            });
          }
        };
        
        mediaRecorder.start(500); // Collect 500ms chunks
        setIsRecording(true);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'emotion') {
          setLastEmotion(data);
          setEmotionHistory(prev => [...prev, data]);
        }
      };
      
      ws.onerror = () => {
        setError('WebSocket connection error');
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        setIsConnected(false);
      };
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, []);

  const disconnect = useCallback(() => {
    stopCall();
  }, [stopCall]);

  useEffect(() => {
    return () => {
      stopCall();
    };
  }, [stopCall]);

  return {
    isConnected,
    isRecording,
    lastEmotion,
    emotionHistory,
    error,
    startCall,
    stopCall,
    connect,
    disconnect
  };
}
