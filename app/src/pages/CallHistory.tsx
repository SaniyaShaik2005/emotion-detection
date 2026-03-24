import React, { useState } from 'react';
import { useCalls, useCall, deleteCall, exportCall, getTranscript } from '@/hooks/useApi';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Phone,
  BarChart3,
  RefreshCw,
  MoreHorizontal,
  Download,
  Trash2,
  FileText,
  Volume2
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';
import { EMOTION_COLORS, EMOTION_ICONS } from '@/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CallHistory: React.FC = () => {
  const [page, setPage] = useState(0);
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [recordingError, setRecordingError] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const limit = 10;
  
  const { data, isLoading, error, refetch } = useCalls(limit, page * limit);
  const { data: selectedCallData, isLoading: isLoadingDetails } = useCall(selectedCallId);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const handleDelete = async (callId: string) => {
    if (!window.confirm("Are you sure you want to delete this record? This cannot be undone.")) return;
    
    try {
      setIsDeleting(callId);
      await deleteCall(callId);
      toast.success("Call record deleted successfully");
      refetch();
    } catch (err) {
      toast.error("Failed to delete record");
      console.error(err);
    } finally {
      setIsDeleting(null);
    }
  };

  const handleExport = async (callId: string) => {
    try {
      setIsExporting(callId);
      const data = await exportCall(callId);
      
      // Simple JSON download for now
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `call_export_${callId.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success("Call data exported successfully");
    } catch (err) {
      toast.error("Failed to export data");
      console.error(err);
    } finally {
      setIsExporting(null);
    }
  };

  const handleViewTranscript = async (callId: string) => {
    try {
      const data = await getTranscript(callId);
      setTranscript(data.transcript);
      setIsTranscriptOpen(true);
    } catch (err) {
      toast.error("Failed to load transcript");
      console.error(err);
    }
  };

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-500 mb-4">Error loading call history: {error}</p>
        <Button onClick={refetch}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Call History</h1>
        <Button onClick={refetch} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Recent Calls
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : data?.calls.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Phone className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No calls recorded yet</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Call ID</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Start Time</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Dominant Emotion</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.calls.map((call) => (
                    <TableRow key={call.call_id}>
                      <TableCell className="font-mono text-sm">
                        {call.call_id.slice(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-6 w-6">
                            <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${call.agent_name}`} />
                            <AvatarFallback className="text-[10px]">{call.agent_name.substring(0, 2)}</AvatarFallback>
                          </Avatar>
                          {call.agent_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-6 w-6">
                            <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${call.customer_name}&backgroundColor=e2e8f0`} />
                            <AvatarFallback className="text-[10px]">{call.customer_name.substring(0, 2)}</AvatarFallback>
                          </Avatar>
                          {call.customer_name}
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(call.start_time)}</TableCell>
                      <TableCell>{formatDuration(call.duration_seconds)}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(call.status)}>
                          {call.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {call.dominant_emotion ? (
                          <span 
                            className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                            style={{ 
                              backgroundColor: `${EMOTION_COLORS[call.dominant_emotion]}20`,
                              color: EMOTION_COLORS[call.dominant_emotion]
                            }}
                          >
                            {EMOTION_ICONS[call.dominant_emotion]}
                            {call.dominant_emotion}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Open menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => setSelectedCallId(call.call_id)}>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleViewTranscript(call.call_id)}>
                              <FileText className="mr-2 h-4 w-4" />
                              View Transcript
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleExport(call.call_id)}
                              disabled={isExporting === call.call_id}
                            >
                              <Download className="mr-2 h-4 w-4" />
                              {isExporting === call.call_id ? "Exporting..." : "Export JSON"}
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-red-600 focus:text-red-600"
                              onClick={() => handleDelete(call.call_id)}
                              disabled={isDeleting === call.call_id}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              {isDeleting === call.call_id ? "Deleting..." : "Delete Record"}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="mt-4 flex justify-end">
                <Pagination className="justify-end w-auto mx-0">
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious 
                        onClick={() => setPage(p => Math.max(0, p - 1))}
                        className={page === 0 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                      />
                    </PaginationItem>
                    
                    <PaginationItem>
                      <PaginationLink isActive>
                        {page + 1}
                      </PaginationLink>
                    </PaginationItem>
                    
                    <PaginationItem>
                      <PaginationNext 
                        onClick={() => setPage(p => p + 1)}
                        className={(!data || data.calls.length < limit) ? "pointer-events-none opacity-50" : "cursor-pointer"}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Call Details Dialog */}
      <Dialog open={!!selectedCallId} onOpenChange={() => { setSelectedCallId(null); setRecordingError(false); }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Call Details</DialogTitle>
          </DialogHeader>
          
          {isLoadingDetails ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : selectedCallData?.call ? (
            <div className="space-y-6">

              {/* Recording Player */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Volume2 className="w-4 h-4 text-gray-600" />
                  <span className="font-medium text-sm text-gray-700">Call Recording</span>
                </div>
                {recordingError ? (
                  <p className="text-sm text-gray-400 italic">No recording saved for this call.</p>
                ) : (
                  <audio
                    controls
                    className="w-full h-10"
                    src={`${API_BASE_URL}/api/calls/${selectedCallId}/recording`}
                    onError={() => setRecordingError(true)}
                    onPlay={() => setRecordingError(false)}
                  />
                )}
              </div>

              {/* Call Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Agent</p>
                  <p className="font-medium">{selectedCallData.call.agent_name}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Customer</p>
                  <p className="font-medium">{selectedCallData.call.customer_name}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Duration</p>
                  <p className="font-medium">
                    {formatDuration(selectedCallData.call.duration_seconds)}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Avg Confidence</p>
                  <p className="font-medium">
                    {Math.round((selectedCallData.call.avg_confidence || 0) * 100)}%
                  </p>
                </div>
              </div>

              {/* Emotion Distribution */}
              {selectedCallData.call.emotion_distribution && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Emotion Distribution</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selectedCallData.call.emotion_distribution)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .map(([emotion, percentage]) => (
                        <div 
                          key={emotion}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg"
                          style={{ backgroundColor: `${EMOTION_COLORS[emotion]}15` }}
                        >
                          <span>{EMOTION_ICONS[emotion]}</span>
                          <span className="capitalize font-medium">{emotion}</span>
                          <span 
                            className="font-bold"
                            style={{ color: EMOTION_COLORS[emotion] }}
                          >
                            {Math.round((percentage as number) * 100)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Emotion Timeline Chart */}
              {selectedCallData.emotions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Emotion Timeline</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={selectedCallData.emotions.map((e) => ({
                        time: e.time_offset_seconds,
                        confidence: Math.round(e.confidence * 100),
                        emotion: e.emotion
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="time" 
                          tickFormatter={(v) => `${v}s`}
                        />
                        <YAxis domain={[0, 100]} />
                        <Tooltip 
                          formatter={(value: number, _name: string, props: any) => [
                            `${value}%`,
                            props.payload.emotion
                          ]}
                          labelFormatter={(label) => `Time: ${label}s`}
                        />
                        <Line 
                          type="stepAfter" 
                          dataKey="confidence" 
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Emotion Log Table - Accordion */}
              {selectedCallData.emotions.length > 0 && (
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="emotion-timeline">
                    <AccordionTrigger className="text-lg font-semibold hover:no-underline px-1">
                      Detailed Emotion Timeline Log
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="max-h-64 overflow-y-auto mt-2 border rounded-md">
                        <Table>
                          <TableHeader className="bg-muted/50 sticky top-0">
                            <TableRow>
                              <TableHead>Time</TableHead>
                              <TableHead>Emotion</TableHead>
                              <TableHead>Confidence</TableHead>
                              <TableHead>Speech</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {selectedCallData.emotions.map((log, index) => (
                              <TableRow key={index}>
                                <TableCell className="font-mono">{log.time_offset_seconds.toFixed(1)}s</TableCell>
                                <TableCell>
                                  <span 
                                    className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium w-fit"
                                    style={{ 
                                      backgroundColor: `${EMOTION_COLORS[log.emotion]}20`,
                                      color: EMOTION_COLORS[log.emotion]
                                    }}
                                  >
                                    {EMOTION_ICONS[log.emotion]}
                                    {log.emotion}
                                  </span>
                                </TableCell>
                                <TableCell>
                                  {Math.round(log.confidence * 100)}%
                                </TableCell>
                                <TableCell>
                                  {log.is_speech ? (
                                    <Badge variant="default" className="bg-green-500">Yes</Badge>
                                  ) : (
                                    <Badge variant="secondary">No</Badge>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Transcript Dialog */}
      <Dialog open={isTranscriptOpen} onOpenChange={setIsTranscriptOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Call Transcript (Emotions)</DialogTitle>
          </DialogHeader>
          <div className="mt-4 bg-gray-50 p-6 rounded-lg border font-mono text-sm whitespace-pre-wrap max-h-[60vh] overflow-y-auto">
            {transcript || "Generating transcript..."}
          </div>
          <div className="flex justify-end mt-4">
            <Button onClick={() => setIsTranscriptOpen(false)}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CallHistory;
