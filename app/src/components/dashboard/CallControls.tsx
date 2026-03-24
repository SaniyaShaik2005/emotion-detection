import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Phone, PhoneOff, Mic, MicOff, Loader2, User, Building2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface CallControlsProps {
  isConnected: boolean;
  isRecording: boolean;
  onStartCall: (agentName: string, customerName: string) => void;
  onEndCall: () => void;
}

export const CallControls: React.FC<CallControlsProps> = ({
  isConnected,
  isRecording,
  onStartCall,
  onEndCall
}) => {
  const { user } = useAuth();
  const [agentName, setAgentName] = useState(user?.name || 'Agent');
  const [customerName, setCustomerName] = useState('Customer');
  const [isStarting, setIsStarting] = useState(false);

  const handleStart = async () => {
    setIsStarting(true);
    try {
      await onStartCall(agentName, customerName);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isConnected ? (
            <>
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500" />
              </span>
              Call in Progress
            </>
          ) : (
            <>
              <Phone className="w-5 h-5" />
              Start New Call
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!isConnected ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="agent-name">Agent Name</Label>
              <Input
                id="agent-name"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="Enter agent name"
                disabled={isStarting}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-name">Customer Name</Label>
              <Input
                id="customer-name"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Enter customer name"
                disabled={isStarting}
              />
            </div>
            <Button 
              onClick={handleStart} 
              className="w-full"
              disabled={isStarting || !agentName.trim()}
            >
              {isStarting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Phone className="w-4 h-4 mr-2" />
                  Start Call
                </>
              )}
            </Button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <HoverCard>
                <HoverCardTrigger asChild>
                  <div className="bg-gray-50 hover:bg-gray-100 transition-colors p-3 rounded-lg cursor-pointer">
                    <p className="text-sm text-gray-500">Agent</p>
                    <p className="font-medium truncate">{agentName}</p>
                  </div>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <div className="flex justify-between space-x-4">
                    <Avatar>
                      <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${agentName}`} />
                      <AvatarFallback>{agentName.substring(0, 2).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div className="space-y-1 flex-1">
                      <h4 className="text-sm font-semibold">{agentName}</h4>
                      <p className="text-sm text-gray-500">Senior Support Specialist</p>
                      <div className="flex items-center pt-2">
                        <Building2 className="mr-2 h-4 w-4 opacity-70" />{" "}
                        <span className="text-xs text-gray-500">Tier 2 Technical Support</span>
                      </div>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>

              <HoverCard>
                <HoverCardTrigger asChild>
                  <div className="bg-gray-50 hover:bg-gray-100 transition-colors p-3 rounded-lg cursor-pointer">
                    <p className="text-sm text-gray-500">Customer</p>
                    <p className="font-medium truncate">{customerName}</p>
                  </div>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <div className="flex justify-between space-x-4">
                    <Avatar>
                      <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${customerName}&backgroundColor=e2e8f0`} />
                      <AvatarFallback>{customerName.substring(0, 2).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div className="space-y-1 flex-1">
                      <h4 className="text-sm font-semibold">{customerName}</h4>
                      <p className="text-sm text-gray-500">Verified User</p>
                      <div className="flex items-center pt-2">
                        <User className="mr-2 h-4 w-4 opacity-70" />{" "}
                        <span className="text-xs text-gray-500">Premium Account</span>
                      </div>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            </div>
            
            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
              {isRecording ? (
                <>
                  <Mic className="w-5 h-5 text-green-600 animate-pulse" />
                  <span className="text-green-700 font-medium">Recording...</span>
                </>
              ) : (
                <>
                  <MicOff className="w-5 h-5 text-gray-400" />
                  <span className="text-gray-500">Not recording</span>
                </>
              )}
            </div>

            <Button 
              onClick={onEndCall} 
              variant="destructive"
              className="w-full"
            >
              <PhoneOff className="w-4 h-4 mr-2" />
              End Call
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CallControls;
