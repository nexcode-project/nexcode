import { create } from 'zustand';
import { User, authAPI, LoginRequest, RegisterRequest } from '@/lib/api';
import Cookies from 'js-cookie';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  checkAuth: () => Promise<void>;
  loginWithPassword: (credentials: LoginRequest) => Promise<boolean>;
  register: (userData: RegisterRequest) => Promise<boolean>;
  loginWithCAS: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  
  setUser: (user) => set({ 
    user, 
    isAuthenticated: !!user 
  }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  checkAuth: async () => {
    try {
      set({ isLoading: true });
      // Check if we have a stored session token first
      // Only access localStorage on client side to prevent SSR issues
      const sessionToken = typeof window !== 'undefined' 
        ? localStorage.getItem('session_token') 
        : null;
      
      if (!sessionToken) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      
      const response = await authAPI.getCurrentUser();
      set({ 
        user: response.data, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error) {
      console.error('Auth check failed:', error);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('session_token');
      }
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      });
    }
  },
  
  loginWithPassword: async (credentials: LoginRequest) => {
    try {
      set({ isLoading: true });
      const response = await authAPI.login(credentials);
      
      // Store session token in localStorage (since HTTPOnly cookies can't be read by JS)
      if (response.data.session_token && typeof window !== 'undefined') {
        localStorage.setItem('session_token', response.data.session_token);
      }
      
      // Set user info from response
      if (response.data.user) {
        set({ 
          user: response.data.user, 
          isAuthenticated: true, 
          isLoading: false 
        });
      } else {
        // Fallback: get user info via API call
        const userResponse = await authAPI.getCurrentUser();
        set({ 
          user: userResponse.data, 
          isAuthenticated: true, 
          isLoading: false 
        });
      }
      
      toast.success('登录成功');
      return true;
    } catch (error: any) {
      console.error('Password login failed:', error);
      const message = error.response?.data?.detail || '用户名或密码错误';
      toast.error(message);
      set({ isLoading: false });
      return false;
    }
  },

  register: async (userData: RegisterRequest) => {
    try {
      set({ isLoading: true });
      await authAPI.register(userData);
      toast.success('注册成功，请登录');
      set({ isLoading: false });
      return true;
    } catch (error: any) {
      console.error('Registration failed:', error);
      const message = error.response?.data?.detail || '注册失败，请重试';
      toast.error(message);
      set({ isLoading: false });
      return false;
    }
  },

  loginWithCAS: async () => {
    try {
      const response = await authAPI.getCASLoginUrl();
      window.location.href = response.data.login_url;
    } catch (error) {
      console.error('CAS login failed:', error);
      toast.error('CAS登录失败，请重试');
    }
  },
  
  logout: async () => {
    try {
      await authAPI.logout();
      if (typeof window !== 'undefined') {
        localStorage.removeItem('session_token');
      }
      set({ 
        user: null, 
        isAuthenticated: false 
      });
      toast.success('已退出登录');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Logout failed:', error);
      // Force logout even if API call fails
      if (typeof window !== 'undefined') {
        localStorage.removeItem('session_token');
        window.location.href = '/login';
      }
      set({ 
        user: null, 
        isAuthenticated: false 
      });
    }
  },
})); 