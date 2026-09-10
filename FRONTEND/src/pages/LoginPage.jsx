import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Shield, Lock, Mail, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading, authError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState(null);

  const from = location.state?.from?.pathname || '/chat';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError('Please provide both email and password');
      return;
    }

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setLocalError(err.message || 'Invalid credentials or connection error');
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] px-4 py-8 relative">
      {/* Decorative Air-Gap Security Watermark */}
      <div className="absolute top-6 left-6 flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-[#0a1128] flex items-center justify-center text-blue-400">
          <Shield className="w-4 h-4 fill-blue-500/20" />
        </div>
        <span className="font-semibold text-xs tracking-tight text-slate-900">
          Sovereign AI Workbench
        </span>
      </div>

      <div className="w-full max-w-md bg-white border border-slate-200/90 rounded-2xl shadow-card p-6 sm:p-8 animate-in fade-in duration-300">
        {/* Card Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3 shadow-2xs">
            <Shield className="w-6 h-6 fill-blue-100" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Air-Gapped Operator Access
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Sign in to access confidential organizational intelligence.
          </p>
        </div>

        {/* Errors */}
        {(localError || authError) && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{localError || authError}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Organizational Email
            </label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@refinery.psu.gov"
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-xs"
              />
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="font-semibold text-slate-700">
                Security Password
              </label>
              <Link
                to="/forgot-password"
                className="text-[11px] text-blue-600 hover:underline"
              >
                Forgot Password?
              </Link>
            </div>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-xs"
              />
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full py-2.5 mt-2"
            isLoading={loading}
            icon={ArrowRight}
          >
            Authenticate Session
          </Button>
        </form>

        {/* Bottom Link */}
        <div className="mt-6 pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
          Need a provisioned operator account?{' '}
          <Link to="/register" className="text-blue-600 font-semibold hover:underline">
            Register Request
          </Link>
        </div>

        {/* Security Footer */}
        <div className="mt-4 text-center">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-800 text-[10px] font-mono rounded-full border border-emerald-200/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />
            100% On-Premise Execution
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
