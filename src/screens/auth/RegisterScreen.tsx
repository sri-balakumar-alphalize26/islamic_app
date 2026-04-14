import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { COLORS } from '../../config';
import { useAuthStore } from '../../contexts/AuthStore';
export default function RegisterScreen({ navigation }: any) {
  const { t } = useTranslation();
  const { register } = useAuthStore();
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [phone, setPhone] = useState(''); const [password, setPassword] = useState(''); const [confirm, setConfirm] = useState(''); const [loading, setLoading] = useState(false);
  const doReg = async () => {
    if (!name || !password || (!email && !phone)) { Alert.alert('Error', 'Fill required fields'); return; }
    if (password !== confirm) { Alert.alert('Error', 'Passwords do not match'); return; }
    if (password.length < 6) { Alert.alert('Error', 'Min 6 characters'); return; }
    setLoading(true);
    try {
      await register({ name, email: email || undefined, phone_number: phone || undefined, password });
      // After successful registration, go to language select then login
      Alert.alert('Success', 'Account created! Please sign in.', [
        { text: 'OK', onPress: () => navigation.navigate('Login') },
      ]);
    } catch (e: any) { Alert.alert('Error', e.response?.data?.message || 'Registration failed'); }
    setLoading(false);
  };
  return (
    <SafeAreaView style={s.c}><KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}><ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
      <Text style={s.title}>{t('auth.sign_up')}</Text><Text style={s.sub}>{t('auth.create_account') || 'Create your account'}</Text>
      <Text style={s.label}>{t('auth.full_name')} *</Text><TextInput style={s.input} value={name} onChangeText={setName} placeholder="Your Name" placeholderTextColor={COLORS.textTertiary} />
      <Text style={s.label}>{t('auth.email')}</Text><TextInput style={s.input} value={email} onChangeText={setEmail} placeholder="email@example.com" placeholderTextColor={COLORS.textTertiary} keyboardType="email-address" autoCapitalize="none" />
      <Text style={s.label}>{t('auth.phone')}</Text><TextInput style={s.input} value={phone} onChangeText={setPhone} placeholder="+1234567890" placeholderTextColor={COLORS.textTertiary} keyboardType="phone-pad" />
      <Text style={s.label}>{t('auth.password')} *</Text><TextInput style={s.input} value={password} onChangeText={setPassword} placeholder="••••••••" placeholderTextColor={COLORS.textTertiary} secureTextEntry />
      <Text style={s.label}>{t('auth.confirm_password') || 'Confirm'} *</Text><TextInput style={s.input} value={confirm} onChangeText={setConfirm} placeholder="••••••••" placeholderTextColor={COLORS.textTertiary} secureTextEntry />
      <TouchableOpacity style={[s.btn, loading && { opacity: 0.7 }]} onPress={doReg} disabled={loading}>{loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnTxt}>{t('auth.sign_up')}</Text>}</TouchableOpacity>
      <View style={s.row}><Text style={{ fontSize: 15, color: COLORS.textSecondary }}>{t('auth.have_account')} </Text><TouchableOpacity onPress={() => navigation.goBack()}><Text style={{ fontSize: 15, color: COLORS.primary, fontWeight: '600' }}>{t('auth.sign_in')}</Text></TouchableOpacity></View>
    </ScrollView></KeyboardAvoidingView></SafeAreaView>
  );
}
const s = StyleSheet.create({ c: { flex: 1, backgroundColor: '#fff' }, scroll: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 40 }, title: { fontSize: 26, fontWeight: '700', color: COLORS.text }, sub: { fontSize: 15, color: COLORS.textSecondary, marginTop: 4, marginBottom: 10 }, label: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary, marginBottom: 6, marginTop: 12 }, input: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: COLORS.text, backgroundColor: COLORS.backgroundSecondary }, btn: { backgroundColor: COLORS.primary, borderRadius: 10, paddingVertical: 16, alignItems: 'center', marginTop: 24 }, btnTxt: { color: '#fff', fontSize: 17, fontWeight: '600' }, row: { flexDirection: 'row', justifyContent: 'center', marginTop: 20, paddingBottom: 40 } });
