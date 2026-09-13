import React, { createContext, useContext, useState, useEffect } from 'react';
import authApi from '../api/authApi';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  // Start as null — user must log in to gain access
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while we verify the stored session
  const [authError, setAuthError] = useState(null);

  // On mount: restore user profile from localStorage and verify session with backend
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const saved = localStorage.getItem('sovereign_user');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (parsed && parsed._id && parsed.email) {
            setUser(parsed);
          }
        } catch {
          localStorage.removeItem('sovereign_user');
        }
      }

      // Re-verify session and fetch full profile from server
      try {
        const res = await authApi.getMe();
        if (isMounted && res && res.user) {
          setUser(res.user);
        }
      } catch (err) {
        // If server explicitly returns 401 unauthorized, clear session
        if (err.status === 401 && isMounted) {
          setUser(null);
          localStorage.removeItem('sovereign_user');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  // Persist non-sensitive profile to localStorage whenever it changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('sovereign_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('sovereign_user');
    }
  }, [user]);

  const login = async (email, password) => {
    setLoading(true);
    setAuthError(null);
    try {
      const res = await authApi.login({ email, password });
      if (res && res.user) {
        setUser(res.user);
        return res.user;
      }
      throw new Error('Invalid response from authentication server');
    } catch (err) {
      const msg = err.message || 'Authentication failed. Check your credentials.';
      setAuthError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setAuthError(null);
    try {
      const res = await authApi.register(userData);
      return res;
    } catch (err) {
      setAuthError(err.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // Even if backend call fails, clear local state
    } finally {
      setUser(null);
      localStorage.removeItem('sovereign_user');
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    return await authApi.changePassword({ currentPassword, newPassword });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        authError,
        login,
        register,
        logout,
        changePassword,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
