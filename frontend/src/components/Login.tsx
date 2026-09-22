import { useState } from 'react';
import { Activity, Mail, KeyRound, ArrowRight } from 'lucide-react';

export function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
      const url = `${apiBase.startsWith('http') ? '' : 'http://'}${apiBase}/api/auth/request-otp`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to request OTP');
      }
      setStep(2);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
      const url = `${apiBase.startsWith('http') ? '' : 'http://'}${apiBase}/api/auth/verify-otp`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to verify OTP');
      }
      onLogin(data.token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="bg-card border border-gray-700 rounded-lg p-8 max-w-md w-full shadow-2xl">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <Activity className="text-cyan-400" size={32} />
          <h1 className="text-2xl font-bold tracking-wider font-mono text-white">FUSION ENGINE</h1>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 p-3 rounded mb-6 text-sm font-mono text-center">
            {error}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleRequestOtp} className="flex flex-col gap-4">
            <p className="text-gray-400 text-sm font-mono text-center mb-2">
              Enter your authorization email to receive a one-time passcode.
            </p>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="operator@aerospace.local"
                className="w-full bg-[#0b0f19] border border-gray-700 rounded p-3 pl-10 text-white font-mono focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
            <button
              disabled={loading || !email}
              className="mt-2 w-full bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? 'REQUESTING...' : 'REQUEST OTP'}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="flex flex-col gap-4">
            <p className="text-gray-400 text-sm font-mono text-center mb-2">
              OTP sent to <span className="text-cyan-400">{email}</span>
            </p>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
              <input
                type="text"
                required
                value={otp}
                onChange={e => setOtp(e.target.value)}
                placeholder="123456"
                className="w-full bg-[#0b0f19] border border-gray-700 rounded p-3 pl-10 text-white font-mono text-center tracking-widest text-xl focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
            <button
              disabled={loading || otp.length < 6}
              className="mt-2 w-full bg-emerald-600 hover:bg-emerald-500 text-white font-mono font-bold py-3 rounded flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? 'VERIFYING...' : 'AUTHORIZE'}
            </button>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="mt-2 text-xs text-gray-500 hover:text-gray-300 font-mono text-center underline"
            >
              Change Email
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
