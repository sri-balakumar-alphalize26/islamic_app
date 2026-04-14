#!/usr/bin/env python3
"""
Populate Quran + Adhkar translations directly via Odoo XML-RPC.
Run from command line: python populate_translations.py

Quran: fetches from Al-Quran Cloud API (free, no API key).
Adhkar: hardcoded scholarly translations from Hisn al-Muslim.
"""

import json
import urllib.request
import xmlrpc.client

# ── CONFIG ──────────────────────────────────────────────────────────────────
ODOO_URL = 'http://192.168.255.246:8069'
ODOO_DB = 'odookra'
ODOO_USER = 'aghniesh@gmail.com'
ODOO_PASS = '1234'

QURAN_EDITIONS = {
    'fr': 'fr.hamidullah',
    'tr': 'tr.diyanet',
    'hi': 'hi.hindi',
}


def connect():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    if not uid:
        # Try other common passwords
        for pw in ['admin', '1234', '12345678', 'admin123', '1']:
            uid = common.authenticate(ODOO_DB, ODOO_USER, pw, {})
            if uid:
                print(f'  Authenticated with password: {pw}')
                break
    if not uid:
        raise Exception('Cannot authenticate to Odoo. Check ODOO_USER/ODOO_PASS in the script.')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    print(f'Connected to Odoo as uid={uid}')
    return uid, models


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'IslamicApp/1.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode('utf-8'))


def call(models, uid, model, method, *args, **kwargs):
    return models.execute_kw(ODOO_DB, uid, ODOO_PASS, model, method, *args, **kwargs)


def populate_quran(uid, models):
    print('\n=== QURAN TRANSLATIONS ===')

    # Get all surahs
    surahs = call(models, uid, 'islamic.surah', 'search_read',
                  [[]], {'fields': ['id', 'number', 'name']})
    surah_map = {s['number']: s['id'] for s in surahs}
    print(f'Found {len(surahs)} surahs in database')

    for lang, edition in QURAN_EDITIONS.items():
        field = f'translation_{lang}'
        print(f'\n--- {lang.upper()} ({edition}) ---')
        try:
            url = f'https://api.alquran.cloud/v1/quran/{edition}'
            print(f'  Fetching from {url}...')
            data = fetch_json(url)
            api_surahs = data.get('data', {}).get('surahs', [])
            print(f'  Got {len(api_surahs)} surahs from API')

            # Build a map of (surah_num, ayah_num) -> translation text
            translation_map = {}
            for api_surah in api_surahs:
                surah_num = api_surah['number']
                for api_ayah in api_surah.get('ayahs', []):
                    text = api_ayah.get('text', '').strip()
                    if text:
                        translation_map[(surah_num, api_ayah['numberInSurah'])] = text
            print(f'  Got {len(translation_map)} translations from API')

            # Fetch ALL ayahs from DB in one call
            all_ayahs = call(models, uid, 'islamic.ayah', 'search_read',
                             [[]], {'fields': ['id', 'surah_id', 'number']})
            print(f'  Found {len(all_ayahs)} ayahs in database')

            # Match and batch update
            total_updated = 0
            for ayah in all_ayahs:
                s_id = ayah['surah_id'][0] if ayah['surah_id'] else None
                # Find surah number from surah_id
                s_num = None
                for num, sid in surah_map.items():
                    if sid == s_id:
                        s_num = num
                        break
                if s_num is None:
                    continue
                text = translation_map.get((s_num, ayah['number']))
                if text:
                    call(models, uid, 'islamic.ayah', 'write',
                         [[ayah['id']], {field: text}])
                    total_updated += 1
                    if total_updated % 500 == 0:
                        print(f'  ... {total_updated} ayahs updated')

            print(f'  DONE: {total_updated} ayahs updated for {lang}')

        except Exception as e:
            print(f'  ERROR for {lang}: {e}')


