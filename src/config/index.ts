export const APP_CONFIG = {
  APP_NAME: 'Islamic App',
  API_BASE_URL: '',  // Set dynamically from ServerSetupScreen
  ODOO_DATABASE: '', // Set dynamically from ServerSetupScreen
  DEFAULT_ODOO_PORT: '8069',
  API_TIMEOUT: 30000,
  STORAGE_KEYS: {
    ACCESS_TOKEN: '@app_token',
    REFRESH_TOKEN: '@app_refresh',
    USER_PROFILE: '@app_profile',
    LANGUAGE: '@app_language',
    ONBOARDING_DONE: '@app_onboarding',
    SERVER_URL: '@app_server_url',
    SERVER_DB: '@app_server_db',
  },
  LANGUAGES: [
    { code: 'en', name: 'English', nameNative: 'English', rtl: false, flag: '🇬🇧' },
    { code: 'ar', name: 'Arabic', nameNative: 'العربية', rtl: true, flag: '🇸🇦' },
    { code: 'fr', name: 'French', nameNative: 'Français', rtl: false, flag: '🇫🇷' },
    { code: 'tr', name: 'Turkish', nameNative: 'Türkçe', rtl: false, flag: '🇹🇷' },
    { code: 'hi', name: 'Hindi', nameNative: 'हिन्दी', rtl: false, flag: '🇮🇳' },
  ],
};

export const COLORS = {
  primary: '#0E7C61',
  primaryDark: '#085041',
  primaryLight: '#E1F5EE',
  secondary: '#D4A017',
  secondaryLight: '#FFF8E1',
  accent: '#6366F1',
  gold: '#C8A951',
  background: '#FFFFFF',
  backgroundSecondary: '#F5F6F8',
  text: '#1A1A2E',
  textSecondary: '#6C757D',
  textTertiary: '#ADB5BD',
  textOnPrimary: '#FFFFFF',
  border: '#E9ECEF',
  borderLight: '#F1F3F5',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  islamicGreen: '#0E7C61',
  islamicGold: '#C8A951',
  islamicTeal: '#0D9488',
};

export const SIZES = {
  xs: 11,
  sm: 13,
  md: 15,
  lg: 17,
  xl: 20,
  xxl: 26,
};
