import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '@react-navigation/native';
import { COLORS } from '../../config';
import { adhkarAPI } from '../../api/client';

export default function AdhkarScreen() {
  const { t } = useTranslation();
  const nav = useNavigation<any>();
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adhkarAPI.getCategories()
      .then(res => {
        const data = res.data?.data || [];
        if (Array.isArray(data)) setCategories(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <SafeAreaView style={s.c}>
        <Text style={s.title}>{t('adhkar.categories')}</Text>
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.c}>
      <Text style={s.title}>{t('adhkar.categories')}</Text>
      <FlatList
        data={categories}
        keyExtractor={i => i.code}
        contentContainerStyle={{ paddingHorizontal: 24, paddingBottom: 80 }}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[s.card, { borderLeftColor: item.color || COLORS.primary }]}
            onPress={() => nav.navigate('AdhkarCategory', { code: item.code, name: item.name })}
            activeOpacity={0.7}
          >
            <View style={{ flex: 1 }}>
              <Text style={s.cardTitle}>{item.name}</Text>
              <Text style={s.cardSub}>
                {item.adhkar_count} {t('adhkar.items', { defaultValue: 'items' })}
              </Text>
            </View>
            <Text style={s.arrow}>›</Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.text, padding: 24, paddingBottom: 12 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16, borderLeftWidth: 4 },
  cardTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  cardSub: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  arrow: { fontSize: 24, color: COLORS.textTertiary },
});
