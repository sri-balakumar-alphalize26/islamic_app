import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { COLORS } from '../../config';

export default function SplashScreen() {
  return (
    <View style={s.container}>
      <View style={s.logo}><Text style={s.icon}>☪</Text></View>
      <Text style={s.name}>Islamic App</Text>
      <Text style={s.bis}>بسم الله الرحمن الرحيم</Text>
      <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 30 }} />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' },
  logo: { width: 100, height: 100, borderRadius: 50, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
  icon: { fontSize: 48, color: '#fff' },
  name: { fontSize: 26, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  bis: { fontSize: 18, color: COLORS.gold },
});
