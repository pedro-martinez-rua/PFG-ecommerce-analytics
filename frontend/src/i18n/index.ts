import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en/traduccion.json';
import es from './locales/es/traduccion.json';

const STORAGE_KEY = 'lang';

const getInitialLang = () => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'es' || stored === 'en') return stored;
  return 'es';
};

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: es },
  },
  lng: getInitialLang(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

i18n.on('languageChanged', (lng) => {
  localStorage.setItem(STORAGE_KEY, lng);
});

export default i18n;
