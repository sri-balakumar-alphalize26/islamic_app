import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';

export default function LoginScreen({ navigation }: any) {
  const { t } = useTranslation();
  const { login } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const doLogin = async () => {
    if (!email.trim() || !password.trim()) { Alert.alert('Error', 'Please fill in all fields'); return; }
    setLoading(true);
    try { await login(email.trim(), password); } catch (e: any) { Alert.alert('Error', e.response?.data?.message || 'Login failed'); }
    setLoading(false);
  };
  return (
    <SafeAreaView style={s.c}><KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
    <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
      <View style={s.header}><View style={s.logo}><Text style={{ fontSize: 36, color: '#fff' }}>☪</Text></View><Text style={s.bis}>بسم الله الرحمن الرحيم</Text><Text style={s.title}>{t('auth.sign_in')}</Text></View>
      <Text style={s.label}>{t('auth.email')}</Text>
      <TextInput style={s.input} value={email} onChangeText={setEmail} placeholder="email@example.com" placeholderTextColor={COLORS.textTertiary} keyboardType="email-address" autoCapitalize="none" />
      <Text style={s.label}>{t('auth.password')}</Text>
      <View style={{ position: 'relative' }}><TextInput style={[s.input, { paddingRight: 50 }]} value={password} onChangeText={setPassword} placeholder="••••••••" placeholderTextColor={COLORS.textTertiary} secureTextEntry={!showPw} /><TouchableOpacity style={{ position: 'absolute', right: 14, top: 14 }} onPress={() => setShowPw(!showPw)}><Text style={{ fontSize: 20 }}>{showPw ? '🙈' : '👁'}</Text></TouchableOpacity></View>
      <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}><Text style={s.forgot}>{t('auth.forgot_password')}</Text></TouchableOpacity>
      <TouchableOpacity style={[s.btn, loading && { opacity: 0.7 }]} onPress={doLogin} disabled={loading}>{loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.sign_in')}</Text>}</TouchableOpacity>
      <View style={s.divider}><View style={s.line} /><Text style={s.or}>{t('auth.or')}</Text><View style={s.line} /></View>
      <TouchableOpacity style={s.social}><Text style={{ fontSize: 18, fontWeight: '700', color: '#4285F4', marginRight: 10 }}>G</Text><Text style={{ fontSize: 15, fontWeight: '500', color: COLORS.text }}>{t('auth.continue_google')}</Text></TouchableOpacity>
      <View style={s.row}><Text style={{ fontSize: 15, color: COLORS.textSecondary }}>{t('auth.no_account')} </Text><TouchableOpacity onPress={() => navigation.navigate('Register')}><Text style={{ fontSize: 15, color: COLORS.primary, fontWeight: '600' }}>{t('auth.sign_up')}</Text></TouchableOpacity></View>
    </ScrollView></KeyboardAvoidingView></SafeAreaView>
  );
}
const s = StyleSheet.create({ c: { flex: 1, backgroundColor: '#fff' }, scroll: { flexGrow: 1, paddingHorizontal: 24 }, header: { alignItems: 'center', paddingTop: 30, paddingBottom: 20 }, logo: { width: 70, height: 70, borderRadius: 35, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 12 }, bis: { fontSize: 16, color: COLORS.gold, marginBottom: 16 }, title: { fontSize: 26, fontWeight: '700', color: COLORS.text }, label: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary, marginBottom: 6, marginTop: 12 }, input: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: COLORS.text, backgroundColor: COLORS.backgroundSecondary }, forgot: { color: COLORS.primary, fontSize: 13, fontWeight: '500', textAlign: 'right', marginBottom: 24, marginTop: 8 }, btn: { backgroundColor: COLORS.primary, borderRadius: 10, paddingVertical: 16, alignItems: 'center', marginBottom: 20 }, btnText: { color: '#fff', fontSize: 17, fontWeight: '600' }, divider: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 }, line: { flex: 1, height: 1, backgroundColor: COLORS.border }, or: { marginHorizontal: 16, color: COLORS.textTertiary, fontSize: 13 }, social: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingVertical: 14, marginBottom: 12 }, row: { flexDirection: 'row', justifyContent: 'center', marginTop: 16, paddingBottom: 40 } });
