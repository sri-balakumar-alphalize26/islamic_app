import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../../config';
import { contentAPI } from '../../api/client';
import type { QuranBookmark } from './SurahDetailScreen';

const BOOKMARK_KEY = '@quran_bookmark';

export default function QuranScreen() {
  const { t } = useTranslation();
  const nav = useNavigation<any>();
  const [search, setSearch] = useState('');
  const [surahs, setSurahs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookmark, setBookmark] = useState<QuranBookmark | null>(null);

  useEffect(() => {
    contentAPI.getSurahs()
      .then(res => {
        const data = res.data?.data || res.data;
        if (Array.isArray(data)) setSurahs(data);
      })
      .catch(() => Alert.alert('Error', 'Failed to load surahs. Please check your connection or log in again.'))
      .finally(() => setLoading(false));
  }, []);

  // Reload bookmark every time the tab is focused (user may have updated it in SurahDetail)
  useFocusEffect(
    useCallback(() => {
      AsyncStorage.getItem(BOOKMARK_KEY)
        .then(stored => setBookmark(stored ? JSON.parse(stored) : null))
        .catch(() => {});
    }, [])
  );

  const openBookmark = () => {
    if (!bookmark) return;
    nav.navigate('SurahDetail', {
      surahNumber: bookmark.surahNumber,
      surahName: bookmark.surahName,
      scrollToAyah: bookmark.ayahNumber,
    });
  };

  const filtered = search
    ? surahs.filter(s => s.name?.toLowerCase().includes(search.toLowerCase()) || s.name_arabic?.includes(search))
    : surahs;

  if (loading) {
    return (
      <SafeAreaView style={s.c}>
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 60 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.c}>
      <View style={s.h}>
        <Text style={s.title}>{t('quran.surah_list')}</Text>
        <View style={s.sb}>
          <Ionicons name="search" size={18} color={COLORS.textTertiary} />
          <TextInput
            style={s.si}
            placeholder={t('quran.search')}
            placeholderTextColor={COLORS.textTertiary}
            value={search}
            onChangeText={setSearch}
          />
        </View>
      </View>
      <FlatList
        data={filtered}
        keyExtractor={i => String(i.number)}
        ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: COLORS.borderLight }} />}
        contentContainerStyle={{ paddingHorizontal: 24, paddingBottom: 80 }}
        ListHeaderComponent={
          bookmark ? (
            <TouchableOpacity style={s.bookmarkBanner} onPress={openBookmark} activeOpacity={0.8}>
              <Ionicons name="bookmark" size={20} color={COLORS.primary} />
              <View style={{ flex: 1 }}>
                <Text style={s.bbLabel}>Continue Reading</Text>
                <Text style={s.bbName}>{bookmark.surahName} · Ayah {bookmark.ayahNumber}</Text>
              </View>
              <Ionicons name="arrow-forward" size={18} color={COLORS.primary} />
            </TouchableOpacity>
          ) : null
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={s.item}
            onPress={() => nav.navigate('SurahDetail', { surahNumber: item.number, surahName: item.name })}
            activeOpacity={0.7}
          >
            <View style={s.num}><Text style={s.nt}>{item.number}</Text></View>
            <View style={{ flex: 1 }}>
              <Text style={s.sn}>{item.name}</Text>
              <Text style={s.meta}>{item.revelation_type} · {item.total_ayahs} {t('quran.ayahs')}</Text>
            </View>
            <Text style={s.ar}>{item.name_arabic}</Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  h: { padding: 24, paddingBottom: 12 },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.text, marginBottom: 12 },
  sb: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.backgroundSecondary, borderRadius: 10, paddingHorizontal: 14, height: 44 },
  si: { flex: 1, marginLeft: 8, fontSize: 15, color: COLORS.text },

  bookmarkBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.primaryLight, borderRadius: 12, padding: 14, marginBottom: 12, gap: 10 },
  bbLabel: { fontSize: 11, color: COLORS.primary, fontWeight: '500', marginBottom: 2 },
  bbName: { fontSize: 14, fontWeight: '600', color: COLORS.text },

  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14 },
  num: { width: 36, height: 36, borderRadius: 18, backgroundColor: COLORS.primaryLight, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  nt: { fontSize: 13, fontWeight: '600', color: COLORS.primary },
  sn: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  meta: { fontSize: 11, color: COLORS.textTertiary, marginTop: 2 },
  ar: { fontSize: 18, color: COLORS.text },
});
