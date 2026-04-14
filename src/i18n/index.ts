import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import ar from './locales/ar.json';
import fr from './locales/fr.json';
import tr from './locales/tr.json';
import hi from './locales/hi.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ar: { translation: ar },
    fr: { translation: fr },
    tr: { translation: tr },
    hi: { translation: hi },
  },
  lng: 'en',
  fallbackLng: 'en',
  compatibilityJSON: 'v3',
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

export const changeLanguage = (lang: string) => i18n.changeLanguage(lang);
export default i18n;
