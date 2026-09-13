import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Search,
  Filter,
  Shield,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Edit2,
  RefreshCw,
  Lock,
  Building,
  Check,
  X,
  AlertCircle,
} from 'lucide-react';
import adminApi from '../../api/adminApi';
import CreateUserModal from './CreateUserModal';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import Loader from '../common/Loader';

const UserManagementSection = () => {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({
    role: 'operator',
    department: '',
    isActive: true,
    newPassword: '',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState(null);
  const [editSuccess, setEditSuccess] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await adminApi.getUsers({
        search: search.trim() || undefined,
        limit: 100,
      });
      if (res && res.users) {
        setUsers(res.users);
        setTotal(res.total || res.users.length);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to fetch user directory from server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [search]);

  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setEditFormData({
      role: user.role || 'operator',
      department: user.department || '',
      isActive: typeof user.isActive === 'boolean' ? user.isActive : true,
      newPassword: '',
    });
    setEditError(null);
    setEditSuccess(null);
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    if (!editingUser) return;

    setEditLoading(true);
    setEditError(null);
    setEditSuccess(null);

    try {
      const payload = {
        role: editFormData.role,
        department: editFormData.department.trim() || undefined,
        isActive: editFormData.isActive,
        isAdmin: editFormData.role === 'admin',
      };

      if (editFormData.newPassword) {
        if (editFormData.newPassword.length < 8) {
          setEditError('New password must be at least 8 characters');
          setEditLoading(false);
          return;
        }
        payload.password = editFormData.newPassword;
      }

      await adminApi.updateUser(editingUser._id, payload);
      setEditSuccess('User updated successfully');

      // Refresh list
      fetchUsers();

      setTimeout(() => {
        setEditingUser(null);
      }, 1200);
    } catch (err) {
      setEditError(err.message || 'Failed to update user record');
    } finally {
      setEditLoading(false);
    }
  };

  // Filter users by selected role on client
  const filteredUsers = users.filter((u) => {
    if (roleFilter === 'all') return true;
    return u.role === roleFilter;
  });

  // Calculate quick metrics
  const activeCount = users.filter((u) => u.isActive !== false).length;
  const adminCount = users.filter((u) => u.isAdmin || u.role === 'admin').length;
  const operatorCount = users.filter((u) => u.role === 'operator').length;

  const getRoleBadgeVariant = (role) => {
    switch (role) {
      case 'admin':
        return 'purple';
      case 'engineer':
        return 'blue';
      case 'analyst':
        return 'warning';
      case 'viewer':
        return 'default';
      default:
        return 'sovereign';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3.5">
        <div className="p-4 bg-white border border-slate-200/90 rounded-xl shadow-subtle">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Total Operators
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{total}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Provisioned on-premise</div>
        </div>

        <div className="p-4 bg-white border border-slate-200/90 rounded-xl shadow-subtle">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Active Accounts
          </div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">{activeCount}</div>
          <div className="text-[10px] text-emerald-600/80 mt-0.5">Authorized for login</div>
        </div>

        <div className="p-4 bg-white border border-slate-200/90 rounded-xl shadow-subtle">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Administrators
          </div>
          <div className="text-2xl font-bold text-purple-600 mt-1">{adminCount}</div>
          <div className="text-[10px] text-purple-600/80 mt-0.5">Full governance rights</div>
        </div>

        <div className="p-4 bg-white border border-slate-200/90 rounded-xl shadow-subtle">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Operators & Staff
          </div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{operatorCount}</div>
          <div className="text-[10px] text-blue-600/80 mt-0.5">Execution clearance</div>
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="p-5">
        {/* Controls Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
          <div className="flex flex-1 items-center gap-2 max-w-md">
            <div className="relative flex-1">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search operators by name or email..."
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>

            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="all">All Roles</option>
              <option value="admin">Admins</option>
              <option value="operator">Operators</option>
              <option value="engineer">Engineers</option>
              <option value="analyst">Analysts</option>
              <option value="viewer">Viewers</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={RefreshCw}
              isLoading={loading}
              onClick={fetchUsers}
              title="Refresh user directory"
            >
              Refresh
            </Button>
            <Button
              size="sm"
              icon={UserPlus}
              onClick={() => setIsCreateModalOpen(true)}
            >
              Create New User
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 my-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Users Table */}
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-2.5 px-3">Operator Name</th>
                <th className="py-2.5 px-3">Email</th>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Created</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {loading && users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    <Loader text="Loading registered operators..." size="sm" />
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No operators match your search or filter.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => {
                  const firstName = u.fullName?.firstName || '';
                  const middleName = u.fullName?.middleName || '';
                  const lastName = u.fullName?.lastName || '';
                  const fullName = `${firstName} ${middleName ? middleName + ' ' : ''}${lastName}`.trim() || '—';
                  const initials = `${firstName[0] || ''}${lastName[0] || ''}`.toUpperCase() || 'U';
                  const isUserActive = typeof u.isActive === 'boolean' ? u.isActive : true;

                  return (
                    <tr key={u._id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-[11px] flex-shrink-0">
                            {initials}
                          </div>
                          <span className="font-semibold text-slate-900">{fullName}</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">
                        {u.email}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            u.isAdmin || u.role === 'admin'
                              ? 'bg-purple-100 text-purple-700'
                              : u.role === 'engineer'
                              ? 'bg-blue-100 text-blue-700'
                              : u.role === 'analyst'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {u.isAdmin && <Shield className="w-3 h-3 text-purple-600" />}
                          {u.role || 'operator'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {u.department || <span className="text-slate-400 italic">Unassigned</span>}
                      </td>
                      <td className="py-2.5 px-3">
                        {isUserActive ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200/80">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            Suspended
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 text-[11px] font-mono">
                        {u.createdAt ? new Date(u.createdAt).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => handleOpenEdit(u)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Modify user clearance or status"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Edit</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onUserCreated={(newUser) => {
          fetchUsers();
        }}
      />

      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div
            className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Edit2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Modify Operator Clearance
                  </h3>
                  <div className="text-[11px] text-slate-500 font-mono truncate max-w-[220px]">
                    {editingUser.email}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setEditingUser(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateUser} className="p-6 space-y-3.5 text-xs">
              {editError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{editError}</span>
                </div>
              )}

              {editSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>{editSuccess}</span>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Assigned Clearance Role
                </label>
                <select
                  value={editFormData.role}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, role: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-800"
                >
                  <option value="operator">Operator</option>
                  <option value="engineer">Engineer</option>
                  <option value="analyst">Analyst</option>
                  <option value="viewer">Viewer</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Department
                </label>
                <input
                  type="text"
                  value={editFormData.department}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, department: e.target.value })
                  }
                  placeholder="e.g. Cybersecurity, Operations"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Reset Password (leave empty to keep current)
                </label>
                <input
                  type="password"
                  minLength={8}
                  value={editFormData.newPassword}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, newPassword: e.target.value })
                  }
                  placeholder="New password (min 8 chars)"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg font-mono text-slate-800"
                />
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editFormData.isActive}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, isActive: e.target.checked })
                    }
                    className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                  />
                  <span className="font-semibold text-slate-800">
                    Account Active & Authorized to Sign In
                  </span>
                </label>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditingUser(null)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" isLoading={editLoading}>
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementSection;
