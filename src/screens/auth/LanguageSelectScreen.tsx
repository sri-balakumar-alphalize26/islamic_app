import React from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { APP_CONFIG, COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';
import { changeLanguage } from '../../i18n';

export default function LanguageSelectScreen({ navigation }: any) {
  const { setLanguage, finishOnboarding } = useAuthStore();
  const select = async (code: string) => {
    await setLanguage(code);
    await changeLanguage(code);
    await finishOnboarding();
    navigation.replace('Login');
  };
  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <View style={s.logo}><Text style={s.logoIcon}>☪</Text></View>
        <Text style={s.bis}>بسم الله الرحمن الرحيم</Text>
        <Text style={s.title}>Select Your Language</Text>
        <Text style={s.subtitle}>اختر لغتك</Text>
      </View>
      <FlatList data={APP_CONFIG.LANGUAGES} keyExtractor={(i) => i.code} contentContainerStyle={{ paddingHorizontal: 24, paddingBottom: 40 }} ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.langItem} onPress={() => select(item.code)} activeOpacity={0.7}>
            <Text style={s.flag}>{item.flag}</Text>
            <View style={{ flex: 1 }}><Text style={s.native}>{item.nameNative}</Text><Text style={s.english}>{item.name}</Text></View>
            <Text style={s.arrow}>→</Text>
          </TouchableOpacity>
        )} />
    </SafeAreaView>
  );
}
const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { alignItems: 'center', paddingVertical: 40, paddingHorizontal: 24 },
  logo: { width: 80, height: 80, borderRadius: 40, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
  logoIcon: { fontSize: 40, color: '#fff' },
  bis: { fontSize: 22, color: COLORS.islamicGold, marginBottom: 16 },
  title: { fontSize: 22, fontWeight: '600', color: COLORS.text, marginBottom: 4 },
  subtitle: { fontSize: 18, color: COLORS.textSecondary },
  langItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 18, paddingHorizontal: 16, backgroundColor: COLORS.backgroundSecondary, borderRadius: 14 },
  flag: { fontSize: 32, marginRight: 16 },
  native: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  english: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  arrow: { fontSize: 20, color: COLORS.primary, fontWeight: '600' },
});
