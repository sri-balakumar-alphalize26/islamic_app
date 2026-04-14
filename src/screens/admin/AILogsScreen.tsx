import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, SafeAreaView,
  ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../config';
import { aiAPI } from '../../api/client';

export default function AILogsScreen({ navigation }: any) {
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const fetchConversations = useCallback(async (p = 1, append = false) => {
    try {
      const res = await aiAPI.getConversations(p);
      const data = res.data?.data || [];
      if (append) {
        setConversations((prev) => [...prev, ...data]);
      } else {
        setConversations(Array.isArray(data) ? data : []);
      }
      if (data.length < 20) setHasMore(false);
    } catch (e: any) {
      Alert.alert('Error', 'Failed to load AI logs');
    }
  }, []);

  useEffect(() => {
    fetchConversations(1).finally(() => setLoading(false));
  }, [fetchConversations]);

  const onRefresh = async () => {
    setRefreshing(true);
    setPage(1);
    setHasMore(true);
    await fetchConversations(1);
    setRefreshing(false);
  };

  const handleLoadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    setPage(nextPage);
    await fetchConversations(nextPage, true);
    setLoadingMore(false);
  };

  const renderItem = ({ item }: any) => {
    const date = item.created_at || item.create_date;
    return (
      <View style={s.item}>
        <View style={s.itemHeader}>
          <View style={s.aiIcon}>
            <Ionicons name="sparkles" size={16} color={COLORS.accent} />
          </View>
          <View style={{ flex: 1, marginLeft: 10 }}>
            <Text style={s.itemTitle} numberOfLines={2}>{item.title || 'Untitled conversation'}</Text>
            {item.topic && <Text style={s.itemTopic}>{item.topic}</Text>}
          </View>
        </View>
        <View style={s.itemFooter}>
          {item.user_name && (
            <View style={s.metaItem}>
              <Ionicons name="person-outline" size={13} color={COLORS.textTertiary} />
              <Text style={s.metaText}>{item.user_name}</Text>
            </View>
          )}
          {date && (
            <View style={s.metaItem}>
              <Ionicons name="time-outline" size={13} color={COLORS.textTertiary} />
              <Text style={s.metaText}>{new Date(date).toLocaleString()}</Text>
            </View>
          )}
          {item.message_count != null && (
            <View style={s.metaItem}>
              <Ionicons name="chatbubble-outline" size={13} color={COLORS.textTertiary} />
              <Text style={s.metaText}>{item.message_count} msgs</Text>
            </View>
          )}
          {item.tokens_used != null && (
            <View style={s.metaItem}>
              <Ionicons name="flash-outline" size={13} color={COLORS.textTertiary} />
              <Text style={s.metaText}>{item.tokens_used} tokens</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>AI Conversation Logs</Text>
        <View style={{ width: 24 }} />
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={conversations}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={s.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.3}
          ListEmptyComponent={<Text style={s.empty}>No AI conversations found</Text>}
          ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={COLORS.primary} style={{ marginVertical: 16 }} /> : null}
        />
      )}
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
  list: { padding: 16, paddingBottom: 40 },
  item: {
    backgroundColor: COLORS.backgroundSecondary, borderRadius: 14, padding: 16,
    marginBottom: 12,
  },
  itemHeader: { flexDirection: 'row', alignItems: 'flex-start' },
  aiIcon: {
    width: 32, height: 32, borderRadius: 8, backgroundColor: COLORS.accent + '15',
    justifyContent: 'center', alignItems: 'center', marginTop: 2,
  },
  itemTitle: { fontSize: 14, fontWeight: '600', color: COLORS.text, lineHeight: 20 },
  itemTopic: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  itemFooter: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 10,
    paddingTop: 10, borderTopWidth: 1, borderTopColor: COLORS.borderLight,
  },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontSize: 11, color: COLORS.textTertiary },
  empty: { fontSize: 14, color: COLORS.textTertiary, textAlign: 'center', marginTop: 40 },
});
