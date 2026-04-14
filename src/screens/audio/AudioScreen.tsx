import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import type { AudioPlayer } from 'expo-audio';
import { COLORS } from '../../config';
import { audioAPI, userAPI } from '../../api/client';
import { useAuthStore } from '../../contexts/AuthStore';

export default function AudioScreen() {
  const { t } = useTranslation();
  const { refreshStats } = useAuthStore();
  const [tracks, setTracks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [playingId, setPlayingId] = useState<number | null>(null);
  const playerRef = useRef<AudioPlayer | null>(null);
  const playStartRef = useRef<number | null>(null);

  useEffect(() => {
    setAudioModeAsync({ playsInSilentMode: true, shouldPlayInBackground: true }).catch(() => {});
    audioAPI.list()
      .then(res => {
        const data = res.data?.data || res.data;
        if (Array.isArray(data)) setTracks(data);
      })
      .catch(() => Alert.alert('Error', 'Failed to load audio. Please log in again.'))
      .finally(() => setLoading(false));

    return () => {
      logCurrentSession();
      playerRef.current?.remove();
    };
  }, []);

  const logCurrentSession = async () => {
    if (!playStartRef.current) return;
    const minutes = (Date.now() - playStartRef.current) / 60000;
    playStartRef.current = null;
    if (minutes < 0.1) return;
    try {
      await userAPI.logListening(parseFloat(minutes.toFixed(2)));
      await refreshStats();
    } catch {}
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const playTrack = async (track: any) => {
    try {
      // Stopping the current track
      if (playingId === track.id) {
        await logCurrentSession();
        playerRef.current?.pause();
        playerRef.current?.remove();
        playerRef.current = null;
        setPlayingId(null);
        return;
      }

      // Switching tracks
      if (playerRef.current) {
        await logCurrentSession();
        playerRef.current.pause();
        playerRef.current.remove();
        playerRef.current = null;
      }

      if (!track.audio_url) {
        Alert.alert('Audio Unavailable', 'No audio URL configured for this track.');
        return;
      }

      setPlayingId(track.id);
      playStartRef.current = Date.now();

      const player = createAudioPlayer({ uri: track.audio_url });
      playerRef.current = player;

      player.addListener('playbackStatusUpdate', async (status) => {
        if (status.didJustFinish) {
          await logCurrentSession();
          setPlayingId(null);
          player.remove();
          playerRef.current = null;
        }
      });

      player.play();
    } catch (e) {
      playStartRef.current = null;
      setPlayingId(null);
      Alert.alert('Playback Error', 'Could not play this audio track.');
    }
  };

  return (
    <SafeAreaView style={s.c}>
      <FlatList
        data={tracks}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={{ paddingBottom: 80 }}
        ListHeaderComponent={
          <>
            <Text style={s.title}>{t('tabs.audio')}</Text>
            {/* Summary banner showing track count */}
            <View style={s.banner}>
              <View style={s.bannerIconWrap}>
                <Ionicons name="musical-notes" size={22} color="#fff" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.bt}>{t('audio.recitations')}</Text>
                <Text style={s.bs}>
                  {tracks.length} {tracks.length === 1 ? 'track' : 'tracks'} available
                </Text>
              </View>
            </View>
            <Text style={s.sec}>{t('audio.recitations')}</Text>
          </>
        }
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 30 }} />
          ) : (
            <Text style={s.empty}>No audio tracks available</Text>
          )
        }
        renderItem={({ item }) => {
          const isPlaying = playingId === item.id;
          return (
            <TouchableOpacity style={s.item} onPress={() => playTrack(item)} activeOpacity={0.7}>
              <View style={[s.play, isPlaying && { backgroundColor: COLORS.primary }]}>
                <Ionicons name={isPlaying ? 'stop' : 'play'} size={20} color={isPlaying ? '#fff' : COLORS.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.itemTitle}>{item.title}</Text>
                <Text style={s.itemSub}>
                  {item.reciter || 'Reciter'} · {item.duration || formatDuration(item.duration_seconds)}
                  {isPlaying ? ' · Playing...' : ''}
                </Text>
              </View>
              {item.is_downloadable && !isPlaying && (
                <Ionicons name="download-outline" size={20} color={COLORS.textTertiary} />
              )}
            </TouchableOpacity>
          );
        }}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: '#fff' },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.text, paddingHorizontal: 24, paddingTop: 24 },
  banner: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.primary, marginHorizontal: 24, marginTop: 16, borderRadius: 14, padding: 16, gap: 12 },
  bannerIconWrap: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
  bt: { fontSize: 17, fontWeight: '600', color: '#fff' },
  bs: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 2 },
  sec: { fontSize: 17, fontWeight: '600', color: COLORS.text, paddingHorizontal: 24, marginTop: 24, marginBottom: 12 },
  item: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 24, paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: COLORS.borderLight },
  play: { width: 42, height: 42, borderRadius: 21, backgroundColor: COLORS.primaryLight, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  itemTitle: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  itemSub: { fontSize: 11, color: COLORS.textTertiary, marginTop: 2 },
  empty: { textAlign: 'center', color: COLORS.textTertiary, marginTop: 30, fontSize: 14 },
});
