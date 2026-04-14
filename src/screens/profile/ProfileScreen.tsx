import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Modal, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { APP_CONFIG, COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';
import { changeLanguage } from '../../i18n';

export default function ProfileScreen() {
  const { t } = useTranslation();
  const nav = useNavigation<any>();
  const { user, logout, language, setLanguage } = useAuthStore();
  const [showLangPicker, setShowLangPicker] = useState(false);

  const currentLang = APP_CONFIG.LANGUAGES.find(l => l.code === language) || APP_CONFIG.LANGUAGES[0];

  const doLogout = () =>
    Alert.alert(t('auth.logout'), 'Are you sure?', [
      { text: t('common.cancel'), style: 'cancel' },
      { text: t('auth.logout'), style: 'destructive', onPress: logout },
    ]);

  const pickLanguage = async (code: string) => {
    await setLanguage(code);
    await changeLanguage(code);
    setShowLangPicker(false);
  };

  const stats = [
    { icon: 'hand-left-outline' as const, label: t('profile.total_dhikr'), value: user?.stats?.total_dhikr || 0 },
    { icon: 'flame-outline' as const, label: t('profile.current_streak'), value: `${user?.stats?.current_streak || 0} days` },
    { icon: 'book-outline' as const, label: t('profile.pages_read'), value: user?.stats?.quran_pages || 0 },
    { icon: 'headset-outline' as const, label: t('profile.listening_time'), value: `${Math.round(user?.stats?.listening_minutes || 0)} min` },
  ];

  const menu = [
    { icon: 'card-outline' as const, label: t('profile.subscription'), screen: 'Subscription', color: COLORS.secondary },
    { icon: 'people-outline' as const, label: t('profile.family_ties'), screen: 'FamilyTies', color: COLORS.islamicTeal },
    { icon: 'sparkles-outline' as const, label: t('ai.assistant'), screen: 'AIAssistant', color: COLORS.accent },
  ];

  return (
    <SafeAreaView style={s.c}>
      <ScrollView>
        {/* Avatar & Info */}
        <View style={s.ph}>
          <View style={s.avatar}>
            <Text style={s.at}>{(user?.name || 'U')[0].toUpperCase()}</Text>
          </View>
          <Text style={s.name}>{user?.name || 'User'}</Text>
          <Text style={s.email}>{user?.email || user?.phone || ''}</Text>
          {user?.is_premium && (
            <View style={s.badge}><Text style={s.badgeTxt}>Premium</Text></View>
          )}
        </View>

        {/* Stats Grid */}
        <View style={s.grid}>
          {stats.map((st, i) => (
            <View key={i} style={s.stat}>
              <Ionicons name={st.icon} size={20} color={COLORS.primary} />
              <Text style={s.sv}>{st.value}</Text>
              <Text style={s.sl}>{st.label}</Text>
            </View>
          ))}
        </View>

        {/* Language Selector */}
        <TouchableOpacity style={s.langRow} onPress={() => setShowLangPicker(true)} activeOpacity={0.7}>
          <View style={[s.mic, { backgroundColor: COLORS.primary + '15' }]}>
            <Ionicons name="language-outline" size={20} color={COLORS.primary} />
          </View>
          <Text style={s.ml}>{t('profile.language') || 'Language'}</Text>
          <Text style={s.langCurrent}>{currentLang.flag} {currentLang.nameNative}</Text>
          <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
        </TouchableOpacity>

        {/* Menu */}
        <View style={s.menu}>
          {menu.map((m, i) => (
            <TouchableOpacity key={i} style={s.mi} onPress={() => nav.navigate(m.screen)} activeOpacity={0.7}>
              <View style={[s.mic, { backgroundColor: (m.color || COLORS.primary) + '15' }]}>
                <Ionicons name={m.icon} size={20} color={m.color || COLORS.primary} />
              </View>
              <Text style={s.ml}>{m.label}</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
            </TouchableOpacity>
          ))}
        </View>

        {/* Admin */}
        {(user?.role === 'admin' || user?.role === 'special') && (
          <TouchableOpacity style={s.adminBtn} onPress={() => nav.navigate('AdminDashboard')}>
            <Ionicons name="shield-checkmark-outline" size={20} color={COLORS.primary} />
            <Text style={s.adminTxt}>{t('admin.dashboard')}</Text>
          </TouchableOpacity>
        )}

        {/* Logout */}
        <TouchableOpacity style={s.logoutBtn} onPress={doLogout}>
          <Ionicons name="log-out-outline" size={20} color={COLORS.error} />
          <Text style={s.logoutTxt}>{t('auth.logout')}</Text>
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Language Picker Modal */}
      <Modal visible={showLangPicker} animationType="slide" transparent presentationStyle="overFullScreen">
        <View style={s.overlay}>
          <View style={s.sheet}>
            <View style={s.sheetHeader}>
              <Text style={s.sheetTitle}>{t('auth.select_language') || 'Select Language'}</Text>
              <TouchableOpacity onPress={() => setShowLangPicker(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            <FlatList
              data={APP_CONFIG.LANGUAGES}
              keyExtractor={item => item.code}
              ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: COLORS.borderLight }} />}
              renderItem={({ item }) => {
                const isActive = item.code === language;
                return (
                  <TouchableOpacity style={s.langItem} onPress={() => pickLanguage(item.code)} activeOpacity={0.7}>
                    <Text style={s.langFlag}>{item.flag}</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={[s.langNative, isActive && s.langNativeActive]}>{item.nameNative}</Text>
                      <Text style={s.langEn}>{item.name}</Text>
                    </View>
                    {isActive && <Ionicons name="checkmark-circle" size={22} color={COLORS.primary} />}
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  ph: { alignItems: 'center', paddingVertical: 30 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  at: { fontSize: 32, fontWeight: '600', color: '#fff' },
  name: { fontSize: 20, fontWeight: '700', color: COLORS.text },
  email: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  badge: { backgroundColor: COLORS.secondaryLight, paddingHorizontal: 14, paddingVertical: 4, borderRadius: 999, marginTop: 8 },
  badgeTxt: { fontSize: 13, fontWeight: '600', color: COLORS.secondary },

  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 24, gap: 12 },
  stat: { width: '47%', backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16, alignItems: 'center' },
  sv: { fontSize: 17, fontWeight: '700', color: COLORS.text, marginTop: 6 },
  sl: { fontSize: 11, color: COLORS.textTertiary, marginTop: 2, textAlign: 'center' },

  // Language row (separate from menu, appears above it)
  langRow: {
    flexDirection: 'row', alignItems: 'center', marginTop: 24, marginHorizontal: 24,
    paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: COLORS.borderLight,
  },
  langCurrent: { fontSize: 13, color: COLORS.textSecondary, marginRight: 8 },

  menu: { paddingHorizontal: 24 },
  mi: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: COLORS.borderLight },
  mic: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  ml: { flex: 1, fontSize: 15, fontWeight: '500', color: COLORS.text },

  adminBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginHorizontal: 24, marginTop: 24, padding: 16, backgroundColor: COLORS.primaryLight, borderRadius: 14, gap: 8 },
  adminTxt: { fontSize: 15, fontWeight: '600', color: COLORS.primary },
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginHorizontal: 24, marginTop: 16, padding: 16, borderRadius: 14, borderWidth: 1, borderColor: COLORS.error + '30', gap: 8 },
  logoutTxt: { fontSize: 15, fontWeight: '500', color: COLORS.error },

  // Language picker modal
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, paddingBottom: 34, maxHeight: '60%' },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 0.5, borderBottomColor: COLORS.border },
  sheetTitle: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  langItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 14, gap: 14 },
  langFlag: { fontSize: 28 },
  langNative: { fontSize: 16, fontWeight: '500', color: COLORS.text },
  langNativeActive: { color: COLORS.primary, fontWeight: '700' },
  langEn: { fontSize: 12, color: COLORS.textSecondary, marginTop: 1 },
});
