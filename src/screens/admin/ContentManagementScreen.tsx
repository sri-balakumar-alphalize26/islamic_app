import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, SafeAreaView,
  ActivityIndicator, Alert, TextInput, Modal, ScrollView, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { adminAPI, contentAPI } from '../../api/client';

const CONTENT_TYPES = [
  { label: 'Article', value: 'article' },
  { label: 'Daily Wisdom', value: 'daily_wisdom' },
  { label: 'Hadith', value: 'hadith' },
  { label: 'Dua', value: 'dua' },
  { label: 'Reminder', value: 'reminder' },
];

const stateBadge = (state: string) => {
  switch (state) {
    case 'published': return { bg: COLORS.success + '20', color: COLORS.success, label: 'Published' };
    case 'draft': return { bg: COLORS.warning + '20', color: COLORS.warning, label: 'Draft' };
    case 'archived': return { bg: COLORS.textTertiary + '20', color: COLORS.textTertiary, label: 'Archived' };
    default: return { bg: COLORS.border, color: COLORS.textSecondary, label: state };
  }
};

export default function ContentManagementScreen({ navigation }: any) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [form, setForm] = useState({
    title_en: '', content_type: 'article', body_en: '', arabic_text: '', reference: '',
  });
  const [typePickerOpen, setTypePickerOpen] = useState(false);

  const fetchContent = useCallback(async () => {
    try {
      const res = await adminAPI.listContent();
      const data = res.data?.data || res.data || [];
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      Alert.alert('Error', 'Failed to load content');
    }
  }, []);

  useEffect(() => {
    fetchContent().finally(() => setLoading(false));
  }, [fetchContent]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchContent();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!form.title_en.trim()) {
      Alert.alert('Validation', 'Title is required');
      return;
    }
    setCreating(true);
    try {
      await adminAPI.createContent(form);
      setShowCreate(false);
      setForm({ title_en: '', content_type: 'article', body_en: '', arabic_text: '', reference: '' });
      await fetchContent();
      Alert.alert('Success', 'Content created');
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.error || 'Failed to create content');
    } finally {
      setCreating(false);
    }
  };

  const handlePublish = async (id: number) => {
    try {
      await adminAPI.publishContent(id);
      await fetchContent();
      Alert.alert('Success', 'Content published');
    } catch (e: any) {
      Alert.alert('Error', 'Failed to publish');
    }
  };

  const renderItem = ({ item }: any) => {
    const badge = stateBadge(item.state || 'draft');
    const isExpanded = expandedId === item.id;
    return (
      <TouchableOpacity
        style={s.item}
        onPress={() => setExpandedId(isExpanded ? null : item.id)}
        activeOpacity={0.7}
      >
        <View style={s.itemRow}>
          <View style={{ flex: 1 }}>
            <Text style={s.itemTitle} numberOfLines={1}>{item.title || item.name || 'Untitled'}</Text>
            <View style={s.itemMeta}>
              <Text style={s.itemType}>{item.content_type || '-'}</Text>
              <View style={[s.badge, { backgroundColor: badge.bg }]}>
                <Text style={[s.badgeText, { color: badge.color }]}>{badge.label}</Text>
              </View>
            </View>
            {item.create_date && (
              <Text style={s.itemDate}>{new Date(item.create_date || item.created_at).toLocaleDateString()}</Text>
            )}
          </View>
          <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={18} color={COLORS.textTertiary} />
        </View>
        {isExpanded && (
          <View style={s.actions}>
            {item.state !== 'published' && (
              <TouchableOpacity style={s.publishBtn} onPress={() => handlePublish(item.id)}>
                <Ionicons name="checkmark-circle-outline" size={16} color={COLORS.background} />
                <Text style={s.publishBtnText}>Publish</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>Content Management</Text>
        <View style={{ width: 24 }} />
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          ListEmptyComponent={<Text style={s.empty}>No content found</Text>}
        />
      )}

      {/* FAB */}
      <TouchableOpacity style={s.fab} onPress={() => setShowCreate(true)}>
        <Ionicons name="add" size={28} color={COLORS.background} />
      </TouchableOpacity>

      {/* Create Modal */}
      <Modal visible={showCreate} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.container}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => setShowCreate(false)}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
            <Text style={s.headerTitle}>New Content</Text>
            <View style={{ width: 24 }} />
          </View>
          <ScrollView contentContainerStyle={s.form}>
            <Text style={s.label}>Title (English)</Text>
            <TextInput
              style={s.input}
              value={form.title_en}
              onChangeText={(v) => setForm({ ...form, title_en: v })}
              placeholder="Enter title"
              placeholderTextColor={COLORS.textTertiary}
            />

            <Text style={s.label}>Content Type</Text>
            <TouchableOpacity style={s.picker} onPress={() => setTypePickerOpen(!typePickerOpen)}>
              <Text style={s.pickerText}>
                {CONTENT_TYPES.find((t) => t.value === form.content_type)?.label || 'Select'}
              </Text>
              <Ionicons name="chevron-down" size={18} color={COLORS.textSecondary} />
            </TouchableOpacity>
            {typePickerOpen && (
              <View style={s.pickerDropdown}>
                {CONTENT_TYPES.map((t) => (
                  <TouchableOpacity
                    key={t.value}
                    style={s.pickerOption}
                    onPress={() => { setForm({ ...form, content_type: t.value }); setTypePickerOpen(false); }}
                  >
                    <Text style={[s.pickerOptionText, form.content_type === t.value && { color: COLORS.primary, fontWeight: '600' }]}>
                      {t.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            <Text style={s.label}>Body (English)</Text>
            <TextInput
              style={[s.input, s.textArea]}
              value={form.body_en}
              onChangeText={(v) => setForm({ ...form, body_en: v })}
              placeholder="Enter body text"
              placeholderTextColor={COLORS.textTertiary}
              multiline
              textAlignVertical="top"
            />

            <Text style={s.label}>Arabic Text</Text>
            <TextInput
              style={[s.input, { textAlign: 'right' }]}
              value={form.arabic_text}
              onChangeText={(v) => setForm({ ...form, arabic_text: v })}
              placeholder="النص العربي"
              placeholderTextColor={COLORS.textTertiary}
            />

            <Text style={s.label}>Reference</Text>
            <TextInput
              style={s.input}
              value={form.reference}
              onChangeText={(v) => setForm({ ...form, reference: v })}
              placeholder="e.g. Sahih Bukhari 1234"
              placeholderTextColor={COLORS.textTertiary}
            />

            <TouchableOpacity style={s.submitBtn} onPress={handleCreate} disabled={creating}>
              {creating ? (
                <ActivityIndicator size="small" color={COLORS.background} />
              ) : (
                <Text style={s.submitBtnText}>Create Content</Text>
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
  list: { padding: 16, paddingBottom: 100 },
  item: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16,
    marginBottom: 12,
  },
  itemRow: { flexDirection: 'row', alignItems: 'center' },
  itemTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text, marginBottom: 6 },
  itemMeta: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  itemType: { fontSize: 12, color: COLORS.textSecondary, textTransform: 'capitalize' },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  badgeText: { fontSize: 11, fontWeight: '600' },
  itemDate: { fontSize: 11, color: COLORS.textTertiary, marginTop: 4 },
  actions: { marginTop: 12, flexDirection: 'row', gap: 10 },
  publishBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: COLORS.primary,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8,
  },
  publishBtnText: { fontSize: 13, fontWeight: '600', color: COLORS.background },
  empty: { fontSize: 14, color: COLORS.textTertiary, textAlign: 'center', marginTop: 40 },
  fab: {
    position: 'absolute', bottom: 30, right: 20, width: 56, height: 56,
    borderRadius: 28, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.2, shadowRadius: 4,
    elevation: 6,
  },
  form: { padding: 20, paddingBottom: 40 },
  label: { fontSize: 13, fontWeight: '600', color: COLORS.text, marginBottom: 6, marginTop: 16 },
  input: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 10, padding: 14,
    fontSize: 15, color: COLORS.text, borderWidth: 1, borderColor: COLORS.border,
  },
  textArea: { minHeight: 120 },
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
