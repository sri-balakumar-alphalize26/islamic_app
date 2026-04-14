import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Navigation from './src/navigation/RootNavigator';
import { useAuthStore } from './src/contexts/AuthStore';
import './src/i18n';

export default function App() {
  const initialize = useAuthStore((s) => s.initialize);

  useEffect(() => {
    initialize();
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <Navigation />
    </SafeAreaProvider>
  );
}
