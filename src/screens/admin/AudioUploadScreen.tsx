import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, SafeAreaView,
  ActivityIndicator, Alert, TextInput, Modal, ScrollView, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { audioAPI, adminAPI } from '../../api/client';

const AUDIO_TYPES = [
  { label: 'Quran Recitation', value: 'quran' },
  { label: 'Nasheed', value: 'nasheed' },
  { label: 'Lecture', value: 'lecture' },
  { label: 'Dua', value: 'dua' },
  { label: 'Adhkar', value: 'adhkar' },
];

const LANGUAGES = [
  { label: 'Arabic', value: 'ar' },
  { label: 'English', value: 'en' },
  { label: 'French', value: 'fr' },
  { label: 'Turkish', value: 'tr' },
  { label: 'Hindi', value: 'hi' },
];

const stateBadge = (state: string) => {
  switch (state) {
    case 'published': return { bg: COLORS.success + '20', color: COLORS.success, label: 'Published' };
    case 'draft': return { bg: COLORS.warning + '20', color: COLORS.warning, label: 'Draft' };
    default: return { bg: COLORS.border, color: COLORS.textSecondary, label: state || 'Unknown' };
  }
};

export default function AudioUploadScreen({ navigation }: any) {
  const [tracks, setTracks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [form, setForm] = useState({
    name: '', name_ar: '', audio_type: 'quran', reciter_name: '',
    audio_url: '', duration: '', language: 'ar',
  });
  const [typePickerOpen, setTypePickerOpen] = useState(false);
  const [langPickerOpen, setLangPickerOpen] = useState(false);

  const fetchTracks = useCallback(async () => {
    try {
      const res = await audioAPI.list();
      const data = res.data?.data || res.data || [];
      setTracks(Array.isArray(data) ? data : []);
    } catch (e: any) {
      Alert.alert('Error', 'Failed to load audio tracks');
    }
  }, []);

  useEffect(() => {
    fetchTracks().finally(() => setLoading(false));
  }, [fetchTracks]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchTracks();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!form.name.trim()) {
      Alert.alert('Validation', 'Name is required');
      return;
    }
    if (!form.audio_url.trim()) {
      Alert.alert('Validation', 'Audio URL is required');
      return;
    }
    setCreating(true);
    try {
      await audioAPI.create({
        name: form.name,
        name_ar: form.name_ar,
        audio_type: form.audio_type,
        reciter_name: form.reciter_name,
        audio_url: form.audio_url,
        duration: parseInt(form.duration, 10) || 0,
        language: form.language,
      });
      setShowCreate(false);
      setForm({ name: '', name_ar: '', audio_type: 'quran', reciter_name: '', audio_url: '', duration: '', language: 'ar' });
      await fetchTracks();
      Alert.alert('Success', 'Audio track created');
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.error || 'Failed to create audio');
    } finally {
      setCreating(false);
    }
  };

  const handlePublish = async (id: number) => {
    try {
      await adminAPI.publishAudio(id);
      await fetchTracks();
      Alert.alert('Success', 'Audio published');
    } catch (e: any) {
      Alert.alert('Error', 'Failed to publish');
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const renderItem = ({ item }: any) => {
    const badge = stateBadge(item.state);
    const isExpanded = expandedId === item.id;
    return (
      <TouchableOpacity
        style={s.item}
        onPress={() => setExpandedId(isExpanded ? null : item.id)}
        activeOpacity={0.7}
      >
        <View style={s.itemRow}>
          <View style={s.audioIcon}>
            <Ionicons name="musical-note" size={20} color={COLORS.accent} />
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={s.itemTitle} numberOfLines={1}>{item.name || item.title || 'Untitled'}</Text>
            <View style={s.itemMeta}>
              {item.reciter_name && <Text style={s.itemReciter}>{item.reciter_name}</Text>}
              <Text style={s.itemDuration}>{formatDuration(item.duration)}</Text>
              <View style={[s.badge, { backgroundColor: badge.bg }]}>
                <Text style={[s.badgeText, { color: badge.color }]}>{badge.label}</Text>
              </View>
            </View>
          </View>
          <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={18} color={COLORS.textTertiary} />
        </View>
        {isExpanded && item.state !== 'published' && (
          <View style={s.actions}>
            <TouchableOpacity style={s.publishBtn} onPress={() => handlePublish(item.id)}>
              <Ionicons name="checkmark-circle-outline" size={16} color={COLORS.background} />
              <Text style={s.publishBtnText}>Publish</Text>
            </TouchableOpacity>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderPicker = (
    open: boolean,
    setOpen: (v: boolean) => void,
    options: { label: string; value: string }[],
    current: string,
    onSelect: (v: string) => void,
    label: string,
  ) => (
    <>
      <Text style={s.label}>{label}</Text>
      <TouchableOpacity style={s.picker} onPress={() => setOpen(!open)}>
        <Text style={s.pickerText}>{options.find((o) => o.value === current)?.label || 'Select'}</Text>
        <Ionicons name="chevron-down" size={18} color={COLORS.textSecondary} />
      </TouchableOpacity>
      {open && (
        <View style={s.pickerDropdown}>
          {options.map((o) => (
            <TouchableOpacity
              key={o.value}
              style={s.pickerOption}
              onPress={() => { onSelect(o.value); setOpen(false); }}
            >
              <Text style={[s.pickerOptionText, current === o.value && { color: COLORS.primary, fontWeight: '600' }]}>
                {o.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </>
  );

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>Audio Management</Text>
        <View style={{ width: 24 }} />
      </View>

      <TouchableOpacity style={s.addBtn} onPress={() => setShowCreate(true)}>
        <Ionicons name="add-circle-outline" size={20} color={COLORS.background} />
        <Text style={s.addBtnText}>Add Audio</Text>
      </TouchableOpacity>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={tracks}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          ListEmptyComponent={<Text style={s.empty}>No audio tracks found</Text>}
        />
      )}

      {/* Create Modal */}
      <Modal visible={showCreate} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.container}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => setShowCreate(false)}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
            <Text style={s.headerTitle}>Add Audio Track</Text>
            <View style={{ width: 24 }} />
          </View>
          <ScrollView contentContainerStyle={s.form}>
            <Text style={s.label}>Name (English)</Text>
            <TextInput
              style={s.input}
              value={form.name}
              onChangeText={(v) => setForm({ ...form, name: v })}
              placeholder="Track name"
              placeholderTextColor={COLORS.textTertiary}
            />

            <Text style={s.label}>Name (Arabic)</Text>
            <TextInput
              style={[s.input, { textAlign: 'right' }]}
              value={form.name_ar}
              onChangeText={(v) => setForm({ ...form, name_ar: v })}
              placeholder="اسم المقطع"
              placeholderTextColor={COLORS.textTertiary}
            />

            {renderPicker(typePickerOpen, setTypePickerOpen, AUDIO_TYPES, form.audio_type,
              (v) => setForm({ ...form, audio_type: v }), 'Audio Type')}

            <Text style={s.label}>Reciter Name</Text>
            <TextInput
              style={s.input}
              value={form.reciter_name}
              onChangeText={(v) => setForm({ ...form, reciter_name: v })}
              placeholder="e.g. Sheikh Mishary"
              placeholderTextColor={COLORS.textTertiary}
            />

            <Text style={s.label}>Audio URL (CDN Link)</Text>
            <TextInput
              style={s.input}
              value={form.audio_url}
              onChangeText={(v) => setForm({ ...form, audio_url: v })}
              placeholder="https://cdn.example.com/audio.mp3"
              placeholderTextColor={COLORS.textTertiary}
              keyboardType="url"
              autoCapitalize="none"
            />

            <Text style={s.label}>Duration (seconds)</Text>
            <TextInput
              style={s.input}
              value={form.duration}
              onChangeText={(v) => setForm({ ...form, duration: v })}
              placeholder="e.g. 300"
              placeholderTextColor={COLORS.textTertiary}
              keyboardType="numeric"
            />

            {renderPicker(langPickerOpen, setLangPickerOpen, LANGUAGES, form.language,
              (v) => setForm({ ...form, language: v }), 'Language')}

            <TouchableOpacity style={s.submitBtn} onPress={handleCreate} disabled={creating}>
              {creating ? (
                <ActivityIndicator size="small" color={COLORS.background} />
              ) : (
                <Text style={s.submitBtnText}>Create Audio Track</Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  headerTitle: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  addBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: COLORS.accent,
    alignSelf: 'flex-start', marginLeft: 16, marginTop: 16, paddingHorizontal: 16,
    paddingVertical: 10, borderRadius: 10,
  },
  addBtnText: { fontSize: 14, fontWeight: '600', color: COLORS.background },
  list: { padding: 16, paddingBottom: 40 },
  item: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16,
    marginBottom: 12,
  },
  itemRow: { flexDirection: 'row', alignItems: 'center' },
  audioIcon: {
    width: 40, height: 40, borderRadius: 10, backgroundColor: COLORS.accent + '15',
    justifyContent: 'center', alignItems: 'center',
  },
  itemTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text, marginBottom: 4 },
  itemMeta: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  itemReciter: { fontSize: 12, color: COLORS.textSecondary },
  itemDuration: { fontSize: 12, color: COLORS.textTertiary },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  badgeText: { fontSize: 11, fontWeight: '600' },
  actions: { marginTop: 12, flexDirection: 'row', gap: 10 },
  publishBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: COLORS.primary,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8,
  },
  publishBtnText: { fontSize: 13, fontWeight: '600', color: COLORS.background },
  empty: { fontSize: 14, color: COLORS.textTertiary, textAlign: 'center', marginTop: 40 },
  form: { padding: 20, paddingBottom: 40 },
  label: { fontSize: 13, fontWeight: '600', color: COLORS.text, marginBottom: 6, marginTop: 16 },
  input: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 10, padding: 14,
    fontSize: 15, color: COLORS.text, borderWidth: 1, borderColor: COLORS.border,
  },
  picker: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 10, padding: 14,
    borderWidth: 1, borderColor: COLORS.border, flexDirection: 'row',
    justifyContent: 'space-between', alignItems: 'center',
  },
  pickerText: { fontSize: 15, color: COLORS.text },
  pickerDropdown: {
    backgroundColor: COLORS.background, borderRadius: 10, borderWidth: 1,
    borderColor: COLORS.border, marginTop: 4,
  },
  pickerOption: { padding: 12, borderBottomWidth: 1, borderBottomColor: COLORS.borderLight },
  pickerOptionText: { fontSize: 14, color: COLORS.text },
  submitBtn: {
    backgroundColor: COLORS.primary, borderRadius: 12, padding: 16,
    alignItems: 'center', marginTop: 24,
  },
  submitBtnText: { fontSize: 16, fontWeight: '600', color: COLORS.background },
});
