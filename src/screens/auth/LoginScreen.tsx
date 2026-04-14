import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';
import { fetchOdooDatabases, setServerConfig } from '../../api/client';

export default function LoginScreen({ navigation }: any) {
  const { t } = useTranslation();
  const { login } = useAuthStore();

  const HARDCODED_URL = 'http://115.246.240.218:9169';
  const HARDCODED_DB = 'odookra';
  const [serverUrl, setServerUrl] = useState(HARDCODED_URL);
  const [databases, setDatabases] = useState<string[]>([HARDCODED_DB]);
  const [selectedDb, setSelectedDb] = useState(HARDCODED_DB);
  const [fetchedForUrl, setFetchedForUrl] = useState(HARDCODED_URL);
  const [fetching, setFetching] = useState(false);
  const fetchId = useRef(0);

  const [email, setEmail] = useState('user@gmail.com');
  const [password, setPassword] = useState('user123');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  useEffect(() => {
    setServerConfig(HARDCODED_URL, HARDCODED_DB).catch(() => {});
  }, []);

  const normalizeUrl = (input: string) => {
    let url = input.trim().replace(/\/+$/, '');
    url = url.replace(/\/api\/v1.*$/, '').replace(/\/web.*$/, '');
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) url = `http://${url}`;
    return url;
  };

  const doFetchDatabases = async () => {
    const url = normalizeUrl(serverUrl);
    if (!url) { Alert.alert('Error', 'Please enter a server URL'); return; }
    const myId = ++fetchId.current;
    setFetching(true);
    setDatabases([]);
    setSelectedDb('');
    setFetchedForUrl('');
    try {
      const dbs = await fetchOdooDatabases(url);
      if (myId !== fetchId.current) return;
      if (dbs.length === 0) {
        Alert.alert('No Databases', 'No databases with the Islamic App module installed were found on this server.');
      } else {
        setDatabases(dbs);
        if (dbs.length === 1) setSelectedDb(dbs[0]);
        setFetchedForUrl(url);
      }
    } catch (e: any) {
      if (myId !== fetchId.current) return;
      const msg = e.message?.includes('timeout') ? 'Connection timed out.'
        : e.message?.includes('Network') || e.message?.includes('Cannot connect') ? 'Cannot reach the server.'
        : `Failed to connect: ${e.message}`;
      Alert.alert('Connection Error', msg);
    }
    if (myId === fetchId.current) setFetching(false);
  };

  const doLogin = async () => {
    if (!serverUrl.trim()) { Alert.alert('Error', 'Please enter a server URL'); return; }
    if (!selectedDb) { Alert.alert('Error', 'Please fetch and select a database'); return; }
    if (!email.trim() || !password.trim()) { Alert.alert('Error', 'Please fill in all fields'); return; }
    setLoading(true);
    try {
      const url = normalizeUrl(serverUrl);
      await setServerConfig(url, selectedDb);
      await login(email.trim(), password);
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.message || 'Login failed');
    }
    setLoading(false);
  };

  const dbListVisible = databases.length > 0 && normalizeUrl(serverUrl) === fetchedForUrl;

  return (
    <SafeAreaView style={s.c}><KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
        <View style={s.header}><View style={s.logo}><Text style={{ fontSize: 36, color: '#fff' }}>☪</Text></View><Text style={s.bis}>بسم الله الرحمن الرحيم</Text><Text style={s.title}>{t('auth.sign_in')}</Text></View>


        <Text style={s.label}>{t('auth.email')}</Text>
        <TextInput style={[s.input, s.readonly]} value={email} editable={false} placeholderTextColor={COLORS.textTertiary} />
        <Text style={s.label}>{t('auth.password')}</Text>
        <View style={{ position: 'relative' }}><TextInput style={[s.input, s.readonly, { paddingRight: 50 }]} value={password} editable={false} placeholderTextColor={COLORS.textTertiary} secureTextEntry={!showPw} /><TouchableOpacity style={{ position: 'absolute', right: 14, top: 14 }} onPress={() => setShowPw(!showPw)}><Text style={{ fontSize: 20 }}>{showPw ? '🙈' : '👁'}</Text></TouchableOpacity></View>
        <View style={{ height: 24 }} />
        <TouchableOpacity style={[s.btn, loading && { opacity: 0.7 }]} onPress={doLogin} disabled={loading}>{loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.sign_in')}</Text>}</TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView></SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  scroll: { flexGrow: 1, paddingHorizontal: 24 },
  header: { alignItems: 'center', paddingTop: 30, paddingBottom: 20 },
  logo: { width: 70, height: 70, borderRadius: 35, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  bis: { fontSize: 16, color: COLORS.gold, marginBottom: 16 },
  title: { fontSize: 26, fontWeight: '700', color: COLORS.text },
  label: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary, marginBottom: 6, marginTop: 12 },
  input: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: COLORS.text, backgroundColor: COLORS.backgroundSecondary },
  readonly: { color: COLORS.textSecondary, opacity: 0.85 },
  fetchBtn: { borderWidth: 1.5, borderColor: COLORS.primary, borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 10 },
  fetchBtnText: { color: COLORS.primary, fontSize: 14, fontWeight: '600' },
  dbItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, paddingHorizontal: 16, marginTop: 8, backgroundColor: COLORS.backgroundSecondary, borderRadius: 10, borderWidth: 1.5, borderColor: 'transparent' },
  dbItemSelected: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  radio: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: COLORS.textTertiary, marginRight: 12, justifyContent: 'center', alignItems: 'center' },
  radioSelected: { borderColor: COLORS.primary },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.primary },
  dbName: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  dbNameSelected: { color: COLORS.primary, fontWeight: '600' },
  forgot: { color: COLORS.primary, fontSize: 13, fontWeight: '500', textAlign: 'right', marginBottom: 24, marginTop: 8 },
  btn: { backgroundColor: COLORS.primary, borderRadius: 10, paddingVertical: 16, alignItems: 'center', marginBottom: 20 },
  btnText: { color: '#fff', fontSize: 17, fontWeight: '600' },
  divider: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  line: { flex: 1, height: 1, backgroundColor: COLORS.border },
  or: { marginHorizontal: 16, color: COLORS.textTertiary, fontSize: 13 },
  social: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingVertical: 14, marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'center', marginTop: 16, paddingBottom: 40 },
});
