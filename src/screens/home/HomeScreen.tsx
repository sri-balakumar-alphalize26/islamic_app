import React, { useState, useEffect, useRef } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Modal, FlatList, Linking, ActivityIndicator, AppState } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import { COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';
import {
  calculatePrayerTimes,
  getNextPrayer,
  formatMinutesLeft,
  PRESET_CITIES,
  PrayerTimes,
  NextPrayer,
} from '../../utils/prayerTimes';
import QiblaWidget from '../../components/QiblaWidget';

const PRAYER_LOC_KEY = '@prayer_location';

type LocState = 'loading' | 'granted' | 'denied' | 'idle';

export default function HomeScreen() {
  const { t } = useTranslation();
  const nav = useNavigation<any>();
  const { user } = useAuthStore();
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? t('home.greeting_morning')
    : hour < 17 ? t('home.greeting_afternoon')
    : t('home.greeting_evening');

  const [locState, setLocState] = useState<LocState>('idle');
  const [cityName, setCityName] = useState<string | null>(null);
  const [prayerTimes, setPrayerTimes] = useState<PrayerTimes | null>(null);
  const [nextPrayer, setNextPrayer] = useState<NextPrayer | null>(null);
  const [showCityPicker, setShowCityPicker] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const applyTimes = (times: PrayerTimes) => {
    setPrayerTimes(times);
    setNextPrayer(getNextPrayer(times));
  };

  const applyCoords = async (c: { latitude: number; longitude: number }) => {
    setCoords({ lat: c.latitude, lng: c.longitude });
    applyTimes(calculatePrayerTimes(c.latitude, c.longitude));
    try {
      const places = await Location.reverseGeocodeAsync(c);
      const place = places?.[0];
      setCityName(place?.city || place?.region || 'Your Location');
    } catch {
      setCityName('Your Location');
    }
  };

  const loadCached = async () => {
    const stored = await AsyncStorage.getItem(PRAYER_LOC_KEY);
    if (stored) {
      const loc = JSON.parse(stored);
      setCityName(loc.name);
      setCoords({ lat: loc.lat, lng: loc.lng });
      applyTimes(calculatePrayerTimes(loc.lat, loc.lng));
    }
  };

  // Location fetch logic (reusable for mount + foreground resume)
  const fetchLocation = async () => {
    setLocState('loading');
    try {
      if (!(await Location.hasServicesEnabledAsync())) {
        setLocState('denied');
        await loadCached();
        return;
      }
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocState('denied');
        await loadCached();
        return;
      }

      const last = await Location.getLastKnownPositionAsync({ maxAge: 10 * 60 * 1000 });
      if (last) {
        await applyCoords(last.coords);
        setLocState('granted');
      }

      const tryFix = (accuracy: Location.LocationAccuracy, timeoutMs: number) =>
        Promise.race<Location.LocationObject | null>([
          Location.getCurrentPositionAsync({ accuracy }),
          new Promise<null>((r) => setTimeout(() => r(null), timeoutMs)),
        ]);

      let fresh = await tryFix(Location.Accuracy.Balanced, 15000);
      if (!fresh) fresh = await tryFix(Location.Accuracy.Low, 10000);

      if (fresh) {
        await applyCoords(fresh.coords);
        setLocState('granted');
      } else if (!last) {
        setLocState('denied');
        await loadCached();
      }
    } catch (e: any) {
      console.warn('Location fetch failed:', e?.message);
      setLocState('denied');
      await loadCached();
    }
  };

  // Try device location on mount
  useEffect(() => { fetchLocation(); }, []);

  // Re-check location when app returns to foreground (e.g. after enabling in Settings)
  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active' && (locState === 'denied' || !coords)) {
        fetchLocation();
      }
    });
    return () => sub.remove();
  }, [locState, coords]);

  // Update "next prayer" every minute
  useEffect(() => {
    if (!prayerTimes) return;
    timerRef.current = setInterval(() => setNextPrayer(getNextPrayer(prayerTimes)), 60000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [prayerTimes]);

  const selectCity = async (city: { name: string; lat: number; lng: number }) => {
    try {
      await AsyncStorage.setItem(PRAYER_LOC_KEY, JSON.stringify(city));
      setCityName(city.name);
      setCoords({ lat: city.lat, lng: city.lng });
      applyTimes(calculatePrayerTimes(city.lat, city.lng));
      setShowCityPicker(false);
    } catch {}
  };

  const openSettings = () => Linking.openSettings();

  return (
    <SafeAreaView style={s.c}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={s.header}>
          <View>
            <Text style={s.greet}>{greeting}</Text>
            <Text style={s.name}>{user?.name || 'User'}</Text>
          </View>
          <TouchableOpacity style={s.aiBtn} onPress={() => nav.navigate('AIAssistant')}>
            <Ionicons name="sparkles" size={22} color={COLORS.primary} />
          </TouchableOpacity>
        </View>

        {/* Prayer Times Widget */}
        {locState === 'loading' && (
          <View style={s.prayerLoading}>
            <ActivityIndicator size="small" color={COLORS.primary} />
            <Text style={s.prayerLoadingTxt}>Getting your location…</Text>
          </View>
        )}

        {locState === 'denied' && !prayerTimes && (
          <View style={s.prayerDenied}>
            <Ionicons name="location-outline" size={20} color={COLORS.warning} />
            <Text style={s.prayerDeniedTxt}>Enable location to see prayer times</Text>
            <View style={s.prayerDeniedRow}>
              <TouchableOpacity style={s.settingsBtn} onPress={openSettings}>
                <Text style={s.settingsBtnTxt}>Open Settings</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.manualBtn} onPress={() => setShowCityPicker(true)}>
                <Text style={s.manualBtnTxt}>Pick City</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {nextPrayer && (
          <TouchableOpacity
            style={s.prayerCard}
            onPress={() => locState === 'denied' && setShowCityPicker(true)}
            activeOpacity={locState === 'denied' ? 0.85 : 1}
          >
            <View style={s.prayerIconWrap}>
              <Text style={{ fontSize: 20 }}>🕌</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.prayerLabel}>Next Prayer · {nextPrayer.name}</Text>
              <Text style={s.prayerTime}>
                {nextPrayer.time} · {formatMinutesLeft(nextPrayer.minutesLeft)} remaining
              </Text>
            </View>
            <View style={s.prayerLocWrap}>
              <Ionicons
                name={locState === 'granted' ? 'location' : 'location-outline'}
                size={13}
                color="rgba(255,255,255,0.75)"
              />
              <Text style={s.prayerLocTxt}>{cityName}</Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Stats Grid — same as profile */}
        <View style={s.grid}>
          {[
            { icon: 'hand-left-outline' as const, label: t('profile.total_dhikr'), value: user?.stats?.total_dhikr || 0 },
            { icon: 'flame-outline' as const, label: t('profile.current_streak'), value: `${user?.stats?.current_streak || 0} days` },
            { icon: 'book-outline' as const, label: t('profile.pages_read'), value: user?.stats?.quran_pages || 0 },
            { icon: 'headset-outline' as const, label: t('profile.listening_time'), value: `${Math.round(user?.stats?.listening_minutes || 0)} min` },
          ].map((st, i) => (
            <View key={i} style={s.stat}>
              <Ionicons name={st.icon} size={22} color={COLORS.primary} />
              <Text style={s.sv}>{st.value}</Text>
              <Text style={s.sl}>{st.label}</Text>
            </View>
          ))}
        </View>

        {/* Qibla Finder */}
        <QiblaWidget
          latitude={coords?.lat ?? null}
          longitude={coords?.lng ?? null}
          locationDenied={locState === 'denied' && !coords}
        />

        {/* Admin */}
        {(user?.role === 'admin' || user?.role === 'special') && (
          <TouchableOpacity style={s.admin} onPress={() => nav.navigate('AdminDashboard')}>
            <Ionicons name="settings-outline" size={20} color={COLORS.primary} />
            <Text style={s.adminTxt}>{t('admin.dashboard')}</Text>
            <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
          </TouchableOpacity>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* City Picker Modal (fallback when location denied) */}
      <Modal visible={showCityPicker} animationType="slide" transparent presentationStyle="overFullScreen">
        <View style={s.overlay}>
          <View style={s.sheet}>
            <View style={s.sheetHeader}>
              <Text style={s.sheetTitle}>Select City</Text>
              <TouchableOpacity onPress={() => setShowCityPicker(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            <FlatList
              data={PRESET_CITIES}
              keyExtractor={item => item.name}
              ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: COLORS.borderLight }} />}
              renderItem={({ item }) => (
                <TouchableOpacity style={s.cityRow} onPress={() => selectCity(item)} activeOpacity={0.7}>
                  <Ionicons
                    name="location"
                    size={18}
                    color={cityName === item.name ? COLORS.primary : COLORS.textTertiary}
                  />
                  <Text style={[s.cityName, cityName === item.name && s.cityNameActive]}>
                    {item.name}
                  </Text>
                  {cityName === item.name && <Ionicons name="checkmark" size={18} color={COLORS.primary} />}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },

  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 24, paddingTop: 16 },
  greet: { fontSize: 15, color: COLORS.textSecondary },
  name: { fontSize: 20, fontWeight: '700', color: COLORS.text, marginTop: 2 },
  aiBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.primaryLight, justifyContent: 'center', alignItems: 'center' },

  prayerLoading: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 24, marginBottom: 16, padding: 14, backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, gap: 10 },
  prayerLoadingTxt: { fontSize: 14, color: COLORS.textSecondary },

  prayerDenied: { marginHorizontal: 24, marginBottom: 16, padding: 16, backgroundColor: '#FFF8E1', borderRadius: 14, borderWidth: 1, borderColor: '#FFE082' },
  prayerDeniedTxt: { fontSize: 14, color: COLORS.text, fontWeight: '500', marginLeft: 4, marginTop: 4 },
  prayerDeniedRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  settingsBtn: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 8, paddingVertical: 10, alignItems: 'center' },
  settingsBtnTxt: { color: '#fff', fontSize: 13, fontWeight: '600' },
  manualBtn: { flex: 1, backgroundColor: COLORS.backgroundSecondary, borderRadius: 8, paddingVertical: 10, alignItems: 'center' },
  manualBtnTxt: { color: COLORS.text, fontSize: 13, fontWeight: '600' },

  prayerCard: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 24, marginBottom: 16, backgroundColor: COLORS.primaryDark, borderRadius: 16, padding: 16, gap: 12 },
  prayerIconWrap: { width: 38, height: 38, borderRadius: 19, backgroundColor: 'rgba(255,255,255,0.15)', justifyContent: 'center', alignItems: 'center' },
  prayerLabel: { fontSize: 12, color: 'rgba(255,255,255,0.75)', marginBottom: 3 },
  prayerTime: { fontSize: 15, fontWeight: '700', color: '#fff' },
  prayerLocWrap: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  prayerLocTxt: { fontSize: 11, color: 'rgba(255,255,255,0.65)' },

  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 24, gap: 12, marginBottom: 8 },
  stat: { width: '47%', backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16, alignItems: 'center' },
  sv: { fontSize: 18, fontWeight: '700', color: COLORS.text, marginTop: 6 },
  sl: { fontSize: 11, color: COLORS.textTertiary, marginTop: 2, textAlign: 'center' },

  admin: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 24, marginTop: 20, padding: 16, backgroundColor: COLORS.backgroundSecondary, borderRadius: 14 },
  adminTxt: { flex: 1, fontSize: 15, fontWeight: '500', color: COLORS.text, marginLeft: 10 },

  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, paddingBottom: 34, maxHeight: '70%' },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 0.5, borderBottomColor: COLORS.border },
  sheetTitle: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  cityRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 14, gap: 12 },
  cityName: { flex: 1, fontSize: 15, color: COLORS.text },
  cityNameActive: { color: COLORS.primary, fontWeight: '600' },
});
