import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  Users,
  Check,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import settingApi from '../api/settingApi';
import UserManagementSection from '../components/admin/UserManagementSection';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

const SettingsPage = () => {
  const { user, logout, changePassword } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const isAdmin = user?.isAdmin || user?.role === 'admin';
  const currentTab = searchParams.get('tab') || 'general';

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
          value: 'http://localhost:11434',
          category: 'ai',
          description: 'Host Windows endpoint for local Ollama model runtime.',
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

  const userFirstName = user?.fullName?.firstName || '';
  const userMiddleName = user?.fullName?.middleName || '';
  const userLastName = user?.fullName?.lastName || '';
  const userFullName = userFirstName
    ? `${userFirstName} ${userMiddleName ? userMiddleName + ' ' : ''}${userLastName}`.trim()
    : user?.email || 'Operator';
  const userInitials = userFirstName
    ? `${userFirstName[0]}${userLastName ? userLastName[0] : ''}`.toUpperCase()
    : 'OP';
  const userRole = user?.role ? user.role.toUpperCase() : 'OPERATOR';

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-slate-700" />
          Settings & Sovereign Administration
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Manage authenticated operator identity, security credentials, and air-gapped cluster policies.
        </p>
      </div>

      {/* Tabs Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setSearchParams({ tab: 'general' })}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            currentTab === 'general'
              ? 'bg-blue-50 text-blue-700 shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <User className="w-4 h-4" />
          <span>Profile & Identity</span>
        </button>

        <button
          onClick={() => setSearchParams({ tab: 'security' })}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            currentTab === 'security'
              ? 'bg-blue-50 text-blue-700 shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Lock className="w-4 h-4" />
          <span>Security Credentials</span>
        </button>

        <button
          onClick={() => setSearchParams({ tab: 'cluster' })}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            currentTab === 'cluster'
              ? 'bg-blue-50 text-blue-700 shadow-2xs'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Server className="w-4 h-4" />
          <span>Cluster Parameters</span>
        </button>

        {/* Admin-only User Management Tab */}
        {isAdmin && (
          <button
            onClick={() => setSearchParams({ tab: 'users' })}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
              currentTab === 'users'
                ? 'bg-purple-50 text-purple-700 shadow-2xs ring-1 ring-purple-200'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Users className="w-4 h-4 text-purple-600" />
            <span>User Management</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 bg-purple-100 text-purple-700 rounded">
              ADMIN
            </span>
          </button>
        )}
      </div>

      {/* Tab 1: Profile & Identity */}
      {currentTab === 'general' && (
        <div className="space-y-6 animate-in fade-in duration-150">
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-base shadow-sm ring-2 ring-slate-200">
                  {userInitials}
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    {userFullName}
                  </h2>
                  <div className="text-xs text-slate-500 font-mono">
                    {user?.email || 'Authenticated Operator'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={isAdmin ? 'purple' : 'sovereign'} size="md">
                  {userRole}
                </Badge>
                {isAdmin && (
                  <Badge variant="blue" size="md">
                    ADMIN CLEARANCE
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

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-5 text-xs font-mono">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <span className="text-slate-400 block text-[10px] font-bold uppercase tracking-wider">
                  DEPARTMENT
                </span>
                <span className="font-semibold text-slate-800 mt-1 block">
                  {user?.department || <span className="text-slate-400 italic">Unassigned</span>}
                </span>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <span className="text-slate-400 block text-[10px] font-bold uppercase tracking-wider">
                  ACCOUNT STATUS
                </span>
                <span className="font-semibold text-emerald-600 mt-1 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  {user?.isActive !== false ? 'Active & Authorized' : 'Suspended'}
                </span>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
                <span className="text-slate-400 block text-[10px] font-bold uppercase tracking-wider">
                  MEMBER SINCE
                </span>
                <span className="font-semibold text-slate-800 mt-1 block">
                  {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Active Session'}
                </span>
              </div>
            </div>
          </Card>

          {/* If admin, quick banner to jump to User Management */}
          {isAdmin && (
            <div className="p-4 bg-purple-50/70 border border-purple-200/90 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs text-purple-900">
                    Administrator Governance Privileges Active
                  </div>
                  <div className="text-[11px] text-purple-700">
                    You have clearance to provision, inspect, and modify operator credentials across this node.
                  </div>
                </div>
              </div>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setSearchParams({ tab: 'users' })}
                className="bg-white border-purple-200 text-purple-700 hover:bg-purple-100"
              >
                Open User Management
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Security Credentials */}
      {currentTab === 'security' && (
        <Card className="p-6 animate-in fade-in duration-150">
          <h3 className="text-sm font-bold text-slate-900 mb-1 flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-600" />
            Update Security Credentials
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Password updates require direct bcrypt re-hashing on the sovereign MongoDB database.
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

          <form onSubmit={handlePasswordChange} className="space-y-3.5 text-xs max-w-md">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Current Password *
              </label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-slate-800"
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
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-slate-800"
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
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-slate-800"
              />
            </div>

            <Button type="submit" size="sm" isLoading={pwLoading}>
              Change Password
            </Button>
          </form>
        </Card>
      )}

      {/* Tab 3: Cluster Parameters */}
      {currentTab === 'cluster' && (
        <Card className="p-6 animate-in fade-in duration-150">
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
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg bg-white font-mono text-xs text-slate-800"
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
      )}

      {/* Tab 4: Admin User Management */}
      {currentTab === 'users' && isAdmin && (
        <UserManagementSection />
      )}
    </div>
  );
};

export default SettingsPage;
