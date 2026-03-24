import React from 'react';
import type { EmotionPrediction } from '@/types';
import { EMOTION_COLORS, EMOTION_ICONS } from '@/types';

interface EmotionTimelineProps {
  emotionHistory: EmotionPrediction[];
  maxSegments?: number;
}

interface TimelineSegment {
  emotion: string;
  startTime: number;
  endTime: number;
  duration: number;
  confidence: number;
}

export const EmotionTimeline: React.FC<EmotionTimelineProps> = ({ 
  emotionHistory, 
  maxSegments = 20 
}) => {
  // Group consecutive same emotions
  const generateTimeline = (): TimelineSegment[] => {
    if (emotionHistory.length === 0) return [];

    const segments: TimelineSegment[] = [];
    let currentSegment: TimelineSegment | null = null;

    emotionHistory.forEach((pred, index) => {
      const time = pred.time_offset || index * 0.5;
      
      if (!currentSegment || currentSegment.emotion !== pred.emotion) {
        if (currentSegment) {
          const seg: TimelineSegment = currentSegment;
          seg.endTime = time;
          seg.duration = seg.endTime - seg.startTime;
        }
        currentSegment = {
          emotion: pred.emotion,
          startTime: time,
          endTime: time,
          duration: 0,
          confidence: pred.confidence
        };
        segments.push(currentSegment);
      } else {
        const seg: TimelineSegment = currentSegment;
        seg.endTime = time;
        seg.duration = seg.endTime - seg.startTime;
        // Update confidence to average
        seg.confidence = (seg.confidence + pred.confidence) / 2;
      }
    });

    // Finalize last segment
    if (currentSegment) {
      const lastPred = emotionHistory[emotionHistory.length - 1];
      const seg: TimelineSegment = currentSegment;
      seg.endTime = lastPred.time_offset || emotionHistory.length * 0.5;
      seg.duration = seg.endTime - seg.startTime;
    }

    return segments.slice(-maxSegments);
  };

  const segments = generateTimeline();
  const totalDuration = segments.reduce((sum, seg) => sum + seg.duration, 0) || 1;

  if (segments.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-500">No timeline data available</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Timeline bar */}
      <div className="flex h-16 rounded-lg overflow-hidden shadow-inner bg-gray-100">
        {segments.map((segment, index) => {
          const widthPercent = (segment.duration / totalDuration) * 100;
          const isNarrow = widthPercent < 5;
          
          return (
            <div
              key={index}
              className="relative flex items-center justify-center transition-all duration-300 hover:opacity-90 cursor-pointer group"
              style={{
                width: `${widthPercent}%`,
                backgroundColor: EMOTION_COLORS[segment.emotion] || '#8884d8',
                minWidth: '20px'
              }}
            >
              {/* Icon (shown if wide enough) */}
              {!isNarrow && (
                <span className="text-lg" title={segment.emotion}>
                  {EMOTION_ICONS[segment.emotion] || '😐'}
                </span>
              )}
              
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    <span>{EMOTION_ICONS[segment.emotion] || '😐'}</span>
                    <span className="capitalize">{segment.emotion}</span>
                  </div>
                  <div>Duration: {segment.duration.toFixed(1)}s</div>
                  <div>Confidence: {(segment.confidence * 100).toFixed(0)}%</div>
                </div>
                <div className="border-4 border-transparent border-t-gray-900 absolute top-full left-1/2 transform -translate-x-1/2"></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Time markers */}
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>0s</span>
        <span>{(totalDuration / 2).toFixed(0)}s</span>
        <span>{totalDuration.toFixed(0)}s</span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 mt-4">
        {Array.from(new Set(segments.map(s => s.emotion))).map(emotion => (
          <div 
            key={emotion} 
            className="flex items-center gap-1 px-2 py-1 rounded-full text-xs"
            style={{ backgroundColor: `${EMOTION_COLORS[emotion]}20` }}
          >
            <span 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: EMOTION_COLORS[emotion] }}
            />
            <span className="capitalize">{emotion}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmotionTimeline;
