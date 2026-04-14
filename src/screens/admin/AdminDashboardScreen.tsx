import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { adminAPI } from '../../api/client';

export default function AdminDashboardScreen({ navigation }: any) {
  const { t } = useTranslation();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.analyticsOverview()
      .then(res => {
        const data = res.data?.data || res.data;
        if (data) setStats(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const cards = stats ? [
    { label: t('admin.total_users'), value: String(stats.users?.total || 0), icon: 'people' as const, color: COLORS.primary },
    { label: t('admin.active_users'), value: String(stats.users?.active_7d || 0), icon: 'pulse' as const, color: COLORS.success },
    { label: t('admin.premium_users'), value: String(stats.users?.premium || 0), icon: 'star' as const, color: COLORS.secondary },
    { label: t('admin.revenue'), value: `$${stats.revenue?.total || 0}`, icon: 'cash' as const, color: COLORS.islamicTeal },
  ] : [
    { label: t('admin.total_users'), value: '...', icon: 'people' as const, color: COLORS.primary },
    { label: t('admin.active_users'), value: '...', icon: 'pulse' as const, color: COLORS.success },
    { label: t('admin.premium_users'), value: '...', icon: 'star' as const, color: COLORS.secondary },
    { label: t('admin.revenue'), value: '...', icon: 'cash' as const, color: COLORS.islamicTeal },
  ];

  const actions = [
    { icon: 'create-outline' as const, label: 'Content Mgmt', color: COLORS.primary, onPress: () => navigation.navigate('ContentManagement') },
    { icon: 'cloud-upload-outline' as const, label: 'Upload Audio', color: COLORS.accent, onPress: () => navigation.navigate('AudioUpload') },
    { icon: 'people-outline' as const, label: 'User Mgmt', color: COLORS.islamicTeal, onPress: () => navigation.navigate('UserManagement') },
    { icon: 'analytics-outline' as const, label: 'AI Logs', color: COLORS.secondary, onPress: () => navigation.navigate('AILogs') },
  ];

  return (
    <SafeAreaView style={s.c}>
      <View style={s.h}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.title}>{t('admin.dashboard')}</Text>
        <View style={{ width: 24 }} />
      </View>
      <ScrollView>
        <Text style={s.sec}>{t('admin.analytics')}</Text>
        {loading ? (
          <ActivityIndicator size="small" color={COLORS.primary} style={{ marginTop: 10 }} />
        ) : null}
        <View style={s.grid}>
          {cards.map((st, i) => (
            <View key={i} style={s.card}>
              <Ionicons name={st.icon} size={22} color={st.color} />
              <Text style={s.cv}>{st.value}</Text>
              <Text style={s.cl}>{st.label}</Text>
            </View>
          ))}
        </View>

        {stats?.engagement && (
          <>
            <Text style={s.sec}>Today's Engagement</Text>
            <View style={s.grid}>
              <View style={s.card}>
                <Ionicons name="hand-left-outline" size={22} color={COLORS.primary} />
                <Text style={s.cv}>{stats.engagement.dhikr_today}</Text>
                <Text style={s.cl}>Dhikr Today</Text>
              </View>
              <View style={s.card}>
                <Ionicons name="sparkles-outline" size={22} color={COLORS.accent} />
                <Text style={s.cv}>{stats.engagement.ai_queries_today}</Text>
                <Text style={s.cl}>AI Queries</Text>
              </View>
            </View>
          </>
        )}

        <Text style={s.sec}>Quick Actions</Text>
        <View style={s.grid}>
          {actions.map((a, i) => (
            <TouchableOpacity key={i} style={s.action} onPress={a.onPress}>
              <View style={[s.aic, { backgroundColor: a.color + '15' }]}>
                <Ionicons name={a.icon} size={22} color={a.color} />
              </View>
              <Text style={s.al}>{a.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={s.note}>Manage content, audio, users, and AI logs directly in-app</Text>
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  h: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  title: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  sec: { fontSize: 15, fontWeight: '600', color: COLORS.text, paddingHorizontal: 24, marginTop: 20, marginBottom: 12 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 24, gap: 12 },
  card: { width: '47%', backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16 },
  cv: { fontSize: 22, fontWeight: '700', color: COLORS.text, marginTop: 8 },
  cl: { fontSize: 11, color: COLORS.textTertiary, marginTop: 2 },
  action: { width: '47%', backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16, alignItems: 'center' },
  aic: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  al: { fontSize: 13, fontWeight: '500', color: COLORS.text, textAlign: 'center' },
  note: { fontSize: 13, color: COLORS.textTertiary, textAlign: 'center', marginTop: 24, paddingHorizontal: 40 },
});
