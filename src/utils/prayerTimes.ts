// Islamic Prayer Time Calculation (Muslim World League method)
// Pure JS — no external dependencies needed

const toRad = (d: number) => (d * Math.PI) / 180;
const toDeg = (r: number) => (r * 180) / Math.PI;
const fixAngle = (a: number) => a - 360 * Math.floor(a / 360);
const fixHour = (a: number) => a - 24 * Math.floor(a / 24);

function julianDay(date: Date): number {
  let y = date.getFullYear();
  let m = date.getMonth() + 1;
  const d = date.getDate();
  if (m <= 2) { y -= 1; m += 12; }
  const A = Math.floor(y / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
}

function sunPosition(jd: number) {
  const D = jd - 2451545.0;
  const g = fixAngle(357.529 + 0.98560028 * D);
  const q = fixAngle(280.459 + 0.98564736 * D);
  const L = fixAngle(q + 1.915 * Math.sin(toRad(g)) + 0.02 * Math.sin(toRad(2 * g)));
  const e = 23.439 - 0.00000036 * D;
  const RA = toDeg(Math.atan2(Math.cos(toRad(e)) * Math.sin(toRad(L)), Math.cos(toRad(L)))) / 15;
  const decl = toDeg(Math.asin(Math.sin(toRad(e)) * Math.sin(toRad(L))));
  const eqT = q / 15 - fixHour(RA);
  return { decl, eqT };
}

function midDay(jd: number, lng: number, tz: number): number {
  const { eqT } = sunPosition(jd);
  return fixHour(12 - eqT - lng / 15 + tz);
}

function sunAngleTime(jd: number, angle: number, lat: number, lng: number, tz: number, afterNoon: boolean): number {
  const { decl } = sunPosition(jd);
  const noon = midDay(jd, lng, tz);
  const cosVal =
    (-Math.sin(toRad(angle)) - Math.sin(toRad(decl)) * Math.sin(toRad(lat))) /
    (Math.cos(toRad(decl)) * Math.cos(toRad(lat)));
  if (cosVal < -1 || cosVal > 1) return NaN;
  const t = (1 / 15) * toDeg(Math.acos(cosVal));
  return noon + (afterNoon ? t : -t);
}

function asrTime(jd: number, shadowFactor: number, lat: number, lng: number, tz: number): number {
  const { decl } = sunPosition(jd);
  const noon = midDay(jd, lng, tz);
  const angle = -toDeg(Math.atan(1 / (shadowFactor + Math.tan(toRad(Math.abs(lat - decl))))));
  return sunAngleTime(jd, angle, lat, lng, tz, true);
}

function hoursToStr(h: number): string {
  if (isNaN(h)) return '--:--';
  const totalMins = Math.round(h * 60);
  const hours = Math.floor(totalMins / 60) % 24;
  const mins = totalMins % 60;
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const h12 = hours % 12 || 12;
  return `${h12}:${mins.toString().padStart(2, '0')} ${ampm}`;
}

export interface PrayerTimes {
  Fajr: string;
  Sunrise: string;
  Dhuhr: string;
  Asr: string;
  Maghrib: string;
  Isha: string;
}

export function calculatePrayerTimes(lat: number, lng: number, date: Date = new Date()): PrayerTimes {
  const tz = -date.getTimezoneOffset() / 60;
  const jd = julianDay(date);
  return {
    Fajr: hoursToStr(sunAngleTime(jd, 18, lat, lng, tz, false)),      // MWL: 18°
    Sunrise: hoursToStr(sunAngleTime(jd, 0.833, lat, lng, tz, false)),
    Dhuhr: hoursToStr(midDay(jd, lng, tz)),
    Asr: hoursToStr(asrTime(jd, 1, lat, lng, tz)),                    // Shafi shadow=1
    Maghrib: hoursToStr(sunAngleTime(jd, 0.833, lat, lng, tz, true)),
    Isha: hoursToStr(sunAngleTime(jd, 17, lat, lng, tz, true)),        // MWL: 17°
  };
}

export interface NextPrayer {
  name: string;
  time: string;
  minutesLeft: number;
}

function parseTimeToMins(timeStr: string): number {
  const [t, ampm] = timeStr.split(' ');
  const [hStr, mStr] = t.split(':');
  let h = parseInt(hStr, 10);
  const m = parseInt(mStr, 10);
  if (ampm === 'PM' && h !== 12) h += 12;
  if (ampm === 'AM' && h === 12) h = 0;
  return h * 60 + m;
}

export function getNextPrayer(times: PrayerTimes, now: Date = new Date()): NextPrayer {
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const prayers: (keyof PrayerTimes)[] = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
  for (const name of prayers) {
    const prayerMins = parseTimeToMins(times[name]);
    if (prayerMins > nowMins) {
      return { name, time: times[name], minutesLeft: prayerMins - nowMins };
    }
  }
  // All done — Fajr tomorrow
  const fajrMins = parseTimeToMins(times.Fajr);
  return { name: 'Fajr', time: times.Fajr, minutesLeft: 24 * 60 - nowMins + fajrMins };
}

export function formatMinutesLeft(mins: number): string {
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

// ── Qibla direction (bearing to Kaaba from any location) ───────────────────
const KAABA_LAT = 21.4225;
const KAABA_LNG = 39.8262;

/**
 * Returns the Qibla bearing in degrees (0–360, clockwise from true north).
 */
export function calculateQibla(lat: number, lng: number): number {
  const phiK = toRad(KAABA_LAT);
  const lambdaK = toRad(KAABA_LNG);
  const phi = toRad(lat);
  const lambda = toRad(lng);
  const bearing = toDeg(
    Math.atan2(
      Math.sin(lambdaK - lambda),
      Math.cos(phi) * Math.tan(phiK) - Math.sin(phi) * Math.cos(lambdaK - lambda),
    ),
  );
  return (bearing + 360) % 360;
}

export const PRESET_CITIES = [
  { name: 'Mecca', lat: 21.3891, lng: 39.8579 },
  { name: 'Medina', lat: 24.5247, lng: 39.5692 },
  { name: 'Cairo', lat: 30.0444, lng: 31.2357 },
  { name: 'Istanbul', lat: 41.0082, lng: 28.9784 },
  { name: 'Dubai', lat: 25.2048, lng: 55.2708 },
  { name: 'Karachi', lat: 24.8607, lng: 67.0011 },
  { name: 'Dhaka', lat: 23.8103, lng: 90.4125 },
  { name: 'Kuala Lumpur', lat: 3.139, lng: 101.6869 },
  { name: 'Jakarta', lat: -6.2088, lng: 106.8456 },
  { name: 'Riyadh', lat: 24.7136, lng: 46.6753 },
  { name: 'London', lat: 51.5074, lng: -0.1278 },
  { name: 'Paris', lat: 48.8566, lng: 2.3522 },
  { name: 'New York', lat: 40.7128, lng: -74.006 },
  { name: 'Toronto', lat: 43.6511, lng: -79.3836 },
  { name: 'Lagos', lat: 6.5244, lng: 3.3792 },
  { name: 'Nairobi', lat: -1.2921, lng: 36.8219 },
];
