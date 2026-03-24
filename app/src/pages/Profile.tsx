import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { User, Mail, Shield, CheckCircle2, Loader2, KeyRound } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const Profile: React.FC = () => {
  const { user, token } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name: name.trim() }),
      });
      if (!res.ok) throw new Error('Update failed');
      // Refresh user in localStorage with new name
      const stored = localStorage.getItem('auth_user');
      if (stored) {
        const u = JSON.parse(stored);
        u.name = name.trim();
        localStorage.setItem('auth_user', JSON.stringify(u));
      }
      setSaveMsg({ type: 'ok', text: 'Name updated successfully! Refresh to see it in the sidebar.' });
    } catch {
      setSaveMsg({ type: 'err', text: 'Failed to save. Try again.' });
    } finally {
      setSaving(false);
    }
  };

  const initials = user?.name?.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U';

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-gray-500 mt-1">Manage your account information</p>
      </div>

      {/* Avatar Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-5">
            <Avatar className="h-20 w-20 border-4 border-white shadow-md">
              <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${user?.name}&backgroundColor=3b82f6`} />
              <AvatarFallback className="text-2xl font-bold bg-blue-100 text-blue-600">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{user?.name}</h2>
              <p className="text-gray-500 text-sm">{user?.email}</p>
              <Badge className="mt-2 capitalize">{user?.role || 'agent'}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Name */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="w-4 h-4" /> Display Name
          </CardTitle>
          <CardDescription>This name appears in call records and analytics.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveName} className="flex gap-3">
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your full name"
              className="flex-1"
              required
            />
            <Button type="submit" disabled={saving || name === user?.name}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
            </Button>
          </form>
          {saveMsg && (
            <Alert className={`mt-3 ${saveMsg.type === 'ok' ? 'border-green-200 bg-green-50' : 'border-red-200'}`} variant={saveMsg.type === 'err' ? 'destructive' : 'default'}>
              {saveMsg.type === 'ok' && <CheckCircle2 className="h-4 w-4 text-green-600" />}
              <AlertDescription className={saveMsg.type === 'ok' ? 'text-green-700' : ''}>{saveMsg.text}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="w-4 h-4" /> Account Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-gray-700">Email address</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
            <Badge variant="secondary">Verified</Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-gray-700">Role</p>
              <p className="text-sm text-gray-500 capitalize">{user?.role || 'Agent'}</p>
            </div>
            <Shield className="w-4 h-4 text-gray-400" />
          </div>
        </CardContent>
      </Card>

      {/* Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <KeyRound className="w-4 h-4" /> Password
          </CardTitle>
          <CardDescription>Password changes are not yet supported via the UI.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <Input type="password" value="••••••••••" readOnly className="flex-1 cursor-not-allowed" />
            <Button variant="outline" disabled>Change Password</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Profile;
