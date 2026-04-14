import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { APP_CONFIG } from '../config';

const K = APP_CONFIG.STORAGE_KEYS;

const api = axios.create({
  baseURL: '',
  timeout: APP_CONFIG.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Load saved server URL and database from storage and apply to axios instance */
export async function initServerConfig(): Promise<{ url: string; db: string }> {
  const [url, db] = await Promise.all([
    AsyncStorage.getItem(K.SERVER_URL),
    AsyncStorage.getItem(K.SERVER_DB),
  ]);
  if (url) {
    api.defaults.baseURL = url;
  }
  if (db) {
    api.defaults.headers.common['X-Odoo-Database'] = db;
  }
  return { url: url || '', db: db || '' };
}

/** Update server URL and database at runtime (called from ServerSetupScreen) */
export async function setServerConfig(serverUrl: string, database: string) {
  // Normalize: ensure URL ends with /api/v1
  let baseUrl = serverUrl.replace(/\/+$/, '');
  if (!baseUrl.endsWith('/api/v1')) {
    baseUrl += '/api/v1';
  }
  await AsyncStorage.setItem(K.SERVER_URL, baseUrl);
  await AsyncStorage.setItem(K.SERVER_DB, database);
  api.defaults.baseURL = baseUrl;
  api.defaults.headers.common['X-Odoo-Database'] = database;
}

/** Check if the islamic_app module is installed on a given database.
 *  Returns true if the module route responds (any status other than 404). */
export async function checkIslamicModule(serverUrl: string, database: string): Promise<boolean> {
  const url = serverUrl.replace(/\/+$/, '');
  try {
    const res = await axios.get(`${url}/api/v1/content/surahs`, {
      timeout: 5000,
      headers: { 'X-Odoo-Database': database },
      validateStatus: () => true,
    });
    return res.status !== 404;
  } catch {
    return false;
  }
}

/** Fetch databases from Odoo server */
export async function fetchOdooDatabases(serverUrl: string): Promise<string[]> {
  const url = serverUrl.replace(/\/+$/, '');
  let allDbs: string[] = [];
  try {
    const res = await axios.post(
      `${url}/jsonrpc`,
      {
        jsonrpc: '2.0',
        method: 'call',
        id: Date.now(),
        params: { service: 'db', method: 'list', args: [] },
      },
      { timeout: 15000, headers: { 'Content-Type': 'application/json' } },
    );
    if (res.data?.error) {
      const err = res.data.error;
      throw new Error(err.data?.message || err.message || 'Odoo RPC Error');
    }
    allDbs = Array.isArray(res.data?.result) ? res.data.result : [];
  } catch (e: any) {
    if (e.response) throw new Error(`Odoo HTTP ${e.response.status}`);
    if (e.request) throw new Error('Cannot connect to Odoo server. Check IP and port.');
    throw e;
  }

  if (allDbs.length === 0) return [];

  const checks = await Promise.all(allDbs.map((db) => checkIslamicModule(url, db)));
  return allDbs.filter((_, i) => checks[i]);
}

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem(K.ACCESS_TOKEN);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const lang = await AsyncStorage.getItem(K.LANGUAGE);
  if (lang) config.headers['Accept-Language'] = lang;
  return config;
});

let isRefreshing = false;
let refreshQueue: { resolve: (token: string) => void; reject: (err: any) => void }[] = [];

