import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import type { EmotionPrediction } from '@/types';
import { EMOTION_COLORS } from '@/types';

interface EmotionGraphProps {
  emotionHistory: EmotionPrediction[];
  maxPoints?: number;
}

interface GraphDataPoint {
  time: number;
  timestamp: string;
  [emotion: string]: number | string;
}

export const EmotionGraph: React.FC<EmotionGraphProps> = ({ 
  emotionHistory, 
  maxPoints = 50 
}) => {
  // Process data for the chart
  const processData = (): GraphDataPoint[] => {
    // Get recent history
    const recent = emotionHistory.slice(-maxPoints);
    
    return recent.map((prediction, index) => {
      const dataPoint: GraphDataPoint = {
        time: index,
        timestamp: new Date(prediction.timestamp).toLocaleTimeString(),
      };
      
      // Add probability for each emotion
      Object.entries(prediction.probabilities).forEach(([emotion, prob]) => {
        dataPoint[emotion] = Math.round(prob * 100);
      });
      
      return dataPoint;
    });
  };

  const data = processData();
  
  // Get all unique emotions from the data
  const allEmotions = React.useMemo(() => {
    const emotions = new Set<string>();
    emotionHistory.forEach(pred => {
      Object.keys(pred.probabilities).forEach(emo => emotions.add(emo));
    });
    return Array.from(emotions).filter(e => e !== 'silence' && e !== 'error');
  }, [emotionHistory]);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-500">No emotion data available yet</p>
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
            minTickGap={30}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fontSize: 12 }}
            label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            formatter={(value: number) => [`${value}%`, 'Confidence']}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '10px' }}
            iconType="line"
          />
          {allEmotions.map(emotion => (
            <Line
              key={emotion}
              type="monotone"
              dataKey={emotion}
              stroke={EMOTION_COLORS[emotion] || '#8884d8'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EmotionGraph;
