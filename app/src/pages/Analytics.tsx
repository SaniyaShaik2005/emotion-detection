import React, { useState } from 'react';
import { useAgentAnalytics, useAnalyticsSummary, useEmotionsTrend, useCalls } from '@/hooks/useApi';
import { EMOTION_COLORS, EMOTION_ICONS } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  Phone, Users, Clock, TrendingUp,
  BarChart3, Award, ThumbsUp, ThumbsDown
} from 'lucide-react';

const PERIODS = [
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
];

const Analytics: React.FC = () => {
  const [period, setPeriod] = useState(30);
  const [trendDays, setTrendDays] = useState(7);

  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(period);
  const { data: agentData, isLoading: agentLoading } = useAgentAnalytics(undefined, period);
  const { data: trendData, isLoading: trendLoading } = useEmotionsTrend(trendDays);
  const { data: callsData, isLoading: callsLoading } = useCalls(500, 0);

  // Prepare pie chart data from emotion distribution
  const pieData = React.useMemo(() => {
    if (!summary?.emotion_distribution) return [];
    return Object.entries(summary.emotion_distribution)
      .map(([emotion, pct]) => ({
        name: emotion,
        value: Math.round((pct as number) * 100),
        color: EMOTION_COLORS[emotion] || '#8884d8',
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 7);
  }, [summary]);

  // Prepare call volume from calls list
  const callVolumeData = React.useMemo(() => {
    if (!callsData?.calls) return [];
    const counts: Record<string, number> = {};
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - trendDays);
    callsData.calls
      .filter(c => new Date(c.start_time) >= cutoff)
      .forEach(c => {
        const day = new Date(c.start_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        counts[day] = (counts[day] || 0) + 1;
      });
    return Object.entries(counts)
      .map(([date, count]) => ({ date, count }))
      .slice(-trendDays);
  }, [callsData, trendDays]);

  // Prepare trend chart data (emotions over days)
  const trendChartData = React.useMemo(() => {
    if (!trendData?.trend) return [];
    return trendData.trend.map(d => ({
      ...d,
      date: new Date(d.date as string).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }));
  }, [trendData]);

  const trendEmotions = React.useMemo(() => {
    if (!trendData?.trend?.length) return [];
    const allKeys = new Set<string>();
    trendData.trend.forEach(d =>
      Object.keys(d).forEach(k => {
        if (k !== 'date' && k !== 'call_count') allKeys.add(k);
      })
    );
    return Array.from(allKeys);
  }, [trendData]);

  const formatDuration = (s: number) =>
    `${Math.floor(s / 60)}m ${s % 60}s`;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-gray-500 mt-1">Call center performance overview</p>
        </div>
        <Select value={String(period)} onValueChange={v => setPeriod(Number(v))}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PERIODS.map(p => (
              <SelectItem key={p.days} value={String(p.days)}>{p.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryLoading ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-28" />)
        ) : (
          <>
            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <Phone className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Calls</p>
                  <p className="text-3xl font-bold">{summary?.total_calls ?? 0}</p>
                  <p className="text-xs text-gray-400">{summary?.completed_calls ?? 0} completed</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Active Agents</p>
                  <p className="text-3xl font-bold">{summary?.total_agents ?? 0}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 bg-green-100 rounded-xl">
                  <Clock className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Duration</p>
                  <p className="text-2xl font-bold">
                    {summary ? formatDuration(Math.round(summary.avg_call_duration)) : '—'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 bg-orange-100 rounded-xl">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Positive Sentiment</p>
                  <p className="text-3xl font-bold">{summary?.positive_sentiment_rate ?? 0}%</p>
                  <p className="text-xs text-gray-400 capitalize">
                    Top: {summary?.top_emotion ? `${EMOTION_ICONS[summary.top_emotion]} ${summary.top_emotion}` : '—'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Call Volume */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-4 h-4" /> Call Volume
              </CardTitle>
              <Select value={String(trendDays)} onValueChange={v => setTrendDays(Number(v))}>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Last 7 days</SelectItem>
                  <SelectItem value="14">Last 14 days</SelectItem>
                  <SelectItem value="30">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {callsLoading ? (
              <Skeleton className="h-52" />
            ) : callVolumeData.length === 0 ? (
              <div className="h-52 flex items-center justify-center text-gray-400">
                No call data for this period
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={210}>
                <BarChart data={callVolumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Calls" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Emotion Distribution Pie */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Emotion Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            {summaryLoading ? (
              <Skeleton className="h-52" />
            ) : pieData.length === 0 ? (
              <div className="h-52 flex items-center justify-center text-gray-400">
                No emotion data yet
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <ResponsiveContainer width="55%" height={210}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                      dataKey="value" paddingAngle={3}>
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => `${v}%`} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex-1 space-y-1.5">
                  {pieData.map(d => (
                    <div key={d.name} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-1.5">
                        <span className="text-base">{EMOTION_ICONS[d.name]}</span>
                        <span className="capitalize text-gray-700">{d.name}</span>
                      </div>
                      <span className="font-semibold" style={{ color: d.color }}>{d.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Emotion Trends Over Time */}
      {trendEmotions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="w-4 h-4" /> Emotion Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trendLoading ? (
              <Skeleton className="h-56" />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend iconType="line" wrapperStyle={{ fontSize: 12 }} />
                  {trendEmotions.map(emotion => (
                    <Line key={emotion} type="monotone" dataKey={emotion}
                      stroke={EMOTION_COLORS[emotion] || '#8884d8'}
                      strokeWidth={2} dot={{ r: 3 }} name={emotion} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Agent Performance Table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Award className="w-4 h-4" /> Agent Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agentLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12" />)}
            </div>
          ) : !agentData?.analytics?.length ? (
            <div className="text-center py-8 text-gray-400">
              <Users className="w-10 h-10 mx-auto mb-2 opacity-40" />
              <p>No completed calls yet. Start a call to see agent analytics.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-3 pr-4 font-medium">Agent</th>
                    <th className="pb-3 pr-4 font-medium text-center">Calls</th>
                    <th className="pb-3 pr-4 font-medium text-center">Avg Duration</th>
                    <th className="pb-3 pr-4 font-medium text-center">
                      <span className="flex items-center justify-center gap-1">
                        <ThumbsUp className="w-3.5 h-3.5 text-green-500" /> Positive
                      </span>
                    </th>
                    <th className="pb-3 pr-4 font-medium text-center">
                      <span className="flex items-center justify-center gap-1">
                        <ThumbsDown className="w-3.5 h-3.5 text-red-500" /> Negative
                      </span>
                    </th>
                    <th className="pb-3 font-medium text-center">Satisfaction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {agentData.analytics.map((a) => (
                    <tr key={a.agent_name} className="hover:bg-gray-50">
                      <td className="py-3 pr-4 font-medium">{a.agent_name}</td>
                      <td className="py-3 pr-4 text-center">
                        <Badge variant="secondary">{a.total_calls}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-center text-gray-600">
                        {formatDuration(Math.round(a.avg_call_duration))}
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <span className="text-green-600 font-semibold">
                          {Math.round(a.positive_emotion_ratio * 100)}%
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <span className="text-red-500 font-semibold">
                          {Math.round(a.negative_emotion_ratio * 100)}%
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${a.avg_customer_satisfaction}%`,
                                backgroundColor: a.avg_customer_satisfaction >= 60 ? '#22c55e' : a.avg_customer_satisfaction >= 40 ? '#f59e0b' : '#ef4444'
                              }}
                            />
                          </div>
                          <span className="text-xs font-medium w-10">
                            {a.avg_customer_satisfaction}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Analytics;