api.interceptors.response.use(
  (res) => {
    if (typeof res.data === 'string') {
      try { res.data = JSON.parse(res.data); } catch (e) {}
    }
    return res;
  },
  async (error) => {
    const originalRequest = error.config;

    // Auto-refresh on 401, but not for auth endpoints themselves
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/')
    ) {
      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = await AsyncStorage.getItem(K.REFRESH_TOKEN);
        if (!refreshToken) throw new Error('No refresh token');

        const refreshRes = await api.post('/auth/refresh', { refresh_token: refreshToken });
        const newToken = refreshRes.data?.data?.access_token;
        const newRefresh = refreshRes.data?.data?.refresh_token;

        if (!newToken) throw new Error('Refresh failed');

        await AsyncStorage.setItem(K.ACCESS_TOKEN, newToken);
        if (newRefresh) await AsyncStorage.setItem(K.REFRESH_TOKEN, newRefresh);

        refreshQueue.forEach(({ resolve }) => resolve(newToken));
        refreshQueue = [];

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        refreshQueue.forEach(({ reject }) => reject(refreshError));
        refreshQueue = [];
        // Clear all stored auth data so user is sent to login on next app open
        await AsyncStorage.multiRemove([K.ACCESS_TOKEN, K.REFRESH_TOKEN, K.USER_PROFILE]);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (d: any) => api.post('/auth/register', d),
  login: (d: any) => api.post('/auth/login', d),
  logout: () => api.post('/auth/logout'),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (email: string, otp: string, new_password: string) =>
    api.post('/auth/reset-password', { email, otp, new_password }),
};

export const userAPI = {
  getProfile: () => api.get('/user/profile'),
  updateProfile: (d: any) => api.put('/user/profile', d),
  getStats: () => api.get('/user/stats'),
  changeLanguage: (lang: string) => api.put('/user/language', { language: lang }),
  logListening: (minutes: number) => api.post('/user/listening', { minutes }),
  logPageRead: (surahNumber: number, ayahCount: number) => api.post('/user/pages', { surah_number: surahNumber, ayah_count: ayahCount }),
};

export const contentAPI = {
  getSurahs: () => api.get('/content/surahs'),
  getSurah: (num: number, tafsir = false) => api.get(`/content/surahs/${num}`, { params: { tafsir: tafsir ? '1' : '0' } }),
  search: (q: string) => api.get('/content/search', { params: { q } }),
  getDailyWisdom: () => api.get('/content/daily-wisdom'),
  getFeatured: () => api.get('/content/featured'),
  getBookmarks: () => api.get('/content/bookmarks'),
  addBookmark: (d: any) => api.post('/content/bookmarks', d),
  deleteBookmark: (id: number) => api.delete(`/content/bookmarks/${id}`),
};

export const adhkarAPI = {
  getCategories: () => api.get('/adhkar/categories'),
  getByCategory: (code: string) => api.get(`/adhkar/category/${code}`),
  getById: (id: number) => api.get(`/adhkar/${id}`),
  getByTime: (time: string) => api.get(`/adhkar/time/${time}`),
  getFeatured: () => api.get('/adhkar/featured'),
};

export const audioAPI = {
  list: (p?: any) => api.get('/audio/list', { params: p }),
  getById: (id: number) => api.get(`/audio/${id}`),
  getStreamUrl: (id: number) => api.get(`/audio/stream/${id}`),
  getPlaylists: () => api.get('/audio/playlists'),
  upload: (d: any) => api.post('/audio/upload', d),
  create: (d: any) => api.post('/audio/upload', d),
};

export const dhikrAPI = {
  log: (d: any) => api.post('/dhikr/log', d),
  increment: (logId: number, amount = 1) => api.post('/dhikr/increment', { log_id: logId, amount }),
  getStats: () => api.get('/dhikr/stats'),
  getHistory: (page = 1) => api.get('/dhikr/history', { params: { page } }),
  getCustom: () => api.get('/dhikr/custom'),
  createCustom: (d: any) => api.post('/dhikr/custom', d),
  deleteCustom: (id: number) => api.delete(`/dhikr/custom/${id}`),
};

export const aiAPI = {
  ask: (question: string, conversationId?: number) => api.post('/ai/ask', { question, conversation_id: conversationId }),
  getConversations: (page = 1) => api.get('/ai/conversations', { params: { page } }),
  getConversation: (id: number) => api.get(`/ai/conversations/${id}`),
};

export const subscriptionAPI = {
  getPlans: () => api.get('/subscription/plans'),
  getCurrent: () => api.get('/subscription/current'),
  purchase: (d: any) => api.post('/subscription/purchase', d),
  cancel: () => api.post('/subscription/cancel'),
};

export const familyAPI = {
  getMembers: () => api.get('/family/members'),
  addMember: (d: any) => api.post('/family/members', d),
  updateMember: (id: number, d: any) => api.put(`/family/members/${id}`, d),
  deleteMember: (id: number) => api.delete(`/family/members/${id}`),
  logContact: (id: number, d: any) => api.post(`/family/members/${id}/contact`, d),
  getOverdue: () => api.get('/family/overdue'),
};

export const adminAPI = {
  createContent: (d: any) => api.post('/admin/content', d),
  publishContent: (id: number) => api.post(`/admin/content/${id}/publish`),
  listContent: (p?: any) => api.get('/content/search', { params: { q: '', ...p } }),
  listUsers: (page = 1, search = '') => api.get('/admin/users', { params: { page, search } }),
  updateUserRole: (userId: number, role: string) => api.put(`/admin/users/${userId}/role`, { role }),
  publishAudio: (id: number) => api.post(`/admin/audio/${id}/publish`),
  analyticsOverview: () => api.get('/admin/analytics/overview'),
  analyticsContent: () => api.get('/admin/analytics/content'),
};

export default api;
