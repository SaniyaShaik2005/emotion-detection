import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Mic, Volume2, Bell, Brain, Info, Cpu, Globe
} from 'lucide-react';

function useSetting<T>(key: string, defaultVal: T): [T, (v: T) => void] {
  const [val, setVal] = useState<T>(() => {
    try {
      const s = localStorage.getItem(`setting_${key}`);
      return s !== null ? JSON.parse(s) : defaultVal;
    } catch { return defaultVal; }
  });
  const update = (v: T) => {
    setVal(v);
    localStorage.setItem(`setting_${key}`, JSON.stringify(v));
  };
  return [val, update];
}

const Settings: React.FC = () => {
  const [noiseSuppression, setNoiseSuppression] = useSetting('noise_suppression', true);
  const [echoCancellation, setEchoCancellation] = useSetting('echo_cancellation', true);
  const [soundAlerts, setSoundAlerts] = useSetting('sound_alerts', false);
  const [negativeAlert, setNegativeAlert] = useSetting('negative_alert', true);
  const [confidenceThreshold, setConfidenceThreshold] = useSetting('confidence_threshold', '60');

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-gray-500 mt-1">Configure your EmoDetect experience</p>
      </div>

      {/* Audio Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Mic className="w-4 h-4" /> Audio Settings
          </CardTitle>
          <CardDescription>Control microphone input quality</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Noise Suppression</Label>
              <p className="text-xs text-gray-500">Filter background noise from microphone input</p>
            </div>
            <Switch checked={noiseSuppression} onCheckedChange={setNoiseSuppression} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Echo Cancellation</Label>
              <p className="text-xs text-gray-500">Prevent microphone from picking up speaker audio</p>
            </div>
            <Switch checked={echoCancellation} onCheckedChange={setEchoCancellation} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Sample Rate</Label>
              <p className="text-xs text-gray-500">Audio capture rate (fixed for model compatibility)</p>
            </div>
            <Badge variant="secondary">16,000 Hz</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Detection Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="w-4 h-4" /> Detection Settings
          </CardTitle>
          <CardDescription>Tune how emotion predictions are made</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Confidence Threshold</Label>
              <p className="text-xs text-gray-500">Minimum confidence to display a prediction</p>
            </div>
            <Select value={confidenceThreshold} onValueChange={setConfidenceThreshold}>
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="40">40%</SelectItem>
                <SelectItem value="50">50%</SelectItem>
                <SelectItem value="60">60%</SelectItem>
                <SelectItem value="70">70%</SelectItem>
                <SelectItem value="80">80%</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Context Window</Label>
              <p className="text-xs text-gray-500">Audio accumulated before each prediction</p>
            </div>
            <Badge variant="secondary">2 seconds</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bell className="w-4 h-4" /> Notifications
          </CardTitle>
          <CardDescription>Choose when to receive in-app alerts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Sound Alerts</Label>
              <p className="text-xs text-gray-500">Play a sound when emotion changes significantly</p>
            </div>
            <Switch checked={soundAlerts} onCheckedChange={setSoundAlerts} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Negative Emotion Alert</Label>
              <p className="text-xs text-gray-500">Highlight when angry or frustrated emotion is detected</p>
            </div>
            <Switch checked={negativeAlert} onCheckedChange={setNegativeAlert} />
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="w-4 h-4" /> About
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center justify-between text-gray-600">
            <span className="flex items-center gap-2"><Globe className="w-4 h-4" /> Version</span>
            <Badge variant="outline">1.0.0</Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between text-gray-600">
            <span className="flex items-center gap-2"><Brain className="w-4 h-4" /> Emotion Model</span>
            <span className="text-gray-400 text-xs">wav2vec2-lg-xlsr (HuggingFace)</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between text-gray-600">
            <span className="flex items-center gap-2"><Cpu className="w-4 h-4" /> Backend</span>
            <span className="text-gray-400 text-xs">FastAPI + SQLite</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between text-gray-600">
            <span className="flex items-center gap-2"><Volume2 className="w-4 h-4" /> Emotions Detected</span>
            <span className="text-gray-400 text-xs">neutral · happy · sad · angry · fearful · disgust · surprised</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
