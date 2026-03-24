import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Phone, CheckCircle2 } from 'lucide-react';

const benefits = [
  'Real-time speech emotion recognition',
  'Supports 7 distinct emotion categories',
  'Full call recording & playback',
  'Per-agent performance analytics',
  'No cloud required — runs locally',
];

const Signup: React.FC = () => {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) { setError('Passwords do not match'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      await signup(name, email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-purple-600 via-purple-700 to-blue-800 p-12 flex-col justify-between text-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
            <Phone className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold">EmoDetect</span>
        </div>

        <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold leading-tight">
              Start detecting emotions<br />
              <span className="text-purple-200">in real time today.</span>
            </h1>
            <p className="mt-4 text-purple-100 text-lg">
              Join your team on EmoDetect and transform how you understand customer interactions.
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-purple-200 text-sm font-medium uppercase tracking-wide">What you get</p>
            {benefits.map(b => (
              <div key={b} className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
                <span className="text-purple-100 text-sm">{b}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-purple-300 text-sm">© 2024 EmoDetect. All rights reserved.</p>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">EmoDetect</span>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-gray-900">Create your account</h2>
            <p className="text-gray-500 mt-2">Get started in less than a minute</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-700">Full Name</Label>
              <Input placeholder="Jane Smith" value={name} onChange={e => setName(e.target.value)} className="h-11" required disabled={loading} />
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-700">Work Email</Label>
              <Input type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} className="h-11" required disabled={loading} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-700">Password</Label>
                <Input type="password" placeholder="Min. 6 chars" value={password} onChange={e => setPassword(e.target.value)} className="h-11" required disabled={loading} />
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-700">Confirm</Label>
                <Input type="password" placeholder="Repeat password" value={confirm} onChange={e => setConfirm(e.target.value)} className="h-11" required disabled={loading} />
              </div>
            </div>

            <Button type="submit" className="w-full h-11 text-base" disabled={loading}>
              {loading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Creating account…</>
              ) : 'Create Account'}
            </Button>

            <p className="text-center text-xs text-gray-400">
              By creating an account you agree to our Terms of Service.
            </p>
          </form>

          <div className="text-center">
            <span className="text-gray-500 text-sm">Already have an account? </span>
            <Link to="/login" className="text-blue-600 font-semibold text-sm hover:underline">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