def populate_adhkar(uid, models):
    print('\n=== ADHKAR TRANSLATIONS ===')

    all_adhkar = call(models, uid, 'islamic.adhkar', 'search_read',
                      [[]], {'fields': ['id', 'name', 'translation_en']})
    print(f'Found {len(all_adhkar)} adhkar in database')

    updated = 0
    for item in ADHKAR_TRANSLATIONS:
        en_prefix = item['en'][:50].lower()
        # Match by English translation
        matched = None
        for a in all_adhkar:
            if a.get('translation_en') and en_prefix in a['translation_en'][:60].lower():
                matched = a
                break
        # Fallback: match by name
        if not matched and item.get('name_match'):
            name_lower = item['name_match'].lower()
            for a in all_adhkar:
                if a.get('name') and name_lower in a['name'].lower():
                    matched = a
                    break

        if matched:
            vals = {}
            for key in ('translation_fr', 'translation_tr', 'translation_hi',
                        'name_fr', 'name_tr', 'name_hi'):
                short_key = key.split('_', 1)[1] if key.startswith('name_') else key.replace('translation_', '')
                src_key = key.replace('translation_', '').replace('name_', 'name_') if 'name' in key else key.replace('translation_', '')
                # Map: fr/tr/hi or name_fr/name_tr/name_hi
                if key.startswith('name_'):
                    lang_code = key.replace('name_', '')
                    if item.get(f'name_{lang_code}'):
                        vals[key] = item[f'name_{lang_code}']
                else:
                    lang_code = key.replace('translation_', '')
                    if item.get(lang_code):
                        vals[key] = item[lang_code]

            if vals:
                call(models, uid, 'islamic.adhkar', 'write', [[matched['id']], vals])
                updated += 1
                print(f'  Updated: {matched["name"][:50]}')
        else:
            print(f'  NOT FOUND: {item["en"][:50]}...')

    print(f'DONE: {updated} adhkar updated')


