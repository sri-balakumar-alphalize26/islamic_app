import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Linking, TouchableOpacity } from 'react-native';
import { Magnetometer } from 'expo-sensors';
import { Ionicons } from '@expo/vector-icons';
import { calculateQibla } from '../utils/prayerTimes';

interface Props {
  latitude: number | null;
  longitude: number | null;
  locationDenied?: boolean;
}

const PRIMARY = '#0E7C61';
const GOLD = '#C8A951';
const RING_SIZE = 200;

export default function QiblaWidget({ latitude, longitude, locationDenied }: Props) {
  const [heading, setHeading] = useState(0);
  const [sensorAvailable, setSensorAvailable] = useState(true);

  // Animated values for smooth rotation
  const compassAnim = useRef(new Animated.Value(0)).current; // compass ring rotation
  const needleAnim = useRef(new Animated.Value(0)).current;  // kaaba needle rotation

  const qiblaAngle = latitude != null && longitude != null
    ? calculateQibla(latitude, longitude)
    : null;

  useEffect(() => {
    let sub: any = null;

    (async () => {
      const available = await Magnetometer.isAvailableAsync();
      if (!available) { setSensorAvailable(false); return; }

      Magnetometer.setUpdateInterval(150);
      sub = Magnetometer.addListener(({ x, y }) => {
        let angle = Math.atan2(y, x) * (180 / Math.PI);
        angle = (90 - angle + 360) % 360;
        setHeading(angle);
      });
    })();

    return () => { sub?.remove(); };
  }, []);

  // Animate compass ring (rotates opposite to heading so N stays correct)
  useEffect(() => {
    Animated.timing(compassAnim, {
      toValue: -heading,
      duration: 200,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }).start();
  }, [heading]);

  // Animate Kaaba needle (shows qibla relative to current heading)
  useEffect(() => {
    if (qiblaAngle == null) return;
    const relative = qiblaAngle - heading;
    Animated.timing(needleAnim, {
      toValue: relative,
      duration: 200,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }).start();
  }, [heading, qiblaAngle]);

  // Check if user is facing Qibla (within ±5°)
  const diff = qiblaAngle != null ? Math.abs(((qiblaAngle - heading) % 360 + 360) % 360) : 999;
  const isFacingQibla = diff < 5 || diff > 355;

  const compassRotation = compassAnim.interpolate({
    inputRange: [-360, 360],
    outputRange: ['-360deg', '360deg'],
  });
  const needleRotation = needleAnim.interpolate({
    inputRange: [-360, 360],
    outputRange: ['-360deg', '360deg'],
  });

  // ── No location ──
  if (locationDenied || (latitude == null && longitude == null)) {
    return (
      <View style={s.card}>
        <Ionicons name="compass-outline" size={24} color="#AAA" />
        <Text style={s.unavailTxt}>Enable location to find Qibla direction</Text>
        <TouchableOpacity onPress={() => Linking.openSettings()}>
          <Text style={s.linkTxt}>Open Settings</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ── No magnetometer ──
  if (!sensorAvailable) {
    return (
      <View style={s.card}>
        <Ionicons name="compass-outline" size={24} color="#AAA" />
        <Text style={s.unavailTxt}>Compass not available on this device</Text>
        {qiblaAngle != null && (
          <Text style={s.fallbackTxt}>Qibla is at {Math.round(qiblaAngle)}° from North</Text>
        )}
      </View>
    );
  }

  return (
    <View style={s.card}>
      <Text style={s.title}>Qibla Direction</Text>

      <View style={s.compassWrap}>
        {/* Outer ring with cardinals — rotates with phone */}
        <Animated.View style={[s.compassRing, isFacingQibla && s.compassRingActive, { transform: [{ rotate: compassRotation }] }]}>
          <Text style={[s.cardinal, s.cardN]}>N</Text>
          <Text style={[s.cardinal, s.cardE]}>E</Text>
          <Text style={[s.cardinal, s.cardS]}>S</Text>
          <Text style={[s.cardinal, s.cardW]}>W</Text>

          {/* Tick marks for visual richness */}
          {[0, 45, 90, 135, 180, 225, 270, 315].map(deg => (
            <View key={deg} style={[s.tick, { transform: [{ rotate: `${deg}deg` }, { translateY: -RING_SIZE / 2 + 2 }] }]} />
          ))}
        </Animated.View>

        {/* Kaaba needle — stays fixed at qibla direction relative to heading */}
        <Animated.View style={[s.needleContainer, { transform: [{ rotate: needleRotation }] }]}>
          <View style={s.needleArm}>
            <Text style={s.kaabaIcon}>🕋</Text>
            <View style={s.needleLine} />
          </View>
        </Animated.View>

        {/* Fixed top indicator triangle — "you are pointing this way" */}
        <View style={s.topIndicator}>
          <View style={s.triangle} />
        </View>

        {/* Center dot */}
        <View style={[s.centerDot, isFacingQibla && s.centerDotActive]} />
      </View>

      {/* Status */}
      {isFacingQibla ? (
        <View style={s.alignedRow}>
          <Ionicons name="checkmark-circle" size={20} color={PRIMARY} />
          <Text style={s.alignedTxt}>You're facing Qibla!</Text>
        </View>
      ) : (
        <>
          <Text style={s.degreeText}>
            {qiblaAngle != null ? `${Math.round(qiblaAngle)}°` : '…'} from North
          </Text>
          <Text style={s.hintText}>Rotate until 🕋 reaches the top marker</Text>
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    marginHorizontal: 24, marginTop: 16,
    backgroundColor: '#F8F9FA', borderRadius: 16,
    padding: 20, alignItems: 'center',
    borderWidth: 1, borderColor: '#E8E8E8',
  },
  title: { fontSize: 15, fontWeight: '600', color: '#333', marginBottom: 14 },

  compassWrap: {
    width: RING_SIZE + 20, height: RING_SIZE + 20,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 12,
  },

  compassRing: {
    width: RING_SIZE, height: RING_SIZE, borderRadius: RING_SIZE / 2,
    borderWidth: 3, borderColor: '#DDD',
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#fff',
  },
  compassRingActive: {
    borderColor: PRIMARY, borderWidth: 4,
  },

  cardinal: { position: 'absolute', fontSize: 13, fontWeight: '700', color: '#999' },
  cardN: { top: 10, alignSelf: 'center', color: '#E53935', fontSize: 15, fontWeight: '800' },
  cardE: { right: 12, top: RING_SIZE / 2 - 9 },
  cardS: { bottom: 10, alignSelf: 'center' },
  cardW: { left: 12, top: RING_SIZE / 2 - 9 },

  tick: {
    position: 'absolute', width: 2, height: 8,
    backgroundColor: '#CCC', borderRadius: 1,
    alignSelf: 'center',
  },

  needleContainer: {
    position: 'absolute',
    width: RING_SIZE, height: RING_SIZE,
    alignItems: 'center', justifyContent: 'flex-start',
  },
  needleArm: {
    alignItems: 'center', paddingTop: 14,
  },
  kaabaIcon: { fontSize: 28 },
  needleLine: {
    width: 3, height: 50,
    backgroundColor: GOLD, borderRadius: 2, marginTop: 2,
  },

  // Fixed triangle at top of compass (always points "up" = phone direction)
  topIndicator: {
    position: 'absolute', top: -2, alignSelf: 'center',
  },
  triangle: {
    width: 0, height: 0,
    borderLeftWidth: 8, borderRightWidth: 8, borderBottomWidth: 12,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    borderBottomColor: PRIMARY,
  },

  centerDot: {
    position: 'absolute',
    width: 12, height: 12, borderRadius: 6,
    backgroundColor: '#CCC',
  },
  centerDotActive: { backgroundColor: PRIMARY },

  alignedRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: PRIMARY + '15', paddingHorizontal: 16, paddingVertical: 10,
    borderRadius: 10,
  },
  alignedTxt: { fontSize: 16, fontWeight: '700', color: PRIMARY },

  degreeText: { fontSize: 18, fontWeight: '700', color: '#333', marginTop: 4 },
  hintText: { fontSize: 12, color: '#999', marginTop: 4 },

  unavailTxt: { fontSize: 14, color: '#777', marginTop: 8, textAlign: 'center' },
  linkTxt: { fontSize: 14, color: PRIMARY, fontWeight: '600', marginTop: 8 },
  fallbackTxt: { fontSize: 15, fontWeight: '600', color: '#333', marginTop: 8 },
});
