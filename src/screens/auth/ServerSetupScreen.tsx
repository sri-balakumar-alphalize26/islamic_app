import React, { useState, useRef } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView,
  Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../config';
import { fetchOdooDatabases, setServerConfig } from '../../api/client';
import { useAuthStore } from '../../contexts/AuthStore';

export default function ServerSetupScreen({ navigation }: any) {
  const markServerConfigured = useAuthStore((s) => s.markServerConfigured);
  const [serverUrl, setServerUrl] = useState('');
  const [databases, setDatabases] = useState<string[]>([]);
  const [selectedDb, setSelectedDb] = useState('');
  const [fetching, setFetching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fetched, setFetched] = useState(false);
  const fetchId = useRef(0);

  const normalizeUrl = (input: string) => {
    let url = input.trim().replace(/\/+$/, '');
    // If user pastes full URL with /api/v1 or /web, strip to base
    url = url.replace(/\/api\/v1.*$/, '').replace(/\/web.*$/, '');
    // Add http:// if no protocol
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = `http://${url}`;
    }
    return url;
  };

  const doFetchDatabases = async () => {
    const url = normalizeUrl(serverUrl);
    if (!url) {
      Alert.alert('Error', 'Please enter a server URL');
      return;
    }
    const myId = ++fetchId.current;
    setFetching(true);
    setDatabases([]);
    setSelectedDb('');
    setFetched(false);
    try {
      const dbs = await fetchOdooDatabases(url);
      if (myId !== fetchId.current) return;
      if (dbs.length === 0) {
        Alert.alert('No Databases', 'No databases with the Islamic App module installed were found on this server.');
      } else {
        setDatabases(dbs);
        if (dbs.length === 1) setSelectedDb(dbs[0]);
        setFetched(true);
      }
    } catch (e: any) {
      if (myId !== fetchId.current) return;
      const msg = e.message?.includes('timeout')
        ? 'Connection timed out. Check the URL and ensure the server is running.'
        : e.message?.includes('Network') || e.message?.includes('Cannot connect')
          ? 'Cannot reach the server. Check URL and network connection.'
          : `Failed to connect: ${e.message}`;
      Alert.alert('Connection Error', msg);
    }
    if (myId === fetchId.current) setFetching(false);
  };

  const doSave = async () => {
    if (!selectedDb) {
      Alert.alert('Error', 'Please select a database');
      return;
    }
    setSaving(true);
    try {
      const url = normalizeUrl(serverUrl);
      await setServerConfig(url, selectedDb);
      markServerConfigured();
      navigation.replace('LanguageSelect');
    } catch (e: any) {
      Alert.alert('Error', 'Failed to save server configuration');
    }
    setSaving(false);
  };

  return (
    <SafeAreaView style={s.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
          <View style={s.header}>
            <View style={s.logo}>
              <Text style={{ fontSize: 36, color: '#fff' }}>☪</Text>
            </View>
            <Text style={s.bis}>بسم الله الرحمن الرحيم</Text>
            <Text style={s.title}>Server Setup</Text>
            <Text style={s.subtitle}>Connect to your server</Text>
          </View>

          <Text style={s.label}>Server URL</Text>
          <View style={s.urlRow}>
            <TextInput
              style={[s.input, { flex: 1 }]}
              value={serverUrl}
              onChangeText={(text) => {
                fetchId.current++;
                setServerUrl(text);
                setFetched(false);
                setDatabases([]);
                setSelectedDb('');
              }}
              placeholder="e.g. 192.168.1.100:8069"
              placeholderTextColor={COLORS.textTertiary}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
          </View>
          <Text style={s.hint}>
            Enter IP or domain with port (e.g. 192.168.1.100:8069 or myserver.com:8069)
          </Text>

          <TouchableOpacity
            style={[s.fetchBtn, fetching && { opacity: 0.7 }]}
            onPress={doFetchDatabases}
            disabled={fetching}
          >
            {fetching ? (
              <ActivityIndicator color={COLORS.primary} />
            ) : (
              <Text style={s.fetchBtnText}>Fetch Databases</Text>
            )}
          </TouchableOpacity>

          {fetched && databases.length > 0 && (
            <View style={s.dbSection}>
              <Text style={s.label}>Select Database</Text>
              {databases.map((db) => (
                <TouchableOpacity
                  key={db}
                  style={[s.dbItem, selectedDb === db && s.dbItemSelected]}
                  onPress={() => setSelectedDb(db)}
                  activeOpacity={0.7}
                >
                  <View style={[s.radio, selectedDb === db && s.radioSelected]}>
                    {selectedDb === db && <View style={s.radioDot} />}
                  </View>
                  <Text style={[s.dbName, selectedDb === db && s.dbNameSelected]}>{db}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {selectedDb !== '' && (
            <TouchableOpacity
              style={[s.connectBtn, saving && { opacity: 0.7 }]}
              onPress={doSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={s.connectBtnText}>Connect</Text>
              )}
            </TouchableOpacity>
          )}

          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { flexGrow: 1, paddingHorizontal: 24 },
  header: { alignItems: 'center', paddingTop: 30, paddingBottom: 20 },
  logo: {
    width: 70, height: 70, borderRadius: 35,
    backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 12,
  },
  bis: { fontSize: 16, color: COLORS.gold, marginBottom: 12 },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.text },
  subtitle: { fontSize: 14, color: COLORS.textSecondary, marginTop: 4 },
  label: { fontSize: 13, fontWeight: '500', color: COLORS.textSecondary, marginBottom: 6, marginTop: 16 },
  input: {
    borderWidth: 1, borderColor: COLORS.border, borderRadius: 10,
    paddingHorizontal: 16, paddingVertical: 14,
    fontSize: 15, color: COLORS.text, backgroundColor: COLORS.backgroundSecondary,
  },
  urlRow: { flexDirection: 'row', gap: 8 },
  hint: { fontSize: 12, color: COLORS.textTertiary, marginTop: 4 },
  fetchBtn: {
    borderWidth: 1.5, borderColor: COLORS.primary, borderRadius: 10,
    paddingVertical: 14, alignItems: 'center', marginTop: 16,
  },
  fetchBtnText: { color: COLORS.primary, fontSize: 15, fontWeight: '600' },
  dbSection: { marginTop: 8 },
  dbItem: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 14, paddingHorizontal: 16, marginTop: 8,
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 10,
    borderWidth: 1.5, borderColor: 'transparent',
  },
  dbItemSelected: {
    borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight,
  },
  radio: {
    width: 20, height: 20, borderRadius: 10, borderWidth: 2,
    borderColor: COLORS.textTertiary, marginRight: 12,
    justifyContent: 'center', alignItems: 'center',
  },
  radioSelected: { borderColor: COLORS.primary },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.primary },
  dbName: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  dbNameSelected: { color: COLORS.primary, fontWeight: '600' },
  connectBtn: {
    backgroundColor: COLORS.primary, borderRadius: 10,
    paddingVertical: 16, alignItems: 'center', marginTop: 20,
  },
  connectBtnText: { color: '#fff', fontSize: 17, fontWeight: '600' },
});