# ── Adhkar translation data ──────────────────────────────────────────────────
ADHKAR_TRANSLATIONS = [
    {
        'en': 'All praise is for Allah who gave us life after having taken it from us',
        'name_match': 'Morning Supplication (Waking Up)',
        'fr': "Louange à Allah qui nous a redonné la vie après nous avoir fait mourir, et c'est vers Lui que se fera la résurrection.",
        'tr': "Bizi öldürdükten sonra dirilten Allah'a hamd olsun. Dönüş O'nadır.",
        'hi': "सारी प्रशंसा अल्लाह के लिए है जिसने हमें मृत्यु (नींद) के बाद जीवन दिया और उसी की ओर लौटना है।",
        'name_fr': "Invocation du réveil", 'name_tr': "Uyanma Duası", 'name_hi': "जागने की दुआ",
    },
    {
        'en': 'O Allah, You are my Lord, there is none worthy of worship but You',
        'name_match': 'Morning Master Supplication',
        'fr': "Ô Allah, Tu es mon Seigneur, il n'y a de divinité digne d'adoration que Toi. Tu m'as créé et je suis Ton serviteur, je suis soumis à Ton pacte et à Ta promesse autant que je le peux. Je cherche refuge auprès de Toi contre le mal que j'ai commis. Je reconnais Tes bienfaits envers moi et je reconnais mon péché, pardonne-moi donc, car nul ne pardonne les péchés si ce n'est Toi.",
        'tr': "Allah'ım! Sen benim Rabbimsin. Senden başka ilah yoktur. Beni Sen yarattın. Ben Senin kulunum. Gücüm yettiğince Sana verdiğim söz ve vaadimin üzerindeyim. Yaptığım kötülüklerin şerrinden Sana sığınırım. Üzerimdeki nimetlerini itiraf ederim. Günahlarımı da itiraf ederim. Beni bağışla. Çünkü günahları ancak Sen bağışlarsın.",
        'hi': "ऐ अल्लाह! तू मेरा रब है, तेरे सिवा कोई माबूद नहीं। तूने मुझे पैदा किया और मैं तेरा बंदा हूँ, और मैं अपनी सामर्थ्य के अनुसार तेरे वादे और प्रतिज्ञा पर हूँ। मैंने जो कुछ किया उसकी बुराई से तेरी शरण चाहता हूँ। मैं अपने ऊपर तेरी नेमतों का और अपने गुनाहों का इकरार करता हूँ, सो तू मुझे माफ़ कर दे, क्योंकि तेरे सिवा गुनाहों को कोई माफ़ नहीं कर सकता।",
        'name_fr': "Maître invocation du matin", 'name_tr': "Seyyidul İstiğfar", 'name_hi': "सय्यिदुल इस्तिग़फ़ार",
    },
    {
        'en': 'We have reached the morning and at this very time all sovereignty belongs to Allah',
        'name_match': "Morning Remembrance of Allah's Sovereignty",
        'fr': "Nous voilà au matin et la royauté appartient à Allah. Louange à Allah. Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé.",
        'tr': "Sabaha erdik, mülk de Allah'a ait olarak sabaha erdi. Hamd Allah'a mahsustur. Allah'tan başka ilah yoktur.",
        'hi': "हमने सुबह की और सारी बादशाहत अल्लाह की है। सारी प्रशंसा अल्लाह के लिए है। अल्लाह के सिवा कोई माबूद नहीं।",
        'name_fr': "Souveraineté d'Allah le matin", 'name_tr': "Sabah Allah'ın Egemenliği", 'name_hi': "सुबह अल्लाह की संप्रभुता का ज़िक्र",
    },
    {
        'en': "O Allah, by Your leave we have reached the morning",
        'name_match': 'Morning Prayer for Protection',
        'fr': "Ô Allah, c'est par Toi que nous arrivons au matin et c'est par Toi que nous arrivons au soir.",
        'tr': "Allah'ım! Senin sayende sabaha erdik, Senin sayende akşama erdik.",
        'hi': "ऐ अल्लाह! तेरी कृपा से हमने सुबह की और तेरी कृपा से हमने शाम की।",
        'name_fr': "Prière du matin pour la protection", 'name_tr': "Sabah Korunma Duası", 'name_hi': "सुबह की सुरक्षा की दुआ",
    },
    {
        'en': "O Allah, You are my Lord, none has the right to be worshipped except You",
        'name_match': 'Trusting in Allah',
        'fr': "Ô Allah, Tu es mon Seigneur, nulle divinité n'est digne d'adoration sauf Toi. Je place ma confiance en Toi.",
        'tr': "Allah'ım! Sen benim Rabbimsin. Senden başka ilah yoktur. Sana tevekkül ettim.",
        'hi': "ऐ अल्लाह! तू मेरा रब है, तेरे सिवा कोई माबूद नहीं। मैंने तुझ पर भरोसा किया।",
        'name_fr': "Confiance en Allah", 'name_tr': "Allah'a Tevekkül", 'name_hi': "अल्लाह पर भरोसा",
    },
    {
        'en': "I am pleased with Allah as Lord",
        'name_match': 'Contentment with Allah',
        'fr': "Je suis satisfait d'Allah comme Seigneur, de l'Islam comme religion et de Muhammad comme prophète.",
        'tr': "Rab olarak Allah'tan, din olarak İslam'dan, peygamber olarak Muhammed'den razı oldum.",
        'hi': "मैं अल्लाह को रब मानकर, इस्लाम को दीन मानकर और मुहम्मद को नबी मानकर राज़ी हूँ।",
        'name_fr': "Contentement avec Allah", 'name_tr': "Allah'tan Razı Olmak", 'name_hi': "अल्लाह से राज़ी होना",
    },
    {
        'en': "O Living One, O Sustainer, in Your Mercy I seek relief",
        'name_match': "Seeking Allah's Mercy",
        'fr': "Ô Vivant, ô Subsistant, par Ta miséricorde j'implore secours.",
        'tr': "Ey Hayy ve Kayyum! Rahmetinle yardımını istiyorum.",
        'hi': "ऐ सदा जीवित! ऐ क़ायम रखने वाले! तेरी रहमत से मैं मदद माँगता हूँ।",
        'name_fr': "Recherche de la miséricorde", 'name_tr': "Allah'ın Rahmetini İstemek", 'name_hi': "अल्लाह की रहमत माँगना",
    },
    {
        'en': "In the name of Allah with Whose name nothing is harmed",
        'name_match': 'Protection from Harm',
        'fr': "Au nom d'Allah, grâce au nom duquel rien sur terre ni dans le ciel ne peut nuire.",
        'tr': "Allah'ın adıyla ki, O'nun adı anılınca yerde ve gökte hiçbir şey zarar veremez.",
        'hi': "अल्लाह के नाम से, जिसके नाम के साथ ज़मीन और आसमान में कोई चीज़ नुक़सान नहीं पहुँचा सकती।",
        'name_fr': "Protection contre le mal", 'name_tr': "Zarardan Korunma", 'name_hi': "हानि से सुरक्षा",
    },
    {
        'en': "I seek refuge in the perfect words of Allah from the evil",
        'name_match': 'Seeking Refuge in Allah',
        'fr': "Je cherche refuge dans les paroles parfaites d'Allah contre le mal de ce qu'Il a créé.",
        'tr': "Yarattıklarının şerrinden Allah'ın tam kelimelerine sığınırım.",
        'hi': "मैं अल्लाह के पूर्ण कलिमात की शरण लेता हूँ उसकी सृष्टि की बुराई से।",
        'name_fr': "Chercher refuge auprès d'Allah", 'name_tr': "Allah'a Sığınma", 'name_hi': "अल्लाह की शरण लेना",
    },
    {
        'en': "O Allah, grant my body health",
        'name_match': 'Prayer for Health',
        'fr': "Ô Allah, accorde la santé à mon corps, à mon ouïe et à ma vue.",
        'tr': "Allah'ım! Bedenime, kulağıma ve gözüme afiyet ver.",
        'hi': "ऐ अल्लाह! मेरे शरीर, कानों और आँखों को स्वस्थ रख।",
        'name_fr': "Prière pour la santé", 'name_tr': "Sağlık Duası", 'name_hi': "स्वास्थ्य की दुआ",
    },
    {
        'en': "Allah is sufficient for me, none has the right to be worshipped except Him",
        'name_match': 'Reliance on Allah',
        'fr': "Allah me suffit, il n'y a de divinité digne d'adoration que Lui, sur Lui je place ma confiance.",
        'tr': "Allah bana yeter. O'ndan başka ilah yoktur. O'na tevekkül ettim.",
        'hi': "अल्लाह मुझे काफ़ी है, उसके सिवा कोई माबूद नहीं, उसी पर मैंने भरोसा किया।",
        'name_fr': "Se fier à Allah", 'name_tr': "Allah'a Güvenmek", 'name_hi': "अल्लाह पर निर्भरता",
    },
    {
        'en': "Glory be to Allah and praise be to Him",
        'name_match': 'Glorification of Allah',
        'fr': "Gloire et louange à Allah.",
        'tr': "Allah'ı tesbih eder ve O'na hamd ederim.",
        'hi': "अल्लाह पाक है और उसी की प्रशंसा है।",
        'name_fr': "Glorification d'Allah", 'name_tr': "Allah'ı Tesbih", 'name_hi': "अल्लाह की तस्बीह",
    },
    {
        'en': "None has the right to be worshipped except Allah, alone, without partner",
        'name_match': 'Declaration of Tawhid',
        'fr': "Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है, उसका कोई साझी नहीं।",
        'name_fr': "Déclaration du Tawhid", 'name_tr': "Tevhid Beyanı", 'name_hi': "तौहीद की घोषणा",
    },
    {
        'en': "O Allah, I ask You for beneficial knowledge",
        'name_match': 'Prayer for Beneficial Knowledge',
        'fr': "Ô Allah, je Te demande une science bénéfique, une subsistance licite et des œuvres acceptées.",
        'tr': "Allah'ım! Senden faydalı ilim, helal rızık ve kabul olunan amel istiyorum.",
        'hi': "ऐ अल्लाह! मैं तुझसे लाभदायक ज्ञान, हलाल रोज़ी और क़बूल होने वाले अमल माँगता हूँ।",
        'name_fr': "Prière pour le savoir", 'name_tr': "Faydalı İlim Duası", 'name_hi': "लाभदायक ज्ञान की दुआ",
    },
    {
        'en': "I seek forgiveness from Allah",
        'name_match': 'Seeking Forgiveness',
        'fr': "Je demande pardon à Allah et me repens à Lui.",
        'tr': "Allah'tan bağışlanma diler ve O'na tövbe ederim.",
        'hi': "मैं अल्लाह से माफ़ी माँगता हूँ और उसकी ओर तौबा करता हूँ।",
        'name_fr': "Demande de pardon", 'name_tr': "İstiğfar", 'name_hi': "इस्तिग़फ़ार",
    },
    {
        'en': "We have reached the evening and at this very time all sovereignty belongs to Allah",
        'name_match': "Evening Remembrance",
        'fr': "Nous voilà au soir et la royauté appartient à Allah.",
        'tr': "Akşama erdik, mülk de Allah'a ait olarak akşama erdi.",
        'hi': "हमने शाम की और सारी बादशाहत अल्लाह की है।",
        'name_fr': "Rappel du soir", 'name_tr': "Akşam Zikri", 'name_hi': "शाम का ज़िक्र",
    },
    {
        'en': "O Allah, by Your leave we have reached the evening",
        'name_match': 'Evening Prayer',
        'fr': "Ô Allah, c'est par Toi que nous arrivons au soir.",
        'tr': "Allah'ım! Senin sayende akşama erdik.",
        'hi': "ऐ अल्लाह! तेरी कृपा से हमने शाम की।",
        'name_fr': "Prière du soir", 'name_tr': "Akşam Duası", 'name_hi': "शाम की दुआ",
    },
    {
        'en': "O Allah, Knower of the unseen and the seen",
        'name_match': 'Seeking Protection at Night',
        'fr': "Ô Allah, Connaisseur de l'invisible et du visible, Créateur des cieux et de la terre.",
        'tr': "Allah'ım! Gayb ve şehadet alemini bilen, göklerin ve yerin yaratıcısı!",
        'hi': "ऐ अल्लाह! ग़ैब और ज़ाहिर के जानने वाले, आसमानों और ज़मीन के पैदा करने वाले!",
        'name_fr': "Protection nocturne", 'name_tr': "Gece Korunma Duası", 'name_hi': "रात की सुरक्षा की दुआ",
    },
    {
        'en': "I seek the forgiveness of Allah",
        'name_match': 'Post-Prayer Forgiveness',
        'fr': "Je demande pardon à Allah.",
        'tr': "Allah'tan bağışlanma dilerim.",
        'hi': "मैं अल्लाह से माफ़ी माँगता हूँ।",
        'name_fr': "Pardon après la prière", 'name_tr': "Namaz Sonrası İstiğfar", 'name_hi': "नमाज़ के बाद इस्तिग़फ़ार",
    },
    {
        'en': "O Allah, You are Peace and from You is peace",
        'name_match': 'Source of Peace',
        'fr': "Ô Allah, Tu es la Paix et de Toi vient la paix.",
        'tr': "Allah'ım! Sen Selam'sın ve selamet Sendendir.",
        'hi': "ऐ अल्लाह! तू ही सलाम है और तुझी से शांति है।",
        'name_fr': "Source de paix", 'name_tr': "Barışın Kaynağı", 'name_hi': "शांति का स्रोत",
    },
    {
        'en': "There is no god but Allah, alone, without partner",
        'name_match': 'Post-Prayer Tawhid',
        'fr': "Il n'y a de divinité qu'Allah, Seul sans associé. À Lui la royauté et la louange.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है। बादशाहत और प्रशंसा उसी की है।",
        'name_fr': "Tawhid après la prière", 'name_tr': "Namaz Sonrası Tevhid", 'name_hi': "नमाज़ के बाद तौहीद",
    },
    {
        'en': "Glory be to Allah",
        'name_match': 'Tasbeeh after Prayer',
        'fr': "Gloire à Allah (33 fois), Louange à Allah (33 fois), Allah est le plus grand (33 fois).",
        'tr': "Sübhanallah (33), Elhamdülillah (33), Allahu Ekber (33).",
        'hi': "सुब्हानल्लाह (33), अल्हम्दुलिल्लाह (33), अल्लाहु अकबर (33)।",
        'name_fr': "Tasbih après la prière", 'name_tr': "Namaz Sonrası Tesbih", 'name_hi': "नमाज़ के बाद तस्बीह",
    },
    {
        'en': "Ayat al-Kursi",
        'name_match': 'Ayat al-Kursi',
        'fr': "Allah! Point de divinité à part Lui, le Vivant, Celui qui subsiste par Lui-même.",
        'tr': "Allah, O'ndan başka ilah yoktur. Hayy'dır, Kayyum'dur.",
        'hi': "अल्लाह, उसके सिवा कोई माबूद नहीं, वह हमेशा जीवित है, सबका संभालने वाला है।",
        'name_fr': "Ayat al-Kursi", 'name_tr': "Ayetel Kürsi", 'name_hi': "आयतुल कुर्सी",
    },
    {
        'en': "In Your name my Lord, I lie down and in Your name I rise",
        'name_match': 'Sleeping Supplication',
        'fr': "En Ton nom, Seigneur, je me couche et en Ton nom je me lève.",
        'tr': "Rabbim! Senin adınla yanımı yatağa koydum ve Senin adınla kaldırırım.",
        'hi': "ऐ मेरे रब! तेरे नाम से लेटता हूँ और तेरे नाम से उठता हूँ।",
        'name_fr': "Invocation du coucher", 'name_tr': "Uyku Duası", 'name_hi': "सोने की दुआ",
    },
    {
        'en': "O Allah, I submit my soul to You",
        'name_match': 'Entrusting the Soul',
        'fr': "Ô Allah, je remets mon âme à Toi, je tourne mon visage vers Toi.",
        'tr': "Allah'ım! Nefsimi Sana teslim ettim, yüzümü Sana çevirdim.",
        'hi': "ऐ अल्लाह! मैंने अपनी जान तुझे सौंप दी, अपना चेहरा तेरी ओर फेर लिया।",
        'name_fr': "Confier son âme", 'name_tr': "Ruhunu Teslim Etme", 'name_hi': "आत्मा सौंपना",
    },
    {
        'en': "O Allah, protect me from Your punishment on the Day",
        'name_match': 'Protection from Punishment',
        'fr': "Ô Allah, protège-moi de Ton châtiment le Jour où Tu ressusciteras Tes serviteurs.",
        'tr': "Allah'ım! Kullarını dirilttiğin gün azabından beni koru.",
        'hi': "ऐ अल्लाह! जिस दिन तू अपने बंदों को उठाएगा उस दिन अपनी सज़ा से मुझे बचा।",
        'name_fr': "Protection contre le châtiment", 'name_tr': "Azaptan Korunma", 'name_hi': "अज़ाब से सुरक्षा",
    },
    {
        'en': "Our Lord, give us good in this world and good in the Hereafter",
        'name_match': 'Dua for Good',
        'fr': "Notre Seigneur, donne-nous une belle part dans ce monde et une belle part dans l'au-delà.",
        'tr': "Rabbimiz! Bize dünyada iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.",
        'hi': "ऐ हमारे रब! हमें दुनिया में भी भलाई दे और आख़िरत में भी भलाई दे।",
        'name_fr': "Invocation pour le bien", 'name_tr': "İyilik Duası", 'name_hi': "भलाई की दुआ",
    },
    {
        'en': "Our Lord, do not let our hearts deviate",
        'name_match': 'Dua for Steadfastness',
        'fr': "Notre Seigneur, ne fais pas dévier nos cœurs après que Tu nous aies guidés.",
        'tr': "Rabbimiz! Bizi hidayete erdirdikten sonra kalplerimizi eğriltme.",
        'hi': "ऐ हमारे रब! हमें हिदायत देने के बाद हमारे दिलों को न फेर।",
        'name_fr': "Invocation pour la constance", 'name_tr': "Sebat Duası", 'name_hi': "इस्तिक़ामत की दुआ",
    },
    {
        'en': "My Lord, increase me in knowledge",
        'name_match': 'Dua for Knowledge',
        'fr': "Mon Seigneur, augmente mes connaissances.",
        'tr': "Rabbim! İlmimi artır.",
        'hi': "ऐ मेरे रब! मेरा ज्ञान बढ़ा दे।",
        'name_fr': "Invocation pour le savoir", 'name_tr': "İlim Duası", 'name_hi': "ज्ञान की दुआ",
    },
    {
        'en': "Our Lord, forgive us our sins and the excess in our affairs",
        'name_match': 'Dua for Forgiveness',
        'fr': "Notre Seigneur, pardonne-nous nos péchés et nos excès.",
        'tr': "Rabbimiz! Günahlarımızı ve işlerimizdeki taşkınlıklarımızı bağışla.",
        'hi': "ऐ हमारे रब! हमारे गुनाहों और हमारे मामलों में ज़्यादती को माफ़ कर दे।",
        'name_fr': "Invocation pour le pardon", 'name_tr': "Bağışlanma Duası", 'name_hi': "माफ़ी की दुआ",
    },
]


if __name__ == '__main__':
    print('=== Islamic App Translation Populator ===\n')
    uid, models = connect()
    populate_quran(uid, models)
    populate_adhkar(uid, models)
    print('\n=== ALL DONE ===')
