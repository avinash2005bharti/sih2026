import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  ShieldAlert,
  Lock,
  Mail,
  User,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  UserPlus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';

const ROLES = [
  { value: 'operator', label: 'Operator' },
  { value: 'engineer', label: 'Engineer' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'viewer', label: 'Viewer' },
  { value: 'admin', label: 'Administrator' },
];

const RegisterPage = () => {
  const navigate = useNavigate();
  const { user, register, loading } = useAuth();

  const isAdmin = user?.isAdmin || user?.role === 'admin';

  const [formData, setFormData] = useState({
    firstName: '',
    middleName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'operator',
    department: '',
  });

  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // If not logged in or not admin, show restricted screen
  if (!user || !isAdmin) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] px-4 py-8 relative">
        <div className="w-full max-w-md bg-white border border-slate-200/90 rounded-2xl shadow-card p-6 sm:p-8 text-center animate-in fade-in duration-300">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-3">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">
            Administrator Clearance Required
          </h2>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Per sovereign security policy, operator account provisioning is restricted exclusively to authorized System Administrators.
          </p>

          <div className="mt-6 pt-5 border-t border-slate-100 flex flex-col gap-2">
            {!user ? (
              <Button
                className="w-full"
                onClick={() => navigate('/login')}
              >
                Sign In With Existing Account
              </Button>
            ) : (
              <Button
                className="w-full"
                onClick={() => navigate('/chat')}
              >
                Return to AI Workbench
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!formData.firstName.trim() || !formData.lastName.trim() || !formData.email.trim() || !formData.password) {
      setErrorMsg('All required fields must be completed');
      return;
    }

    if (formData.password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setErrorMsg('Passwords do not match');
      return;
    }

    try {
      const payload = {
        email: formData.email.trim().toLowerCase(),
        fullName: {
          firstName: formData.firstName.trim(),
          middleName: formData.middleName.trim() || undefined,
          lastName: formData.lastName.trim(),
        },
        password: formData.password,
        role: formData.role,
        department: formData.department.trim() || undefined,
        isAdmin: formData.role === 'admin',
      };

      const res = await register(payload);
      setSuccessMsg(res.message || 'Operator provisioned successfully.');
      setTimeout(() => navigate('/settings?tab=users'), 1500);
    } catch (err) {
      setErrorMsg(
        err.message ||
          'Failed to provision operator. Check network connection or permissions.'
      );
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] px-4 py-8 relative">
      <div className="w-full max-w-xl bg-white border border-slate-200/90 rounded-2xl shadow-card p-6 sm:p-8 animate-in fade-in duration-300">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center font-bold">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Provision Sovereign Operator
              </h2>
              <p className="text-xs text-slate-500">
                Authorized administrator credential issuance.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/settings?tab=users')}
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back</span>
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                First Name *
              </label>
              <input
                type="text"
                required
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Middle Name
              </label>
              <input
                type="text"
                value={formData.middleName}
                onChange={(e) => setFormData({ ...formData, middleName: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Last Name *
              </label>
              <input
                type="text"
                required
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Organizational Email *
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="operator@sovereign.defense.gov"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-slate-800"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Master Password *
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="At least 8 characters"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-slate-800"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Confirm Password *
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                placeholder="Repeat password"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-slate-800"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Role Clearance *
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-800 font-medium"
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                placeholder="e.g. Operations"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800"
              />
            </div>
          </div>

          <Button type="submit" className="w-full py-2.5 mt-2" isLoading={loading}>
            Provision Operator Account
          </Button>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage;
