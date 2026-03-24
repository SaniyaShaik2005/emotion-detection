import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { EmotionPrediction } from '@/types';
import { EMOTION_COLORS, EMOTION_ICONS } from '@/types';

interface EmotionDistributionProps {
  emotionHistory: EmotionPrediction[];
}

interface DistributionData {
  name: string;
  value: number;
  color: string;
  icon: string;
}

export const EmotionDistribution: React.FC<EmotionDistributionProps> = ({ emotionHistory }) => {
  // Calculate emotion distribution
  const calculateDistribution = (): DistributionData[] => {
    if (emotionHistory.length === 0) {
      return [];
    }

    const emotionCounts: Record<string, number> = {};
    let total = 0;

    emotionHistory.forEach(prediction => {
      const emotion = prediction.emotion;
      if (emotion !== 'silence' && emotion !== 'error') {
        emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        total++;
      }
    });

    return Object.entries(emotionCounts)
      .map(([emotion, count]) => ({
        name: emotion,
        value: Math.round((count / total) * 100),
        color: EMOTION_COLORS[emotion] || '#8884d8',
        icon: EMOTION_ICONS[emotion] || '😐'
      }))
      .sort((a, b) => b.value - a.value);
  };

  const data = calculateDistribution();

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-500">No emotion data available</p>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium capitalize">
            {data.icon} {data.name}
          </p>
          <p className="text-2xl font-bold" style={{ color: data.color }}>
            {data.value}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value: string, entry: any) => (
              <span style={{ color: entry.color }}>
                {EMOTION_ICONS[value] || ''} {value.charAt(0).toUpperCase() + value.slice(1)}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Summary stats */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        {data.slice(0, 4).map((item) => (
          <div key={item.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span className="flex items-center gap-2">
              <span>{item.icon}</span>
              <span className="capitalize text-sm">{item.name}</span>
            </span>
            <span className="font-semibold" style={{ color: item.color }}>
              {item.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmotionDistribution;
