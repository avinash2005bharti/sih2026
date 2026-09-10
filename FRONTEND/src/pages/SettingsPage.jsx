import React, { useState, useEffect } from 'react';
import {
  Settings,
  User,
  Lock,
  Shield,
  Server,
  Save,
  LogOut,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import settingApi from '../api/settingApi';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

const SettingsPage = () => {
  const { user, logout, changePassword } = useAuth();

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [pwSuccess, setPwSuccess] = useState(null);
  const [pwError, setPwError] = useState(null);

  // System settings state
  const [settingsList, setSettingsList] = useState([]);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [savingKey, setSavingKey] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setSettingsLoading(true);
    try {
      const res = await settingApi.getSettings();
      if (res && res.settings) {
        setSettingsList(res.settings);
      }
    } catch (e) {
      console.warn('Settings API offline, using sovereign defaults:', e.message);
      setSettingsList([
        {
          key: 'AIRGAP_ENFORCEMENT_LEVEL',
          value: 'STRICT_AIRGAP_FIPS_L4',
          category: 'security',
          description: 'Hardware firewall drops all packets outside the on-premise subnet.',
        },
        {
          key: 'LOCAL_OLLAMA_ENDPOINT',
          value: 'http://127.0.0.1:11434',
          category: 'ai',
          description: 'Loopback endpoint for Ollama model runtime.',
        },
        {
          key: 'PYTHON_AI_SERVICE_URL',
          value: 'http://127.0.0.1:8000',
          category: 'orchestrator',
          description: 'FastAPI LangGraph multi-agent service coordinator.',
        },
      ]);
    } finally {
      setSettingsLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwError(null);
    setPwSuccess(null);

    if (newPassword.length < 8) {
      setPwError('New password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPwError('New password and confirmation do not match');
      return;
    }

    setPwLoading(true);
    try {
      const res = await changePassword(currentPassword, newPassword);
      setPwSuccess(res.message || 'Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPwError(err.message || 'Failed to change password');
    } finally {
      setPwLoading(false);
    }
  };

  const handleSaveSetting = async (item) => {
    setSavingKey(item.key);
    setStatusMsg(null);
    try {
      await settingApi.saveSetting(item.key, {
        value: item.value,
        category: item.category,
        description: item.description,
      });
      setStatusMsg(`Setting ${item.key} saved.`);
      setTimeout(() => setStatusMsg(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to update setting');
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-slate-700" />
          Settings & Sovereign Administration
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Manage operator authentication, cluster security policies, and air-gapped endpoints.
        </p>
      </div>

      {/* User Profile Card */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-base shadow-sm ring-2 ring-slate-200">
              {user?.fullName?.firstName ? user.fullName.firstName[0] : 'E'}
              {user?.fullName?.lastName ? user.fullName.lastName[0] : 'R'}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                {user?.fullName?.firstName
                  ? `${user.fullName.firstName} ${user.fullName.lastName || ''}`
                  : 'Elena Rostova'}
              </h2>
              <div className="text-xs text-slate-500 font-mono">
                {user?.email || 'elena.rostova@sovereign.defense.gov'}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="sovereign" size="md">
              {user?.role?.toUpperCase() || 'ANALYST'}
            </Badge>
            {user?.isAdmin && (
              <Badge variant="blue" size="md">
                ADMIN
              </Badge>
            )}
            <Button
              variant="secondary"
              size="sm"
              icon={LogOut}
              onClick={logout}
              className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 border-rose-200"
            >
              Sign Out
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 text-xs font-mono">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block text-[10px]">DEPARTMENT</span>
            <span className="font-semibold text-slate-800">
              {user?.department || 'Systems Compliance & Safety'}
            </span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
            <span className="text-slate-400 block text-[10px]">ORGANIZATION TIER</span>
            <span className="font-semibold text-slate-800">
              Confidential PSU / Defense Grade
            </span>
          </div>
        </div>
      </Card>

      {/* Security & Password Change */}
      <Card className="p-6">
        <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
          <Lock className="w-4 h-4 text-blue-600" />
          Update Security Credentials
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Password updates require direct bcrypt re-hashing on the sovereign database.
        </p>

        {pwSuccess && (
          <div className="p-3 mb-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{pwSuccess}</span>
          </div>
        )}

        {pwError && (
          <div className="p-3 mb-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{pwError}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-3 text-xs max-w-md">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Current Password *
            </label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              New Password (minimum 8 characters) *
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Confirm New Password *
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <Button type="submit" size="sm" isLoading={pwLoading}>
            Change Password
          </Button>
        </form>
      </Card>

      {/* System Settings Key-Value Editor */}
      <Card className="p-6">
        <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
          <Server className="w-4 h-4 text-emerald-600" />
          Air-Gapped Cluster Parameters
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Direct configuration keys stored in MongoDB <code className="font-mono text-[11px]">SystemSetting</code> collection.
        </p>

        {statusMsg && (
          <div className="p-2.5 mb-3 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-mono">
            ✓ {statusMsg}
          </div>
        )}

        <div className="space-y-4">
          {settingsList.map((item, idx) => (
            <div
              key={item.key || idx}
              className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-slate-800">
                  {item.key}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-200 text-slate-700 rounded uppercase">
                  {item.category || 'system'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">{item.description}</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={item.value}
                  onChange={(e) => {
                    const updated = [...settingsList];
                    updated[idx].value = e.target.value;
                    setSettingsList(updated);
                  }}
                  className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg bg-white font-mono text-xs"
                />
                <Button
                  size="sm"
                  variant="secondary"
                  icon={Save}
                  isLoading={savingKey === item.key}
                  onClick={() => handleSaveSetting(item)}
                >
                  Save
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default SettingsPage;
