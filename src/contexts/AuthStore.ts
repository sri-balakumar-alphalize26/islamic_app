import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { APP_CONFIG } from '../config';
import { authAPI, userAPI, initServerConfig } from '../api/client';

const K = APP_CONFIG.STORAGE_KEYS;

export interface UserProfile {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  language: string;
  role: 'user' | 'special' | 'admin';
  is_premium: boolean;
  stats: {
    total_dhikr: number;
    current_streak: number;
    longest_streak: number;
    quran_pages: number;
    listening_minutes: number;
  };
}

interface AuthState {
  isLoading: boolean;
  isLoggedIn: boolean;
  isServerConfigured: boolean;
  user: UserProfile | null;
  language: string;
  onboardingDone: boolean;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  setLanguage: (lang: string) => Promise<void>;
  finishOnboarding: () => Promise<void>;
  markServerConfigured: () => void;
  refreshStats: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isLoading: true,
  isLoggedIn: false,
  isServerConfigured: false,
  user: null,
  language: 'en',
  onboardingDone: false,

  initialize: async () => {
    try {
      // Load server config first
      const serverConfig = await initServerConfig();
      const serverConfigured = !!(serverConfig.url && serverConfig.db);
      set({ isServerConfigured: serverConfigured });

      const results = await AsyncStorage.multiGet([K.ACCESS_TOKEN, K.LANGUAGE, K.ONBOARDING_DONE, K.USER_PROFILE]);
      const token = results[0][1];
      const lang = results[1][1];
      const onb = results[2][1];
      const cached = results[3][1];

      set({ language: lang || 'en', onboardingDone: onb === 'true' });

      if (token) {
        if (cached) {
          try {
            set({ user: JSON.parse(cached), isLoggedIn: true });
          } catch (e) {}
        }
        try {
          const res = await userAPI.getProfile();
          const profile = res.data?.data;
          if (profile) {
            await AsyncStorage.setItem(K.USER_PROFILE, JSON.stringify(profile));
            set({ user: profile, isLoggedIn: true });
          }
        } catch (e) {}
      }
    } catch (e) {
      console.log('Init error:', e);
    }
    set({ isLoading: false });
  },

  login: async (email: string, password: string) => {
    const res = await authAPI.login({ email, password });
    const { access_token, refresh_token } = res.data.data;
    await AsyncStorage.setItem(K.ACCESS_TOKEN, access_token);
    await AsyncStorage.setItem(K.REFRESH_TOKEN, refresh_token);
    const profileRes = await userAPI.getProfile();
    const profile = profileRes.data?.data;
    await AsyncStorage.setItem(K.USER_PROFILE, JSON.stringify(profile));
    set({ isLoggedIn: true, user: profile });
  },

  register: async (data: any) => {
    // Just create account — don't store tokens or auto-login.
    // User will be directed to Login screen to sign in manually.
    await authAPI.register(data);
  },

  logout: async () => {
    try { await authAPI.logout(); } catch (e) {}
    await AsyncStorage.multiRemove([K.ACCESS_TOKEN, K.REFRESH_TOKEN, K.USER_PROFILE]);
    set({ isLoggedIn: false, user: null });
  },

  setLanguage: async (lang: string) => {
    await AsyncStorage.setItem(K.LANGUAGE, lang);
    set({ language: lang });
    // Update backend so get_lang() returns the correct language
    try { await userAPI.changeLanguage(lang); } catch {}
  },

  finishOnboarding: async () => {
    await AsyncStorage.setItem(K.ONBOARDING_DONE, 'true');
    set({ onboardingDone: true });
  },

  markServerConfigured: () => {
    set({ isServerConfigured: true });
  },

  refreshStats: async () => {
    try {
      const res = await userAPI.getStats();
      const stats = res.data?.data;
      if (stats) {
        set(state => ({
          user: state.user ? { ...state.user, stats } : null,
        }));
        const cached = await AsyncStorage.getItem(K.USER_PROFILE);
        if (cached) {
          const profile = JSON.parse(cached);
          profile.stats = stats;
          await AsyncStorage.setItem(K.USER_PROFILE, JSON.stringify(profile));
        }
      }
    } catch (e) {}
  },
}));
