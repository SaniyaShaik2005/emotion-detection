import React from 'react';
import type { EmotionPrediction } from '@/types';
import { EMOTION_COLORS, EMOTION_ICONS } from '@/types';
import { Activity, Mic, MicOff } from 'lucide-react';

interface CurrentEmotionProps {
  prediction: EmotionPrediction | null;
  isRecording: boolean;
}

export const CurrentEmotion: React.FC<CurrentEmotionProps> = ({ prediction, isRecording }) => {
  if (!prediction) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
        <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center mb-4">
          {isRecording ? (
            <Activity className="w-8 h-8 text-gray-400 animate-pulse" />
          ) : (
            <MicOff className="w-8 h-8 text-gray-400" />
          )}
        </div>
        <p className="text-gray-500 text-lg">
          {isRecording ? 'Waiting for audio...' : 'Start a call to detect emotions'}
        </p>
      </div>
    );
  }

  const { emotion, confidence, probabilities, is_speech } = prediction;
  const color = EMOTION_COLORS[emotion] || '#8884d8';
  const icon = EMOTION_ICONS[emotion] || '😐';
  const confidencePercent = Math.round(confidence * 100);

  // Get top 3 emotions
  const topEmotions = Object.entries(probabilities || {})
    .filter(([e]) => e !== 'silence' && e !== 'error')
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Main emotion display */}
      <div 
        className="relative overflow-hidden rounded-xl p-8 text-center transition-all duration-300"
        style={{ 
          backgroundColor: `${color}15`,
          border: `2px solid ${color}40`
        }}
      >
        {/* Recording indicator */}
        {isRecording && is_speech && (
          <div className="absolute top-4 right-4 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span 
                className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ backgroundColor: color }}
              />
              <span 
                className="relative inline-flex rounded-full h-3 w-3"
                style={{ backgroundColor: color }}
              />
            </span>
            <Mic className="w-4 h-4" style={{ color }} />
          </div>
        )}

        {/* Emotion icon */}
        <div 
          className="text-8xl mb-4 animate-in zoom-in duration-300"
          style={{ filter: `drop-shadow(0 4px 8px ${color}40)` }}
        >
          {icon}
        </div>

        {/* Emotion name */}
        <h2 
          className="text-3xl font-bold capitalize mb-2"
          style={{ color }}
        >
          {emotion}
        </h2>

        {/* Confidence */}
        <div className="flex items-center justify-center gap-2">
          <span className="text-gray-600">Confidence:</span>
          <span 
            className="text-2xl font-bold"
            style={{ color }}
          >
            {confidencePercent}%
          </span>
        </div>

        {/* Confidence bar */}
        <div className="mt-4 w-full max-w-xs mx-auto">
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500"
              style={{ 
                width: `${confidencePercent}%`,
                backgroundColor: color
              }}
            />
          </div>
        </div>
      </div>

      {/* Top emotions breakdown */}
      {topEmotions.length > 0 && (
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Other Probabilities</h3>
          <div className="space-y-2">
            {topEmotions.map(([emo, prob]) => {
              if (emo === emotion) return null;
              const probPercent = Math.round((prob as number) * 100);
              const emoColor = EMOTION_COLORS[emo] || '#8884d8';
              
              return (
                <div key={emo} className="flex items-center gap-3">
                  <span className="text-lg">{EMOTION_ICONS[emo] || '😐'}</span>
                  <span className="capitalize text-sm w-20">{emo}</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full"
                      style={{ 
                        width: `${probPercent}%`,
                        backgroundColor: emoColor
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium w-10 text-right">{probPercent}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default CurrentEmotion;