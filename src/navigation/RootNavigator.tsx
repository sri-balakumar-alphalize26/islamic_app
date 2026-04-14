import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../contexts/AuthStore';
import { COLORS } from '../config';

import SplashScreen from '../screens/auth/SplashScreen';
import LanguageSelectScreen from '../screens/auth/LanguageSelectScreen';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';
import HomeScreen from '../screens/home/HomeScreen';
import QuranScreen from '../screens/quran/QuranScreen';
import SurahDetailScreen from '../screens/quran/SurahDetailScreen';
import AdhkarScreen from '../screens/adhkar/AdhkarScreen';
import AdhkarCategoryScreen from '../screens/adhkar/AdhkarCategoryScreen';
import AdhkarCounterScreen from '../screens/adhkar/AdhkarCounterScreen';
import AudioScreen from '../screens/audio/AudioScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';
import AIAssistantScreen from '../screens/ai/AIAssistantScreen';
import SubscriptionScreen from '../screens/subscription/SubscriptionScreen';
import FamilyTiesScreen from '../screens/family/FamilyTiesScreen';
import AdminDashboardScreen from '../screens/admin/AdminDashboardScreen';
import ContentManagementScreen from '../screens/admin/ContentManagementScreen';
import AudioUploadScreen from '../screens/admin/AudioUploadScreen';
import UserManagementScreen from '../screens/admin/UserManagementScreen';
import AILogsScreen from '../screens/admin/AILogsScreen';
import ServerSetupScreen from '../screens/auth/ServerSetupScreen';

const AuthStack = createNativeStackNavigator();
const MainStack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textTertiary,
        tabBarStyle: { backgroundColor: '#fff', borderTopWidth: 0.5, borderTopColor: COLORS.border, height: 62 + insets.bottom, paddingBottom: 8 + insets.bottom, paddingTop: 6 },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '500' as const },
        tabBarIcon: ({ color, size }: { color: string; size: number }) => {
          const icons: Record<string, any> = {
            Home: 'home-outline',
            Quran: 'book-outline',
            Adhkar: 'hand-left-outline',
            Audio: 'headset-outline',
            Profile: 'person-outline',
          };
          return <Ionicons name={icons[route.name] || 'ellipse'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ tabBarLabel: t('tabs.home') }} />
      <Tab.Screen name="Quran" component={QuranScreen} options={{ tabBarLabel: t('tabs.quran') }} />
      <Tab.Screen name="Adhkar" component={AdhkarScreen} options={{ tabBarLabel: t('tabs.adhkar') }} />
      <Tab.Screen name="Audio" component={AudioScreen} options={{ tabBarLabel: t('tabs.audio') }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ tabBarLabel: t('tabs.profile') }} />
    </Tab.Navigator>
  );
}

function AuthNavigator() {
  const { onboardingDone, isServerConfigured } = useAuthStore();
  const initialRoute = !isServerConfigured
    ? 'ServerSetup'
    : onboardingDone
      ? 'Login'
      : 'LanguageSelect';
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}
      initialRouteName={initialRoute}
    >
      <AuthStack.Screen name="ServerSetup" component={ServerSetupScreen} />
      <AuthStack.Screen name="LanguageSelect" component={LanguageSelectScreen} />
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
      <AuthStack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </AuthStack.Navigator>
  );
}

function AppNavigator() {
  return (
    <MainStack.Navigator screenOptions={{ headerShown: false }}>
      <MainStack.Screen name="MainTabs" component={MainTabs} />
      <MainStack.Screen name="SurahDetail" component={SurahDetailScreen} />
      <MainStack.Screen name="AdhkarCategory" component={AdhkarCategoryScreen} />
      <MainStack.Screen name="AdhkarCounter" component={AdhkarCounterScreen} />
      <MainStack.Screen name="AIAssistant" component={AIAssistantScreen} />
      <MainStack.Screen name="Subscription" component={SubscriptionScreen} />
      <MainStack.Screen name="FamilyTies" component={FamilyTiesScreen} />
      <MainStack.Screen name="AdminDashboard" component={AdminDashboardScreen} />
      <MainStack.Screen name="ContentManagement" component={ContentManagementScreen} />
      <MainStack.Screen name="AudioUpload" component={AudioUploadScreen} />
      <MainStack.Screen name="UserManagement" component={UserManagementScreen} />
      <MainStack.Screen name="AILogs" component={AILogsScreen} />
    </MainStack.Navigator>
  );
}

export default function Navigation() {
  const { isLoading, isLoggedIn } = useAuthStore();
  if (isLoading) return <SplashScreen />;
  return (
    <NavigationContainer>
      {isLoggedIn ? <AppNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
}
