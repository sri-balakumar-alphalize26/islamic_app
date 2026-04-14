import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { adhkarAPI } from '../../api/client';

export default function AdhkarCategoryScreen({ route, navigation }: any) {
  const { code, name } = route.params;
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTranslation, setShowTranslation] = useState(true);

  useEffect(() => {
    adhkarAPI.getByCategory(code)
      .then(res => {
        const adhkar = res.data?.data?.adhkar || [];
        setItems(adhkar);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [code]);

  const startSession = () => {
    if (items.length === 0) return;
    navigation.navigate('AdhkarCounter', { items });
  };

  const openSingle = (item: any) => {
    navigation.navigate('AdhkarCounter', {
      adhkarId: item.id,
      title: item.translation || item.title || item.name,
      arabicText: item.arabic_text,
      targetCount: item.repeat_count || 1,
    });
  };

  return (
    <SafeAreaView style={s.c}>
      {/* Header */}
      <View style={s.h}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.title}>{name}</Text>
        <TouchableOpacity onPress={() => setShowTranslation(v => !v)} style={s.toggleBtn}>
          <Ionicons
            name={showTranslation ? 'eye' : 'eye-off'}
            size={22}
            color={showTranslation ? COLORS.primary : COLORS.textTertiary}
          />
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 30 }} />
      ) : (
        <FlatList
          data={items}
          keyExtractor={i => String(i.id)}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 100 }}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          ListHeaderComponent={
            items.length > 0 ? (
              <TouchableOpacity style={s.sessionBtn} onPress={startSession} activeOpacity={0.85}>
                <Ionicons name="play-circle" size={22} color="#fff" />
                <Text style={s.sessionBtnTxt}>
                  Start Full Session ({items.length} adhkar)
                </Text>
              </TouchableOpacity>
            ) : null
          }
          ListEmptyComponent={
            <Text style={s.empty}>No adhkar in this category yet</Text>
          }
          renderItem={({ item }) => (
            <TouchableOpacity style={s.card} onPress={() => openSingle(item)} activeOpacity={0.7}>
              <Text style={s.arabic}>{item.arabic_text}</Text>
              {showTranslation && (item.translation || item.title)
                ? <Text style={s.trans}>{item.translation || item.title}</Text>
                : null}
              <View style={s.cardFooter}>
                <Text style={s.count}>
                  <Ionicons name="repeat" size={13} color={COLORS.primary} /> {item.repeat_count || 1}x
                </Text>
                {item.reference
                  ? <Text style={s.ref} numberOfLines={1}>{item.reference}</Text>
                  : null}
              </View>
            </TouchableOpacity>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  h: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 8, borderBottomWidth: 0.5, borderBottomColor: COLORS.border },
  title: { flex: 1, fontSize: 17, fontWeight: '600', color: COLORS.text, textAlign: 'center' },
  toggleBtn: { width: 36, height: 36, justifyContent: 'center', alignItems: 'center' },

  sessionBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: COLORS.primary, borderRadius: 14,
    padding: 16, marginVertical: 14,
  },
  sessionBtnTxt: { fontSize: 15, fontWeight: '600', color: '#fff', flex: 1 },

  card: { backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16 },
  arabic: { fontSize: 20, lineHeight: 36, textAlign: 'right', color: COLORS.text, marginBottom: 8 },
  trans: { fontSize: 14, color: COLORS.textSecondary, lineHeight: 22, marginBottom: 8 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 },
  count: { fontSize: 13, color: COLORS.primary, fontWeight: '600' },
  ref: { fontSize: 11, color: COLORS.textTertiary, flex: 1, textAlign: 'right', marginLeft: 8 },

  empty: { textAlign: 'center', color: COLORS.textTertiary, marginTop: 40, fontSize: 14 },
});
