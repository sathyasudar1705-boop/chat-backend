import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Loader, AlertCircle, MessageSquare, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Incorrect email or password.');
      localStorage.setItem('token', data.access_token);
      navigate('/chat');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex font-sans page-fade"
         style={{ background: 'linear-gradient(135deg, #F0F7FF 0%, #F8FAFC 60%, #F0FDF4 100%)' }}>

      {/* Left decorative panel */}
      <div className="hidden lg:flex flex-col justify-between w-96 p-10 text-white shadow-saas-xl relative overflow-hidden"
           style={{ background: 'linear-gradient(180deg, #1e3a5f 0%, #1e3050 100%)' }}>
        
        {/* Subtle decorative background glow in the panel */}
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-2xl" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-indigo-500/10 rounded-full blur-2xl" />

        <div className="flex items-center gap-2.5 relative z-10 cursor-pointer" onClick={() => navigate('/')}>
          <img src="/logo.png" className="w-9 h-9 rounded-xl object-cover" alt="Logo" />
          <span className="font-bold text-lg tracking-tight">Indya AI</span>
        </div>
        
        <div className="relative z-10">
          <span className="text-[10px] font-bold tracking-widest uppercase text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-full">
            Indya AI Platform
          </span>
          <blockquote className="text-xl font-bold leading-tight mt-4 mb-3">
            One interface.<br/>Multiple AI engines.<br/>Zero friction.
          </blockquote>
          <p className="text-slate-300 text-xs leading-relaxed">
            Access Gemini, Groq, Mistral, and more—from one clean, private, and secure chat space.
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          {['G', 'M', 'C'].map((l, i) => (
            <div key={i} className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold text-white border border-white/10 shadow-sm">{l}</div>
          ))}
          <span className="text-slate-300 text-xs font-medium">+2 more providers</span>
        </div>
      </div>

      {/* Right auth form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 relative">
        {/* Subtle background blur spots */}
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-blue-100/40 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-emerald-100/30 rounded-full blur-3xl -z-10" />

        {/* Mobile logo */}
        <div className="flex lg:hidden items-center gap-2.5 mb-8 cursor-pointer" onClick={() => navigate('/')}>
          <img src="/logo.png" className="w-9 h-9 rounded-xl object-cover shadow-saas-sm" alt="Logo" />
          <span className="font-bold text-lg text-text-primary tracking-tight">Indya AI</span>
        </div>

        <div className="w-full max-w-md bg-white/80 backdrop-blur-md border border-slate-200/60 rounded-3xl shadow-saas-xl p-8 sm:p-10">
          {/* Header accent stripe */}
          <div className="h-1.5 w-12 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 mb-6" />
          <h2 className="text-2xl font-extrabold text-text-primary tracking-tight mb-1">Welcome back</h2>
          <p className="text-sm text-text-muted mb-8">Sign in to your account to continue</p>

          {error && (
            <div className="mb-6 flex items-start gap-2.5 p-3.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 animate-fade-in">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Email address</label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center pointer-events-none">
                  <Mail className="w-4 h-4 text-slate-400" />
                </div>
                <input
                  type="email" required value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-11 pr-4 py-3 text-sm text-text-primary bg-slate-50/50 border border-slate-200 rounded-xl input-focus placeholder:text-slate-400"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">Password</label>
              </div>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center pointer-events-none">
                  <Lock className="w-4 h-4 text-slate-400" />
                </div>
                <input
                  type="password" required value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 text-sm text-text-primary bg-slate-50/50 border border-slate-200 rounded-xl input-focus placeholder:text-slate-400"
                />
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all btn-hover-scale flex items-center justify-center gap-2 shadow-md hover:shadow-lg mt-2"
            >
              {loading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center text-sm text-text-muted">
            Don't have an account?{' '}
            <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">
              Create one free
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
