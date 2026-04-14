import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { COLORS } from '../../config';
import { dhikrAPI } from '../../api/client';
import { useAuthStore } from '../../contexts/AuthStore';

export default function AdhkarCounterScreen({ route, navigation }: any) {
  const { refreshStats } = useAuthStore();

  const isSession = Array.isArray(route.params?.items) && route.params.items.length > 0;

  const sessionItems: any[] = isSession
    ? route.params.items
    : [{
        id: route.params?.adhkarId,
        arabic_text: route.params?.arabicText,
        translation: route.params?.title,
        repeat_count: route.params?.targetCount || 1,
      }];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [count, setCount] = useState(0);
  const [saving, setSaving] = useState(false);
  const [sessionDone, setSessionDone] = useState(false);
  const [totalRecited, setTotalRecited] = useState(0);

  const item = sessionItems[currentIndex];
  const target: number = item?.repeat_count || 1;
  const isLast = currentIndex === sessionItems.length - 1;
  const done = count >= target;
  const pct = Math.min(count / target, 1);

  const tap = useCallback(() => {
    if (done) return;
    setCount(c => c + 1);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
  }, [done]);

  const saveItem = async (c: number) => {
    if (c <= 0) return;
    try {
      await dhikrAPI.log({
        adhkar_id: item?.id || undefined,
        count: c,
        target,
        custom_text: !item?.id ? item?.arabic_text : undefined,
      });
      setTotalRecited(prev => prev + c);
    } catch (e) {}
  };

  const handleNext = async () => {
    setSaving(true);
    await saveItem(count);
    setSaving(false);
    if (isLast) {
      setSessionDone(true);
    } else {
      setCurrentIndex(i => i + 1);
      setCount(0);
    }
  };

  const handleClose = async () => {
    if (count > 0) {
      setSaving(true);
      await saveItem(count);
      setSaving(false);
    }
    await refreshStats();
    navigation.goBack();
  };

  // ── Session complete screen ──────────────────────────────────────────────────
  if (sessionDone) {
    return (
      <SafeAreaView style={s.c}>
        <View style={s.completionWrap}>
          <Ionicons name="checkmark-circle" size={80} color={COLORS.success} />
          <Text style={s.completeTitle}>Session Complete!</Text>
          <Text style={s.completeSub}>
            {sessionItems.length} adhkar completed{'\n'}
            {totalRecited} total recitations
          </Text>
          <TouchableOpacity
            style={s.doneBtn}
            onPress={async () => { await refreshStats(); navigation.goBack(); }}
          >
            <Ionicons name="checkmark-circle" size={20} color="#fff" />
            <Text style={s.doneTxt}>Close</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // ── Counter screen ───────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={s.c}>
      {/* Header — fixed, never scrolls */}
      <View style={s.header}>
        <TouchableOpacity onPress={handleClose} disabled={saving} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Ionicons name="close" size={24} color={COLORS.text} />
        </TouchableOpacity>
        {isSession
          ? <Text style={s.progress}>{currentIndex + 1} of {sessionItems.length}</Text>
          : <Text style={s.ht} numberOfLines={1}>{item?.translation || ''}</Text>}
        <TouchableOpacity onPress={() => setCount(0)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Text style={s.reset}>Reset</Text>
        </TouchableOpacity>
      </View>

      {/* Session progress bar */}
      {isSession && (
        <View style={s.sessionBarTrack}>
          <View style={[s.sessionBarFill, { width: `${(currentIndex / sessionItems.length) * 100}%` }]} />
        </View>
      )}

      {/* Scrollable body — prevents content from hiding behind header or off-screen */}
      <ScrollView
        contentContainerStyle={s.body}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={s.arabic}>{item?.arabic_text}</Text>

        {item?.translation
          ? <Text style={s.translation}>{item.translation}</Text>
          : null}

        {/* Tap circle */}
        <TouchableOpacity
          style={[s.circle, done && s.circleDone]}
          onPress={tap}
          activeOpacity={0.75}
        >
          <Text style={s.circleNum}>{count}</Text>
          <Text style={s.circleTarget}>/ {target}</Text>
        </TouchableOpacity>

        {/* Progress bar */}
        <View style={s.bar}>
          <View style={[s.fill, { width: `${pct * 100}%` }]} />
        </View>

        <Text style={s.status}>
          {done ? 'Completed!' : `${target - count} remaining`}
        </Text>
        {!done && <Text style={s.hint}>Tap to count</Text>}

        {/* Next / Finish */}
        {done && (
          <TouchableOpacity style={s.nextBtn} onPress={handleNext} disabled={saving} activeOpacity={0.85}>
            {saving
              ? <Text style={s.nextTxt}>Saving...</Text>
              : <>
                  <Text style={s.nextTxt}>{isLast ? 'Finish' : 'Next'}</Text>
                  <Ionicons
                    name={isLast ? 'checkmark-circle' : 'arrow-forward'}
                    size={20}
                    color="#fff"
                  />
                </>}
          </TouchableOpacity>
        )}

        {/* Skip */}
        {isSession && !done && (
          <TouchableOpacity style={s.skipBtn} onPress={handleNext} disabled={saving}>
            <Text style={s.skipTxt}>Skip</Text>
            <Ionicons name="arrow-forward" size={15} color={COLORS.textTertiary} />
          </TouchableOpacity>
        )}

        <View style={{ height: 24 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12 },
  ht: { flex: 1, textAlign: 'center', fontSize: 15, fontWeight: '500', color: COLORS.text, marginHorizontal: 8 },
  progress: { flex: 1, textAlign: 'center', fontSize: 16, fontWeight: '700', color: COLORS.text },
  reset: { fontSize: 13, color: COLORS.primary, fontWeight: '500' },

  // Session bar
  sessionBarTrack: { height: 4, backgroundColor: COLORS.borderLight, marginHorizontal: 16, borderRadius: 2, marginBottom: 4 },
  sessionBarFill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 2 },

  // Body — scrollable, centered
  body: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24, paddingTop: 8 },
  arabic: { fontSize: 22, lineHeight: 40, textAlign: 'center', color: COLORS.text, marginBottom: 10, paddingHorizontal: 8 },
  translation: { fontSize: 13, color: COLORS.textSecondary, textAlign: 'center', lineHeight: 20, marginBottom: 20, paddingHorizontal: 8 },

  // Count circle — reduced from 180 to 148
  circle: { width: 148, height: 148, borderRadius: 74, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
  circleDone: { backgroundColor: COLORS.success },
  circleNum: { fontSize: 46, fontWeight: '700', color: '#fff' },
  circleTarget: { fontSize: 15, color: 'rgba(255,255,255,0.7)' },

  // Progress bar
  bar: { width: '80%', height: 6, backgroundColor: COLORS.borderLight, borderRadius: 3, marginBottom: 12 },
  fill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 3 },

  status: { fontSize: 16, fontWeight: '600', color: COLORS.text },
  hint: { fontSize: 13, color: COLORS.textTertiary, marginTop: 4 },

  // Next / Finish button
  nextBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: COLORS.success, borderRadius: 12, paddingHorizontal: 28, paddingVertical: 14, marginTop: 18 },
  nextTxt: { color: '#fff', fontSize: 16, fontWeight: '600' },

  // Skip
  skipBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 14 },
  skipTxt: { fontSize: 14, color: COLORS.textTertiary },

  // Session complete
  completionWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  completeTitle: { fontSize: 26, fontWeight: '700', color: COLORS.text, marginTop: 16, marginBottom: 12 },
  completeSub: { fontSize: 16, color: COLORS.textSecondary, textAlign: 'center', lineHeight: 26 },
  doneBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: COLORS.primary, borderRadius: 12, paddingHorizontal: 32, paddingVertical: 14, marginTop: 32 },
  doneTxt: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
