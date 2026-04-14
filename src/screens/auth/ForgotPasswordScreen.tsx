import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { authAPI } from '../../api/client';

type Step = 'email' | 'otp';

export default function ForgotPasswordScreen({ navigation }: any) {
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const sendOtp = async () => {
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) { Alert.alert('Error', 'Please enter your email address'); return; }
    setLoading(true);
    try {
      const res = await authAPI.forgotPassword(trimmed);
      const devOtp = res.data?.dev_otp;
      if (devOtp) {
        // Dev mode: auto-fill OTP for testing
        setOtp(devOtp);
        Alert.alert('Code Sent (Dev)', `Your reset code is: ${devOtp}`);
      } else {
        Alert.alert('Code Sent', 'If an account exists with this email, a 6-digit reset code has been sent.');
      }
      setStep('otp');
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.message || 'Failed to send reset code');
    }
    setLoading(false);
  };

  const resetPassword = async () => {
    if (!otp.trim() || otp.trim().length !== 6) { Alert.alert('Error', 'Enter the 6-digit code'); return; }
    if (!newPassword || newPassword.length < 6) { Alert.alert('Error', 'Password must be at least 6 characters'); return; }
    if (newPassword !== confirmPw) { Alert.alert('Error', 'Passwords do not match'); return; }
    setLoading(true);
    try {
      await authAPI.resetPassword(email.trim().toLowerCase(), otp.trim(), newPassword);
      Alert.alert('Success', 'Password reset successful. You can now sign in.', [
        { text: 'Sign In', onPress: () => navigation.navigate('Login') },
      ]);
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.message || 'Reset failed');
    }
    setLoading(false);
  };

  return (
    <SafeAreaView style={s.c}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
          {/* Back button */}
          <TouchableOpacity style={s.back} onPress={() => navigation.goBack()}>
            <Ionicons name="arrow-back" size={22} color={COLORS.text} />
          </TouchableOpacity>

          {/* Header */}
          <View style={s.header}>
            <View style={s.iconWrap}>
              <Ionicons name={step === 'email' ? 'mail-outline' : 'key-outline'} size={32} color={COLORS.primary} />
            </View>
            <Text style={s.title}>
              {step === 'email' ? (t('auth.forgot_password') || 'Forgot Password?') : 'Reset Password'}
            </Text>
            <Text style={s.sub}>
              {step === 'email'
                ? 'Enter your email and we\'ll send you a reset code'
                : `Enter the 6-digit code sent to ${email}`}
            </Text>
          </View>

          {step === 'email' ? (
            <>
              <Text style={s.label}>{t('auth.email')}</Text>
              <TextInput
                style={s.input}
                value={email}
                onChangeText={setEmail}
                placeholder="email@example.com"
                placeholderTextColor={COLORS.textTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoFocus
              />
              <TouchableOpacity
                style={[s.btn, loading && { opacity: 0.7 }]}
                onPress={sendOtp}
                disabled={loading}
              >
                {loading
                  ? <ActivityIndicator color="#fff" />
                  : <Text style={s.btnTxt}>Send Reset Code</Text>}
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Text style={s.label}>Reset Code</Text>
              <TextInput
                style={[s.input, s.otpInput]}
                value={otp}
                onChangeText={setOtp}
                placeholder="000000"
                placeholderTextColor={COLORS.textTertiary}
                keyboardType="number-pad"
                maxLength={6}
                autoFocus
              />

              <Text style={s.label}>New Password</Text>
              <View style={{ position: 'relative' }}>
                <TextInput
                  style={[s.input, { paddingRight: 50 }]}
                  value={newPassword}
                  onChangeText={setNewPassword}
                  placeholder="Min 6 characters"
                  placeholderTextColor={COLORS.textTertiary}
                  secureTextEntry={!showPw}
                />
                <TouchableOpacity style={s.eyeBtn} onPress={() => setShowPw(!showPw)}>
                  <Ionicons name={showPw ? 'eye-off' : 'eye'} size={20} color={COLORS.textTertiary} />
                </TouchableOpacity>
              </View>

              <Text style={s.label}>{t('auth.confirm_password') || 'Confirm Password'}</Text>
              <TextInput
                style={s.input}
                value={confirmPw}
                onChangeText={setConfirmPw}
                placeholder="Repeat password"
                placeholderTextColor={COLORS.textTertiary}
                secureTextEntry={!showPw}
              />

              <TouchableOpacity
                style={[s.btn, loading && { opacity: 0.7 }]}
                onPress={resetPassword}
                disabled={loading}
              >
                {loading
                  ? <ActivityIndicator color="#fff" />
                  : <Text style={s.btnTxt}>Reset Password</Text>}
              </TouchableOpacity>

              <TouchableOpacity style={s.resend} onPress={sendOtp} disabled={loading}>
                <Text style={s.resendTxt}>Didn't receive the code? Resend</Text>
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  scroll: { flexGrow: 1, paddingHorizontal: 24, paddingBottom: 40 },
  back: { marginTop: 12, width: 40 },
  header: { alignItems: 'center', marginTop: 20, marginBottom: 30 },
  iconWrap: {
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: COLORS.primaryLight, justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.text },
  sub: { fontSize: 14, color: COLORS.textSecondary, marginTop: 6, textAlign: 'center', lineHeight: 20, paddingHorizontal: 16 },
  label: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary, marginBottom: 6, marginTop: 16 },
  input: {
    borderWidth: 1, borderColor: COLORS.border, borderRadius: 10,
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 15,
    color: COLORS.text, backgroundColor: COLORS.backgroundSecondary,
  },
  otpInput: { fontSize: 24, fontWeight: '700', textAlign: 'center', letterSpacing: 8 },
  eyeBtn: { position: 'absolute', right: 14, top: 14 },
  btn: {
    backgroundColor: COLORS.primary, borderRadius: 10,
    paddingVertical: 16, alignItems: 'center', marginTop: 24,
  },
  btnTxt: { color: '#fff', fontSize: 17, fontWeight: '600' },
  resend: { alignItems: 'center', marginTop: 20 },
  resendTxt: { fontSize: 14, color: COLORS.primary, fontWeight: '500' },
});
