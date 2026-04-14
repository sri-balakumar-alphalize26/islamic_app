import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, SafeAreaView,
  ActivityIndicator, Alert, TextInput, Modal, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { adminAPI } from '../../api/client';

const ROLES = [
  { label: 'User', value: 'user' },
  { label: 'Special', value: 'special' },
  { label: 'Admin', value: 'admin' },
];

const roleBadge = (role: string) => {
  switch (role) {
    case 'admin': return { bg: COLORS.error + '20', color: COLORS.error, label: 'Admin' };
    case 'special': return { bg: COLORS.accent + '20', color: COLORS.accent, label: 'Special' };
    default: return { bg: COLORS.info + '20', color: COLORS.info, label: 'User' };
  }
};

export default function UserManagementScreen({ navigation }: any) {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);

  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [updatingRole, setUpdatingRole] = useState(false);

  const fetchUsers = useCallback(async (p = 1, searchTerm = search, append = false) => {
    try {
      const res = await adminAPI.listUsers(p, searchTerm);
      const data = res.data?.data || [];
      const pagination = res.data?.pagination;
      if (append) {
        setUsers((prev) => [...prev, ...data]);
      } else {
        setUsers(Array.isArray(data) ? data : []);
      }
      if (pagination) {
        setTotalPages(Math.ceil(pagination.total / pagination.limit));
      }
    } catch (e: any) {
      Alert.alert('Error', 'Failed to load users');
    }
  }, [search]);

  useEffect(() => {
    setPage(1);
    fetchUsers(1, search).finally(() => setLoading(false));
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    setPage(1);
    await fetchUsers(1, search);
    setRefreshing(false);
  };

  const handleSearch = () => {
    setLoading(true);
    setPage(1);
    fetchUsers(1, search).finally(() => setLoading(false));
  };

  const handleLoadMore = async () => {
    if (loadingMore || page >= totalPages) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    setPage(nextPage);
    await fetchUsers(nextPage, search, true);
    setLoadingMore(false);
  };

  const handleChangeRole = async (role: string) => {
    if (!selectedUser) return;
    setUpdatingRole(true);
    try {
      await adminAPI.updateUserRole(selectedUser.id, role);
      setRoleModalOpen(false);
      setSelectedUser(null);
      await fetchUsers(1, search);
      setPage(1);
      Alert.alert('Success', `Role updated to ${role}`);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.error || 'Failed to update role');
    } finally {
      setUpdatingRole(false);
    }
  };

  const renderItem = ({ item }: any) => {
    const badge = roleBadge(item.app_role || item.role || 'user');
    return (
      <TouchableOpacity
        style={s.item}
        onPress={() => { setSelectedUser(item); setRoleModalOpen(true); }}
        activeOpacity={0.7}
      >
        <View style={s.avatar}>
          <Text style={s.avatarText}>
            {(item.display_name || item.name || 'U').charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={{ flex: 1, marginLeft: 12 }}>
          <Text style={s.itemName} numberOfLines={1}>{item.display_name || item.name || 'Unknown'}</Text>
          <Text style={s.itemEmail} numberOfLines={1}>
            {item.email || item.phone_number || item.phone || '-'}
          </Text>
          <View style={s.itemMeta}>
            <View style={[s.badge, { backgroundColor: badge.bg }]}>
              <Text style={[s.badgeText, { color: badge.color }]}>{badge.label}</Text>
            </View>
            {item.is_premium && (
              <View style={[s.badge, { backgroundColor: COLORS.secondary + '20' }]}>
                <Text style={[s.badgeText, { color: COLORS.secondary }]}>Premium</Text>
              </View>
            )}
            {item.last_active && (
              <Text style={s.lastActive}>Active {new Date(item.last_active).toLocaleDateString()}</Text>
            )}
          </View>
        </View>
        <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>User Management</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Search */}
      <View style={s.searchRow}>
        <View style={s.searchBox}>
          <Ionicons name="search" size={18} color={COLORS.textTertiary} />
          <TextInput
            style={s.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="Search by name, email, phone..."
            placeholderTextColor={COLORS.textTertiary}
            returnKeyType="search"
            onSubmitEditing={handleSearch}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => { setSearch(''); fetchUsers(1, ''); }}>
              <Ionicons name="close-circle" size={18} color={COLORS.textTertiary} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={users}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.3}
          ListEmptyComponent={<Text style={s.empty}>No users found</Text>}
          ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={COLORS.primary} style={{ marginVertical: 16 }} /> : null}
        />
      )}

      {/* Role Modal */}
      <Modal visible={roleModalOpen} transparent animationType="fade">
        <TouchableOpacity
          style={s.modalOverlay}
          activeOpacity={1}
          onPress={() => { setRoleModalOpen(false); setSelectedUser(null); }}
        >
          <View style={s.modalSheet}>
            <View style={s.modalHandle} />
            <Text style={s.modalTitle}>
              {selectedUser?.display_name || selectedUser?.name || 'User'}
            </Text>
            <Text style={s.modalSubtitle}>Change Role</Text>

            {ROLES.map((r) => {
              const isCurrent = (selectedUser?.app_role || selectedUser?.role || 'user') === r.value;
              return (
                <TouchableOpacity
                  key={r.value}
                  style={[s.roleOption, isCurrent && s.roleOptionActive]}
                  onPress={() => handleChangeRole(r.value)}
                  disabled={updatingRole}
                >
                  <Text style={[s.roleOptionText, isCurrent && { color: COLORS.primary, fontWeight: '700' }]}>
                    {r.label}
                  </Text>
                  {isCurrent && <Ionicons name="checkmark" size={20} color={COLORS.primary} />}
                </TouchableOpacity>
              );
            })}

            {updatingRole && <ActivityIndicator size="small" color={COLORS.primary} style={{ marginTop: 12 }} />}

            <TouchableOpacity
              style={s.cancelBtn}
              onPress={() => { setRoleModalOpen(false); setSelectedUser(null); }}
            >
              <Text style={s.cancelBtnText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
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
  searchRow: { paddingHorizontal: 16, paddingTop: 12 },
  searchBox: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.backgroundSecondary,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, gap: 8,
    borderWidth: 1, borderColor: COLORS.border,
  },
  searchInput: { flex: 1, fontSize: 15, color: COLORS.text },
  list: { padding: 16, paddingBottom: 40 },
  item: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 14,
    marginBottom: 10,
  },
  avatar: {
    width: 42, height: 42, borderRadius: 21, backgroundColor: COLORS.primary + '20',
    justifyContent: 'center', alignItems: 'center',
  },
  avatarText: { fontSize: 17, fontWeight: '700', color: COLORS.primary },
  itemName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  itemEmail: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  itemMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  badgeText: { fontSize: 11, fontWeight: '600' },
  lastActive: { fontSize: 11, color: COLORS.textTertiary },
  empty: { fontSize: 14, color: COLORS.textTertiary, textAlign: 'center', marginTop: 40 },

  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: COLORS.background, borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24, paddingBottom: 40,
  },
  modalHandle: {
    width: 36, height: 4, borderRadius: 2, backgroundColor: COLORS.border,
    alignSelf: 'center', marginBottom: 16,
  },
  modalTitle: { fontSize: 17, fontWeight: '700', color: COLORS.text, textAlign: 'center' },
  modalSubtitle: { fontSize: 13, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 20 },
  roleOption: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 16, borderRadius: 12, backgroundColor: COLORS.backgroundSecondary,
    marginBottom: 8,
  },
  roleOptionActive: { borderWidth: 1.5, borderColor: COLORS.primary },
  roleOptionText: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  cancelBtn: {
    marginTop: 12, padding: 14, borderRadius: 12, alignItems: 'center',
    backgroundColor: COLORS.backgroundSecondary,
  },
  cancelBtnText: { fontSize: 15, fontWeight: '600', color: COLORS.textSecondary },
});
