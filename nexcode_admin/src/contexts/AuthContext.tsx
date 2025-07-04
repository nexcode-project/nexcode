import React, { createContext, useContext, useState, useEffect } from 'react';
import { message } from 'antd';
import { authAPI, type User, type LoginResponse } from '../services/api';

interface AuthContextType {
  user: User | null;
  darkMode: boolean;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  loginWithCAS: () => Promise<void>;
  logout: () => void;
  toggleDarkMode: () => void;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [loading, setLoading] = useState(true);

  // 检查认证状态
  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      const authStatus = await authAPI.getAuthStatus();
      if (authStatus.authenticated && authStatus.user) {
        setUser(authStatus.user);
      } else {
        // 清除无效token
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    } catch (error) {
      console.error('认证状态检查失败:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  };

  // 密码登录
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response: LoginResponse = await authAPI.login(username, password);
      
      // 存储认证信息
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      setUser(response.user);
      
      message.success('登录成功！');
      return true;
    } catch (error: any) {
      console.error('登录失败:', error);
      const errorMessage = error.response?.data?.detail || '登录失败，请检查用户名和密码';
      message.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // CAS登录
  const loginWithCAS = async (): Promise<void> => {
    try {
      const casResponse = await authAPI.getCASLoginURL();
      
      // 保存当前URL以便登录后返回
      localStorage.setItem('returnUrl', window.location.href);
      
      // 重定向到CAS登录页面
      window.location.href = casResponse.login_url;
    } catch (error: any) {
      console.error('CAS登录失败:', error);
      message.error('CAS登录服务暂时不可用');
    }
  };

  // 处理CAS回调
  const handleCASCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const ticket = urlParams.get('ticket');
    const service = urlParams.get('service') || window.location.origin + '/admin';

    if (ticket) {
      try {
        setLoading(true);
        const response: LoginResponse = await authAPI.verifyCASTicket(ticket, service);
        
        // 存储认证信息
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
        
        message.success('CAS登录成功！');
        
        // 清理URL并返回原页面
        const returnUrl = localStorage.getItem('returnUrl') || '/admin/dashboard';
        localStorage.removeItem('returnUrl');
        window.history.replaceState({}, document.title, returnUrl);
        
      } catch (error: any) {
        console.error('CAS认证失败:', error);
        message.error('CAS认证失败，请重试');
        // 清理URL
        window.history.replaceState({}, document.title, '/login');
      } finally {
        setLoading(false);
      }
    }
  };

  // 登出
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      // 即使API调用失败也要清理本地状态
      console.error('登出API调用失败:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('returnUrl');
      setUser(null);
      message.success('已安全退出');
    }
  };

  // 切换主题
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', JSON.stringify(newDarkMode));
  };

  // 初始化
  useEffect(() => {
    // 检查是否是CAS回调
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('ticket')) {
      handleCASCallback();
    } else {
      checkAuthStatus();
    }
  }, []);

  // 自动检查认证状态（每5分钟）
  useEffect(() => {
    if (user) {
      const interval = setInterval(checkAuthStatus, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const value: AuthContextType = {
    user,
    darkMode,
    loading,
    isAuthenticated: !!user,
    login,
    loginWithCAS,
    logout,
    toggleDarkMode,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 