import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList,
  ActivityIndicator, Dimensions, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { contentAPI, userAPI } from '../../api/client';
import { useAuthStore } from '../../contexts/AuthStore';

const BOOKMARK_KEY = '@quran_bookmark';
const { width: SW } = Dimensions.get('window');
const AYAHS_PER_PAGE = 8;

// Arabic numeral conversion
const AR = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
const toAr = (n: number) => String(n).split('').map(d => AR[+d]).join('');

export interface QuranBookmark {
  surahNumber: number;
  surahName: string;
  ayahNumber: number;
}

export default function SurahDetailScreen({ route, navigation }: any) {
  const { surahNumber, surahName, surahNameArabic, scrollToAyah } = route.params;
  const { refreshStats } = useAuthStore();
  const pagerRef = useRef<FlatList>(null);
  const hasLoggedRef = useRef(false);

  const [ayahs, setAyahs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasBismillah, setHasBismillah] = useState(true);
  const [showTranslation, setShowTranslation] = useState(false); // off by default for Mushaf look
  const [bookmarkedAyah, setBookmarkedAyah] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(0);

  // ── Load data ────────────────────────────────────────────────────────────
  useEffect(() => {
    contentAPI.getSurah(surahNumber)
      .then(res => {
        const data = res.data?.data || res.data;
        if (data?.ayahs) setAyahs(data.ayahs);
        if (data?.has_bismillah !== undefined) setHasBismillah(data.has_bismillah);
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    AsyncStorage.getItem(BOOKMARK_KEY)
      .then(stored => {
        if (stored) {
          const bm: QuranBookmark = JSON.parse(stored);
          if (bm.surahNumber === surahNumber) setBookmarkedAyah(bm.ayahNumber);
        }
      })
      .catch(() => {});
  }, [surahNumber]);

  // ── Pages ────────────────────────────────────────────────────────────────
  const pages = useMemo(() => {
    if (ayahs.length === 0) return [];
    const result: any[][] = [];
    for (let i = 0; i < ayahs.length; i += AYAHS_PER_PAGE) {
      result.push(ayahs.slice(i, i + AYAHS_PER_PAGE));
    }
    return result;
  }, [ayahs]);

  // Jump to bookmarked page
  useEffect(() => {
    if (pages.length === 0) return;
    const targetAyah = scrollToAyah ?? bookmarkedAyah;
    if (!targetAyah) return;
    const idx = ayahs.findIndex(a => a.ayah_number === targetAyah);
    if (idx < 0) return;
    const pageIdx = Math.floor(idx / AYAHS_PER_PAGE);
    setTimeout(() => {
      pagerRef.current?.scrollToIndex({ index: pageIdx, animated: false });
      setCurrentPage(pageIdx);
    }, 300);
  }, [pages]);

  // ── Bookmark ─────────────────────────────────────────────────────────────
  const toggleBookmark = useCallback(async () => {
    try {
      // Bookmark the first ayah on the current page
      const pageAyahs = pages[currentPage];
      if (!pageAyahs || pageAyahs.length === 0) return;
      const firstAyah = pageAyahs[0].ayah_number;

      if (bookmarkedAyah === firstAyah) {
        await AsyncStorage.removeItem(BOOKMARK_KEY);
        setBookmarkedAyah(null);
      } else {
        const bm: QuranBookmark = { surahNumber, surahName, ayahNumber: firstAyah };
        await AsyncStorage.setItem(BOOKMARK_KEY, JSON.stringify(bm));
        setBookmarkedAyah(firstAyah);
      }
    } catch {}
  }, [bookmarkedAyah, currentPage, pages, surahNumber, surahName]);

  // Is current page bookmarked?
  const isPageBookmarked = useMemo(() => {
    if (!bookmarkedAyah || pages.length === 0) return false;
    const pageAyahs = pages[currentPage];
    return pageAyahs?.some((a: any) => a.ayah_number === bookmarkedAyah) ?? false;
  }, [bookmarkedAyah, currentPage, pages]);

  // ── Log pages read ───────────────────────────────────────────────────────
  useEffect(() => {
    if (pages.length === 0 || hasLoggedRef.current) return;
    if (currentPage >= pages.length - 1) {
      hasLoggedRef.current = true;
      userAPI.logPageRead(surahNumber, ayahs.length).then(() => refreshStats()).catch(() => {});
    }
  }, [currentPage, pages]);

  // ── Page navigation ──────────────────────────────────────────────────────
  const onPageChange = useCallback((e: any) => {
    const x = e.nativeEvent.contentOffset.x;
    setCurrentPage(Math.round(x / SW));
  }, []);

  const goPage = useCallback((dir: number) => {
    const next = currentPage + dir;
    if (next < 0 || next >= pages.length) return;
    pagerRef.current?.scrollToIndex({ index: next, animated: true });
    setCurrentPage(next);
  }, [currentPage, pages.length]);

  // ── Render one Mushaf page ──────────────────────────────────────────────
  const renderPage = useCallback(({ item: pageAyahs, index }: { item: any[]; index: number }) => {
    const isFirst = index === 0;
    return (
      <View style={s.pageOuter}>
        <View style={s.page}>
          {/* ── Ornamental Surah Header ── */}
          <View style={s.ornamentFrame}>
            <View style={s.ornamentCornerTL} />
            <View style={s.ornamentCornerTR} />
            <View style={s.ornamentCornerBL} />
            <View style={s.ornamentCornerBR} />
            <Text style={s.surahHeaderAr}>
              {surahNameArabic || `سُورَة ${surahName}`}
            </Text>
          </View>

          {/* ── Continuous Arabic text ── */}
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={s.textArea}
          >
            {/* Bismillah on first page */}
            {isFirst && hasBismillah && surahNumber !== 9 && (
              <Text style={s.bismillah}>
                بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ
              </Text>
            )}

            {/* Flowing Arabic text with inline ayah markers */}
            <Text style={s.arabicBlock}>
              {pageAyahs.map((ayah: any) => (
                <Text key={ayah.ayah_number}>
                  {ayah.text_arabic}
                  <Text style={s.ayahMarker}>{' '}﴿{toAr(ayah.ayah_number)}﴾{' '}</Text>
                </Text>
              ))}
            </Text>

            {/* Translation (toggled) */}
            {showTranslation && (
              <View style={s.translationBlock}>
                <View style={s.translationDivider} />
                {pageAyahs.map((ayah: any) => (
                  <Text key={`t-${ayah.ayah_number}`} style={s.translationLine}>
                    <Text style={s.translationNum}>{ayah.ayah_number}. </Text>
                    {ayah.translation || ''}
                  </Text>
                ))}
              </View>
            )}
          </ScrollView>

          {/* ── Navigation arrows ── */}
          {index < pages.length - 1 && (
            <TouchableOpacity style={s.arrowRight} onPress={() => goPage(1)} activeOpacity={0.7}>
              <Ionicons name="arrow-forward" size={22} color={GOLD} />
            </TouchableOpacity>
          )}
          {index > 0 && (
            <TouchableOpacity style={s.arrowLeft} onPress={() => goPage(-1)} activeOpacity={0.7}>
              <Ionicons name="arrow-back" size={22} color={GOLD} />
            </TouchableOpacity>
          )}

          {/* ── Page footer ── */}
          <View style={s.pageFooter}>
            <Text style={s.footerText}>
              Page {index + 1} - {surahName} - {ayahs.length} Verses
            </Text>
          </View>
        </View>
      </View>
    );
  }, [showTranslation, pages.length, surahName, surahNameArabic, hasBismillah, surahNumber, ayahs.length, goPage]);

  // ── Main render ──────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={s.safe}>
      {/* Header bar */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Ionicons name="arrow-back" size={22} color={GOLD_LIGHT} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>
          Page {currentPage + 1} of {pages.length || '…'}
        </Text>
        <View style={s.headerActions}>
          <TouchableOpacity
            onPress={() => setShowTranslation(v => !v)}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={s.headerBtn}
          >
            <Ionicons
              name={showTranslation ? 'eye' : 'eye-off'}
              size={20}
              color={showTranslation ? GOLD : GOLD_DIM}
            />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={toggleBookmark}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={s.headerBtn}
          >
            <Ionicons
              name={isPageBookmarked ? 'bookmark' : 'bookmark-outline'}
              size={20}
              color={isPageBookmarked ? GOLD : GOLD_DIM}
            />
          </TouchableOpacity>
        </View>
      </View>

      {loading ? (
        <View style={s.loadingWrap}>
          <ActivityIndicator size="large" color={GOLD} />
        </View>
      ) : ayahs.length === 0 ? (
        <View style={s.emptyWrap}>
          <Ionicons name="book-outline" size={48} color={GOLD_DIM} />
          <Text style={s.emptyTitle}>No ayahs loaded</Text>
          <Text style={s.emptySub}>Add ayah data via the Odoo backend</Text>
        </View>
      ) : (
        <FlatList
          ref={pagerRef}
          data={pages}
          horizontal
          pagingEnabled
          inverted
          showsHorizontalScrollIndicator={false}
          keyExtractor={(_, i) => String(i)}
          getItemLayout={(_, index) => ({
            length: SW,
            offset: SW * index,
            index,
          })}
          onMomentumScrollEnd={onPageChange}
          onScrollToIndexFailed={() => {}}
          renderItem={renderPage}
        />
      )}
    </SafeAreaView>
  );
}

// ── Colors ──────────────────────────────────────────────────────────────────
const BG_DARK = '#1C1410';
const BG_PAGE = '#1E1813';
const GOLD = '#C8A951';
const GOLD_LIGHT = '#E8D5A3';
const GOLD_DIM = '#7A6A42';
const BORDER_GOLD = '#3D3020';

// ── Styles ──────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BG_DARK },

  // ── Header ──
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    backgroundColor: BG_DARK, borderBottomWidth: 0.5, borderBottomColor: BORDER_GOLD,
  },
  headerTitle: { fontSize: 15, fontWeight: '600', color: GOLD_LIGHT },
  headerActions: { flexDirection: 'row', gap: 12 },
  headerBtn: { padding: 4 },

  loadingWrap: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  emptyTitle: { fontSize: 16, fontWeight: '600', color: GOLD_LIGHT, marginTop: 16 },
  emptySub: { fontSize: 13, color: GOLD_DIM, marginTop: 6 },

  // ── Page ──
  pageOuter: {
    width: SW,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  page: {
    flex: 1,
    backgroundColor: BG_PAGE,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: BORDER_GOLD,
  },

  // ── Ornamental surah header ──
  ornamentFrame: {
    marginHorizontal: 20,
    marginTop: 18,
    marginBottom: 8,
    borderWidth: 1.5,
    borderColor: GOLD,
    borderRadius: 4,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
    position: 'relative',
  },
  ornamentCornerTL: {
    position: 'absolute', top: -4, left: -4, width: 8, height: 8,
    borderTopWidth: 2, borderLeftWidth: 2, borderColor: GOLD,
  },
  ornamentCornerTR: {
    position: 'absolute', top: -4, right: -4, width: 8, height: 8,
    borderTopWidth: 2, borderRightWidth: 2, borderColor: GOLD,
  },
  ornamentCornerBL: {
    position: 'absolute', bottom: -4, left: -4, width: 8, height: 8,
    borderBottomWidth: 2, borderLeftWidth: 2, borderColor: GOLD,
  },
  ornamentCornerBR: {
    position: 'absolute', bottom: -4, right: -4, width: 8, height: 8,
    borderBottomWidth: 2, borderRightWidth: 2, borderColor: GOLD,
  },
  surahHeaderAr: {
    fontSize: 20, color: GOLD, fontWeight: '700', textAlign: 'center',
    letterSpacing: 2,
  },

  // ── Text area ──
  textArea: {
    paddingHorizontal: 20,
    paddingTop: 14,
    paddingBottom: 60, // space for arrows + footer
  },

  bismillah: {
    fontSize: 20, color: GOLD, textAlign: 'center',
    lineHeight: 40, marginBottom: 14,
  },

  arabicBlock: {
    fontSize: 22,
    lineHeight: 48,
    color: GOLD_LIGHT,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  ayahMarker: {
    fontSize: 16,
    color: GOLD,
  },

  // ── Translation overlay ──
  translationBlock: {
    marginTop: 20,
  },
  translationDivider: {
    height: 1, backgroundColor: BORDER_GOLD, marginBottom: 14,
  },
  translationLine: {
    fontSize: 13, color: GOLD_DIM, lineHeight: 21, marginBottom: 8,
  },
  translationNum: {
    fontWeight: '700', color: GOLD,
  },

  // ── Navigation arrows ──
  arrowRight: {
    position: 'absolute', right: 10, top: '50%', marginTop: -16,
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: BORDER_GOLD, justifyContent: 'center', alignItems: 'center',
  },
  arrowLeft: {
    position: 'absolute', left: 10, top: '50%', marginTop: -16,
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: BORDER_GOLD, justifyContent: 'center', alignItems: 'center',
  },

  // ── Page footer ──
  pageFooter: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    alignItems: 'center', paddingVertical: 10,
    borderTopWidth: 0.5, borderTopColor: BORDER_GOLD,
    backgroundColor: BG_PAGE,
  },
  footerText: {
    fontSize: 12, color: GOLD_DIM, letterSpacing: 0.5,
  },
});
