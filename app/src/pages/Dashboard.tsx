import React, { useState, useCallback } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { CallControls } from '@/components/dashboard/CallControls';
import { CurrentEmotion } from '@/components/dashboard/CurrentEmotion';
import { EmotionGraph } from '@/components/dashboard/EmotionGraph';
import { EmotionDistribution } from '@/components/dashboard/EmotionDistribution';
import { EmotionTimeline } from '@/components/dashboard/EmotionTimeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Activity, 
  TrendingUp, 
  PieChart, 
  Clock, 
  BarChart3,
  AlertCircle,
  Wifi,
  WifiOff,
  Info
} from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const Dashboard: React.FC = () => {
  const [, setCallId] = useState<string | null>(null);
  
  const {
    isConnected,
    isRecording,
    lastEmotion,
    emotionHistory,
    error,
    startCall,
    stopCall,
    connect
  } = useWebSocket();

  const handleStartCall = useCallback(async (agentName: string, customerName: string) => {
    try {
      const newCallId = await startCall(agentName, customerName);
      setCallId(newCallId);
      await connect(newCallId);
    } catch (err) {
      console.error('Failed to start call:', err);
    }
  }, [startCall, connect, setCallId]);

  const handleEndCall = useCallback(() => {
    stopCall();
    setCallId(null);
  }, [stopCall, setCallId]);

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (emotionHistory.length === 0) {
      return {
        totalDetections: 0,
        avgConfidence: 0,
        dominantEmotion: '-',
        speechRatio: 0
      };
    }

    const total = emotionHistory.length;
    const avgConfidence = emotionHistory.reduce((sum, e) => sum + e.confidence, 0) / total;
    
    // Find dominant emotion
    const emotionCounts: Record<string, number> = {};
    emotionHistory.forEach(e => {
      emotionCounts[e.emotion] = (emotionCounts[e.emotion] || 0) + 1;
    });
    const dominantEmotion = Object.entries(emotionCounts)
      .sort(([, a], [, b]) => b - a)[0]?.[0] || '-';

    const speechCount = emotionHistory.filter(e => e.is_speech).length;
    const speechRatio = (speechCount / total) * 100;

    return {
      totalDetections: total,
      avgConfidence: Math.round(avgConfidence * 100),
      dominantEmotion,
      speechRatio: Math.round(speechRatio)
    };
  }, [emotionHistory]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Real-Time Emotion Detection</h1>
          <p className="text-gray-500 mt-1">
            Monitor customer emotions during live calls
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Badge className="bg-green-500 flex items-center gap-1">
              <Wifi className="w-3 h-3" />
              Connected
            </Badge>
          ) : (
            <Badge variant="secondary" className="flex items-center gap-1">
              <WifiOff className="w-3 h-3" />
              Disconnected
            </Badge>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Stats Overview */}
      {isConnected && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Detections</p>
                <p className="text-2xl font-bold">{stats.totalDetections}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <p className="text-sm text-gray-500">Avg Confidence</p>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="w-3.5 h-3.5 text-gray-400 cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Average confidence score of all emotion predictions in this call</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <p className="text-2xl font-bold">{stats.avgConfidence}%</p>
                </div>
              </div>
              <Progress value={stats.avgConfidence} className="h-1.5 mt-2" />
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <PieChart className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Dominant</p>
                <p className="text-lg font-bold capitalize">{stats.dominantEmotion}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Clock className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <p className="text-sm text-gray-500">Speech Ratio</p>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="w-3.5 h-3.5 text-gray-400 cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Percentage of call time where human speech was detected vs silence/noise</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <p className="text-2xl font-bold">{stats.speechRatio}%</p>
                </div>
              </div>
              <Progress value={stats.speechRatio} className="h-1.5 mt-2 [&>div]:bg-orange-500 bg-orange-100/50" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Call Controls & Current Emotion */}
        <div className="space-y-6">
          <CallControls
            isConnected={isConnected}
            isRecording={isRecording}
            onStartCall={handleStartCall}
            onEndCall={handleEndCall}
          />
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Current Emotion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CurrentEmotion 
                prediction={lastEmotion} 
                isRecording={isRecording}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Visualizations */}
        <div className="lg:col-span-2 space-y-6 flex flex-col">
          <Tabs defaultValue="timeline" className="w-full flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="w-5 h-5" /> Analytics View
              </h2>
              <TabsList>
                <TabsTrigger value="timeline">Time Series</TabsTrigger>
                <TabsTrigger value="distribution">Distributions</TabsTrigger>
              </TabsList>
            </div>
            
            <TabsContent value="timeline" className="flex-1 mt-0 outline-none">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-medium">Confidence History</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[250px]">
                      <EmotionGraph emotionHistory={emotionHistory} />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-medium">Segment Sequence</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EmotionTimeline emotionHistory={emotionHistory} />
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            
            <TabsContent value="distribution" className="flex-1 mt-0 outline-none">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle className="text-base font-medium">Overall Proportions</CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-center min-h-[350px]">
                  <div className="w-full max-w-md">
                    <EmotionDistribution emotionHistory={emotionHistory} />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
