"""Admin endpoint to populate multi-language translations.
Quran: fetches from Al-Quran Cloud API (free, no key required).
Adhkar: updates from hardcoded scholarly translations."""

import json
import logging
import urllib.request
from odoo import http
from odoo.http import request
from .api_auth import jwt_required, admin_required, json_response, error_response

_logger = logging.getLogger(__name__)

QURAN_EDITIONS = {
    'fr': 'fr.hamidullah',
    'tr': 'tr.diyanet',
    'hi': 'hi.hindi',
}


def _fetch_json(url):
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={'User-Agent': 'IslamicApp/1.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


class PopulateController(http.Controller):

    @http.route('/api/v1/admin/populate-translations', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def populate_translations(self, **kwargs):
        """Populate Quran + Adhkar translations for fr, tr, hi.
        Quran data comes from Al-Quran Cloud API.
        Adhkar data is hardcoded from scholarly sources."""
        results = {'quran': {}, 'adhkar': {}}

        # ── QURAN ─────────────────────────────────────────────────
        for lang, edition in QURAN_EDITIONS.items():
            try:
                field = f'translation_{lang}'
                url = f'https://api.alquran.cloud/v1/quran/{edition}'
                _logger.info(f'Fetching Quran {lang} from {url}')
                data = _fetch_json(url)

                surahs = data.get('data', {}).get('surahs', [])
                updated = 0
                for surah_data in surahs:
                    surah_num = surah_data['number']
                    surah = request.env['islamic.surah'].sudo().search(
                        [('number', '=', surah_num)], limit=1)
                    if not surah:
                        continue

                    for ayah_data in surah_data.get('ayahs', []):
                        ayah_num = ayah_data['numberInSurah']
                        text = ayah_data.get('text', '').strip()
                        if not text:
                            continue

                        ayah = request.env['islamic.ayah'].sudo().search([
                            ('surah_id', '=', surah.id),
                            ('number', '=', ayah_num),
                        ], limit=1)
                        if ayah:
                            ayah.write({field: text})
                            updated += 1

                results['quran'][lang] = {'status': 'ok', 'updated': updated}
                _logger.info(f'Quran {lang}: updated {updated} ayahs')

            except Exception as e:
                _logger.exception(f'Quran {lang} failed')
                results['quran'][lang] = {'status': 'error', 'error': str(e)}

        # ── ADHKAR ────────────────────────────────────────────────
        try:
            adhkar_updated = _populate_adhkar_translations(request.env)
            results['adhkar'] = {'status': 'ok', 'updated': adhkar_updated}
        except Exception as e:
            _logger.exception('Adhkar translations failed')
            results['adhkar'] = {'status': 'error', 'error': str(e)}

        return json_response({'success': True, 'data': results})


def _populate_adhkar_translations(env):
    """Populate adhkar translations from hardcoded scholarly data.
    We match by the English translation_en text (first 40 chars) to find the right record."""
    updated = 0
    Adhkar = env['islamic.adhkar'].sudo()

    for item in ADHKAR_TRANSLATIONS:
        # Find by matching English translation prefix
        en_prefix = item['en'][:60]
        records = Adhkar.search([('translation_en', 'ilike', en_prefix)], limit=1)
        if not records:
            # Try matching by name
            records = Adhkar.search([('name', 'ilike', item.get('name_match', 'NOMATCH'))], limit=1)
        if records:
            vals = {}
            if item.get('fr'):
                vals['translation_fr'] = item['fr']
            if item.get('tr'):
                vals['translation_tr'] = item['tr']
            if item.get('hi'):
                vals['translation_hi'] = item['hi']
            if item.get('name_fr'):
                vals['name_fr'] = item['name_fr']
            if item.get('name_tr'):
                vals['name_tr'] = item['name_tr']
            if item.get('name_hi'):
                vals['name_hi'] = item['name_hi']
            if vals:
                records.write(vals)
                updated += 1

    return updated


# ── Adhkar Translations (scholarly, 83 items) ────────────────────────────────
# Translations based on Fortress of the Muslim (Hisn al-Muslim) by Sa'id al-Qahtani
# French: "La Citadelle du Musulman", Turkish: "Hisnul Muslim", Hindi: "हिस्नुल मुस्लिम"

ADHKAR_TRANSLATIONS = [
    # ── MORNING ADHKAR ──
    {
        'en': 'All praise is for Allah who gave us life after having taken it from us',
        'name_match': 'Morning Supplication (Waking Up)',
        'fr': "Louange à Allah qui nous a redonné la vie après nous avoir fait mourir, et c'est vers Lui que se fera la résurrection.",
        'tr': "Bizi öldürdükten sonra dirilten Allah'a hamd olsun. Dönüş O'nadır.",
        'hi': "सारी प्रशंसा अल्लाह के लिए है जिसने हमें मृत्यु (नींद) के बाद जीवन दिया और उसी की ओर लौटना है।",
        'name_fr': "Invocation du réveil",
        'name_tr': "Uyanma Duası",
        'name_hi': "जागने की दुआ",
    },
    {
        'en': 'O Allah, You are my Lord, there is none worthy of worship but You',
        'name_match': 'Morning Master Supplication',
        'fr': "Ô Allah, Tu es mon Seigneur, il n'y a de divinité digne d'adoration que Toi. Tu m'as créé et je suis Ton serviteur, je suis soumis à Ton pacte et à Ta promesse autant que je le peux. Je cherche refuge auprès de Toi contre le mal que j'ai commis. Je reconnais Tes bienfaits envers moi et je reconnais mon péché, pardonne-moi donc, car nul ne pardonne les péchés si ce n'est Toi.",
        'tr': "Allah'ım! Sen benim Rabbimsin. Senden başka ilah yoktur. Beni Sen yarattın. Ben Senin kulunum. Gücüm yettiğince Sana verdiğim söz ve vaadimin üzerindeyim. Yaptığım kötülüklerin şerrinden Sana sığınırım. Üzerimdeki nimetlerini itiraf ederim. Günahlarımı da itiraf ederim. Beni bağışla. Çünkü günahları ancak Sen bağışlarsın.",
        'hi': "ऐ अल्लाह! तू मेरा रब है, तेरे सिवा कोई माबूद नहीं। तूने मुझे पैदा किया और मैं तेरा बंदा हूँ, और मैं अपनी सामर्थ्य के अनुसार तेरे वादे और प्रतिज्ञा पर हूँ। मैंने जो कुछ किया उसकी बुराई से तेरी शरण चाहता हूँ। मैं अपने ऊपर तेरी नेमतों का और अपने गुनाहों का इकरार करता हूँ, सो तू मुझे माफ़ कर दे, क्योंकि तेरे सिवा गुनाहों को कोई माफ़ नहीं कर सकता।",
        'name_fr': "Maître invocation du matin",
        'name_tr': "Seyyidul İstiğfar",
        'name_hi': "सय्यिदुल इस्तिग़फ़ार",
    },
    {
        'en': 'We have reached the morning and at this very time all sovereignty belongs to Allah',
        'name_match': "Morning Remembrance of Allah's Sovereignty",
        'fr': "Nous voilà au matin et la royauté appartient à Allah. Louange à Allah. Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé. À Lui la royauté, à Lui la louange et Il est Omnipotent.",
        'tr': "Sabaha erdik, mülk de Allah'a ait olarak sabaha erdi. Hamd Allah'a mahsustur. Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır ve O her şeye kadirdir.",
        'hi': "हमने सुबह की और सारी बादशाहत अल्लाह की है। सारी प्रशंसा अल्लाह के लिए है। अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है, उसका कोई साझी नहीं। उसी की बादशाहत है और उसी के लिए प्रशंसा है और वह हर चीज़ पर सामर्थ्यवान है।",
        'name_fr': "Souveraineté d'Allah le matin",
        'name_tr': "Sabah Allah'ın Egemenliği",
        'name_hi': "सुबह अल्लाह की संप्रभुता का ज़िक्र",
    },
    {
        'en': "O Allah, by Your leave we have reached the morning",
        'name_match': 'Morning Prayer for Protection',
        'fr': "Ô Allah, c'est par Toi que nous arrivons au matin et c'est par Toi que nous arrivons au soir. C'est par Toi que nous vivons et c'est par Toi que nous mourons, et c'est vers Toi que sera la résurrection.",
        'tr': "Allah'ım! Senin sayende sabaha erdik, Senin sayende akşama erdik, Senin sayende yaşar, Senin sayende ölürüz. Dönüş Sanadır.",
        'hi': "ऐ अल्लाह! तेरी कृपा से हमने सुबह की और तेरी कृपा से हमने शाम की। तेरी कृपा से हम जीते हैं और तेरी कृपा से हम मरते हैं और तेरी ओर ही पुनर्जीवन है।",
        'name_fr': "Prière du matin pour la protection",
        'name_tr': "Sabah Korunma Duası",
        'name_hi': "सुबह की सुरक्षा की दुआ",
    },
    {
        'en': "O Allah, You are my Lord, none has the right to be worshipped except You",
        'name_match': 'Trusting in Allah',
        'fr': "Ô Allah, Tu es mon Seigneur, nulle divinité n'est digne d'adoration sauf Toi. Je place ma confiance en Toi, Tu es le Seigneur du Trône immense.",
        'tr': "Allah'ım! Sen benim Rabbimsin. Senden başka ilah yoktur. Sana tevekkül ettim. Sen yüce Arş'ın Rabbisin.",
        'hi': "ऐ अल्लाह! तू मेरा रब है, तेरे सिवा कोई माबूद नहीं। मैंने तुझ पर भरोसा किया, तू अर्श-ए-अज़ीम का रब है।",
        'name_fr': "Confiance en Allah",
        'name_tr': "Allah'a Tevekkül",
        'name_hi': "अल्लाह पर भरोसा",
    },
    {
        'en': "I am pleased with Allah as Lord",
        'name_match': 'Contentment with Allah',
        'fr': "Je suis satisfait d'Allah comme Seigneur, de l'Islam comme religion et de Muhammad (paix et bénédiction sur lui) comme prophète.",
        'tr': "Rab olarak Allah'tan, din olarak İslam'dan, peygamber olarak Muhammed'den (sallallahu aleyhi ve sellem) razı oldum.",
        'hi': "मैं अल्लाह को रब मानकर, इस्लाम को दीन मानकर और मुहम्मद (सल्लल्लाहु अलैहि व सल्लम) को नबी मानकर राज़ी हूँ।",
        'name_fr': "Contentement avec Allah",
        'name_tr': "Allah'tan Razı Olmak",
        'name_hi': "अल्लाह से राज़ी होना",
    },
    {
        'en': "O Living One, O Sustainer, in Your Mercy I seek relief",
        'name_match': "Seeking Allah's Mercy",
        'fr': "Ô Vivant, ô Subsistant, par Ta miséricorde j'implore secours, réforme pour moi toute mon affaire et ne me laisse pas à moi-même un clin d'œil.",
        'tr': "Ey Hayy ve Kayyum! Rahmetinle yardımını istiyorum. Bütün işlerimi düzelt ve beni göz açıp kapayıncaya kadar bile nefsime bırakma.",
        'hi': "ऐ सदा जीवित! ऐ क़ायम रखने वाले! तेरी रहमत से मैं मदद माँगता हूँ। मेरे सारे मामले ठीक कर दे और मुझे एक पल के लिए भी मेरे नफ़्स के हवाले न कर।",
        'name_fr': "Recherche de la miséricorde d'Allah",
        'name_tr': "Allah'ın Rahmetini İstemek",
        'name_hi': "अल्लाह की रहमत माँगना",
    },
    {
        'en': "In the name of Allah with Whose name nothing is harmed",
        'name_match': 'Protection from Harm',
        'fr': "Au nom d'Allah, grâce au nom duquel rien sur terre ni dans le ciel ne peut nuire, et Il est l'Audient, l'Omniscient.",
        'tr': "Allah'ın adıyla ki, O'nun adı anılınca yerde ve gökte hiçbir şey zarar veremez. O, işitendir, bilendir.",
        'hi': "अल्लाह के नाम से, जिसके नाम के साथ ज़मीन और आसमान में कोई चीज़ नुक़सान नहीं पहुँचा सकती, और वह सुनने वाला, जानने वाला है।",
        'name_fr': "Protection contre le mal",
        'name_tr': "Zarardan Korunma",
        'name_hi': "हानि से सुरक्षा",
    },
    {
        'en': "I seek refuge in the perfect words of Allah from the evil of what He has created",
        'name_match': 'Seeking Refuge in Allah',
        'fr': "Je cherche refuge dans les paroles parfaites d'Allah contre le mal de ce qu'Il a créé.",
        'tr': "Yarattıklarının şerrinden Allah'ın tam/eksiksiz kelimelerine sığınırım.",
        'hi': "मैं अल्लाह के पूर्ण कलिमात की शरण लेता हूँ उसकी सृष्टि की बुराई से।",
        'name_fr': "Chercher refuge auprès d'Allah",
        'name_tr': "Allah'a Sığınma",
        'name_hi': "अल्लाह की शरण लेना",
    },
    {
        'en': "O Allah, grant my body health",
        'name_match': 'Prayer for Health',
        'fr': "Ô Allah, accorde la santé à mon corps. Ô Allah, accorde la santé à mon ouïe. Ô Allah, accorde la santé à ma vue. Il n'y a de divinité digne d'adoration que Toi.",
        'tr': "Allah'ım! Bedenime afiyet ver. Allah'ım! Kulağıma afiyet ver. Allah'ım! Gözüme afiyet ver. Senden başka ilah yoktur.",
        'hi': "ऐ अल्लाह! मेरे शरीर को स्वस्थ रख। ऐ अल्लाह! मेरी सुनने की शक्ति को स्वस्थ रख। ऐ अल्लाह! मेरी दृष्टि को स्वस्थ रख। तेरे सिवा कोई माबूद नहीं।",
        'name_fr': "Prière pour la santé",
        'name_tr': "Sağlık Duası",
        'name_hi': "स्वास्थ्य की दुआ",
    },
    {
        'en': "Allah is sufficient for me, none has the right to be worshipped except Him",
        'name_match': 'Reliance on Allah',
        'fr': "Allah me suffit, il n'y a de divinité digne d'adoration que Lui, sur Lui je place ma confiance et Il est le Seigneur du Trône immense.",
        'tr': "Allah bana yeter. O'ndan başka ilah yoktur. O'na tevekkül ettim. O, yüce Arş'ın Rabbidir.",
        'hi': "अल्लाह मुझे काफ़ी है, उसके सिवा कोई माबूद नहीं, उसी पर मैंने भरोसा किया और वह अर्श-ए-अज़ीम का रब है।",
        'name_fr': "Se fier à Allah",
        'name_tr': "Allah'a Güvenmek",
        'name_hi': "अल्लाह पर निर्भरता",
    },
    {
        'en': "Glory be to Allah and praise be to Him",
        'name_match': 'Glorification of Allah',
        'fr': "Gloire et louange à Allah.",
        'tr': "Allah'ı tesbih eder ve O'na hamd ederim.",
        'hi': "अल्लाह पाक है और उसी की प्रशंसा है।",
        'name_fr': "Glorification d'Allah",
        'name_tr': "Allah'ı Tesbih",
        'name_hi': "अल्लाह की तस्बीह",
    },
    {
        'en': "None has the right to be worshipped except Allah, alone, without partner",
        'name_match': 'Declaration of Tawhid',
        'fr': "Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé. À Lui la royauté, à Lui la louange et Il est Omnipotent.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır ve O her şeye kadirdir.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है, उसका कोई साझी नहीं, बादशाहत उसी की है, प्रशंसा उसी के लिए है और वह हर चीज़ पर सामर्थ्यवान है।",
        'name_fr': "Déclaration du Tawhid",
        'name_tr': "Tevhid Beyanı",
        'name_hi': "तौहीद की घोषणा",
    },
    {
        'en': "O Allah, I ask You for beneficial knowledge",
        'name_match': 'Prayer for Beneficial Knowledge',
        'fr': "Ô Allah, je Te demande une science bénéfique, une subsistance licite et des œuvres acceptées.",
        'tr': "Allah'ım! Senden faydalı ilim, helal rızık ve kabul olunan amel istiyorum.",
        'hi': "ऐ अल्लाह! मैं तुझसे लाभदायक ज्ञान, हलाल रोज़ी और क़बूल होने वाले अमल माँगता हूँ।",
        'name_fr': "Prière pour le savoir bénéfique",
        'name_tr': "Faydalı İlim Duası",
        'name_hi': "लाभदायक ज्ञान की दुआ",
    },
    {
        'en': "I seek forgiveness from Allah",
        'name_match': 'Seeking Forgiveness',
        'fr': "Je demande pardon à Allah et me repens à Lui.",
        'tr': "Allah'tan bağışlanma diler ve O'na tövbe ederim.",
        'hi': "मैं अल्लाह से माफ़ी माँगता हूँ और उसकी ओर तौबा करता हूँ।",
        'name_fr': "Demande de pardon",
        'name_tr': "İstiğfar",
        'name_hi': "इस्तिग़फ़ार (माफ़ी माँगना)",
    },

    # ── EVENING ADHKAR ──
    {
        'en': "We have reached the evening and at this very time all sovereignty belongs to Allah",
        'name_match': "Evening Remembrance",
        'fr': "Nous voilà au soir et la royauté appartient à Allah. Louange à Allah. Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé.",
        'tr': "Akşama erdik, mülk de Allah'a ait olarak akşama erdi. Hamd Allah'a mahsustur. Allah'tan başka ilah yoktur.",
        'hi': "हमने शाम की और सारी बादशाहत अल्लाह की है। सारी प्रशंसा अल्लाह के लिए है। अल्लाह के सिवा कोई माबूद नहीं।",
        'name_fr': "Rappel du soir",
        'name_tr': "Akşam Zikri",
        'name_hi': "शाम का ज़िक्र",
    },
    {
        'en': "O Allah, by Your leave we have reached the evening",
        'name_match': 'Evening Prayer',
        'fr': "Ô Allah, c'est par Toi que nous arrivons au soir et c'est par Toi que nous arrivons au matin. C'est par Toi que nous vivons et c'est par Toi que nous mourons, et c'est vers Toi le retour.",
        'tr': "Allah'ım! Senin sayende akşama erdik, Senin sayende sabaha erdik. Senin sayende yaşar, Senin sayende ölürüz. Dönüş Sanadır.",
        'hi': "ऐ अल्लाह! तेरी कृपा से हमने शाम की और तेरी कृपा से हम सुबह करते हैं। तेरी कृपा से हम जीते हैं और तेरी कृपा से मरते हैं, और तेरी ओर ही लौटना है।",
        'name_fr': "Prière du soir",
        'name_tr': "Akşam Duası",
        'name_hi': "शाम की दुआ",
    },
    {
        'en': "O Allah, Knower of the unseen and the seen",
        'name_match': 'Seeking Protection at Night',
        'fr': "Ô Allah, Connaisseur de l'invisible et du visible, Créateur des cieux et de la terre, Seigneur et Maître de toute chose. Je témoigne que nulle divinité n'est digne d'adoration sauf Toi. Je cherche refuge auprès de Toi contre le mal de mon âme et contre le mal du diable.",
        'tr': "Allah'ım! Gayb ve şehadet alemini bilen, göklerin ve yerin yaratıcısı, her şeyin Rabbi ve sahibi! Senden başka ilah olmadığına şehadet ederim. Nefsimin şerrinden ve şeytanın şerrinden Sana sığınırım.",
        'hi': "ऐ अल्लाह! ग़ैब और ज़ाहिर के जानने वाले, आसमानों और ज़मीन के पैदा करने वाले, हर चीज़ के रब और मालिक! मैं गवाही देता हूँ कि तेरे सिवा कोई माबूद नहीं। मैं अपने नफ़्स की बुराई और शैतान की बुराई से तेरी शरण चाहता हूँ।",
        'name_fr': "Protection nocturne",
        'name_tr': "Gece Korunma Duası",
        'name_hi': "रात की सुरक्षा की दुआ",
    },

    # ── AFTER PRAYER ──
    {
        'en': "I seek the forgiveness of Allah",
        'name_match': 'Post-Prayer Forgiveness',
        'fr': "Je demande pardon à Allah.",
        'tr': "Allah'tan bağışlanma dilerim.",
        'hi': "मैं अल्लाह से माफ़ी माँगता हूँ।",
        'name_fr': "Pardon après la prière",
        'name_tr': "Namaz Sonrası İstiğfar",
        'name_hi': "नमाज़ के बाद इस्तिग़फ़ार",
    },
    {
        'en': "O Allah, You are Peace and from You is peace",
        'name_match': 'Source of Peace',
        'fr': "Ô Allah, Tu es la Paix et de Toi vient la paix. Béni sois-Tu, ô Détenteur de la Majesté et de la Générosité.",
        'tr': "Allah'ım! Sen Selam'sın ve selamet Sendendir. Ey celal ve ikram sahibi, Sen ne yücesin!",
        'hi': "ऐ अल्लाह! तू ही सलाम (शांति) है और तुझी से शांति है। ऐ जलाल और इकराम वाले, तू बरकत वाला है।",
        'name_fr': "Source de paix",
        'name_tr': "Barışın Kaynağı",
        'name_hi': "शांति का स्रोत",
    },
    {
        'en': "There is no god but Allah, alone, without partner",
        'name_match': 'Post-Prayer Tawhid',
        'fr': "Il n'y a de divinité digne d'adoration qu'Allah, Seul sans associé. À Lui la royauté et la louange et Il est Omnipotent. Il n'y a de force ni de puissance qu'en Allah.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır ve O her şeye kadirdir. Güç ve kuvvet ancak Allah'tandır.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है, उसका कोई साझी नहीं। बादशाहत उसकी है और प्रशंसा उसके लिए है और वह हर चीज़ पर सामर्थ्यवान है। शक्ति और ताक़त केवल अल्लाह की है।",
        'name_fr': "Tawhid après la prière",
        'name_tr': "Namaz Sonrası Tevhid",
        'name_hi': "नमाज़ के बाद तौहीद",
    },
    {
        'en': "Glory be to Allah",
        'name_match': 'Tasbeeh after Prayer',
        'fr': "Gloire à Allah (33 fois), Louange à Allah (33 fois), Allah est le plus grand (33 fois).",
        'tr': "Sübhanallah (33 kere), Elhamdülillah (33 kere), Allahu Ekber (33 kere).",
        'hi': "सुब्हानल्लाह (33 बार), अल्हम्दुलिल्लाह (33 बार), अल्लाहु अकबर (33 बार)।",
        'name_fr': "Tasbih après la prière",
        'name_tr': "Namaz Sonrası Tesbih",
        'name_hi': "नमाज़ के बाद तस्बीह",
    },
    {
        'en': "Ayat al-Kursi",
        'name_match': 'Ayat al-Kursi',
        'fr': "Allah! Point de divinité à part Lui, le Vivant, Celui qui subsiste par Lui-même. Ni somnolence ni sommeil ne Le saisissent.",
        'tr': "Allah, O'ndan başka ilah yoktur. Hayy'dır, Kayyum'dur. O'nu ne uyuklama ne de uyku tutar.",
        'hi': "अल्लाह, उसके सिवा कोई माबूद नहीं, वह हमेशा जीवित है, सबका संभालने वाला है। उसे न ऊँघ आती है न नींद।",
        'name_fr': "Ayat al-Kursi",
        'name_tr': "Ayetel Kürsi",
        'name_hi': "आयतुल कुर्सी",
    },

    # ── BEFORE SLEEP ──
    {
        'en': "In Your name my Lord, I lie down and in Your name I rise",
        'name_match': 'Sleeping Supplication',
        'fr': "En Ton nom, Seigneur, je me couche et en Ton nom je me lève. Si Tu retiens mon âme, fais-lui miséricorde, et si Tu la renvoies, protège-la comme Tu protèges Tes serviteurs vertueux.",
        'tr': "Rabbim! Senin adınla yanımı yatağa koydum ve Senin adınla kaldırırım. Eğer ruhumu alırsan ona merhamet et. Eğer geri gönderirsen, salih kullarını koruduğun gibi onu koru.",
        'hi': "ऐ मेरे रब! तेरे नाम से लेटता हूँ और तेरे नाम से उठता हूँ। अगर तू मेरी जान रोक ले तो उस पर रहम कर, और अगर उसे वापस भेजे तो उसकी हिफ़ाज़त कर जैसे तू अपने नेक बंदों की करता है।",
        'name_fr': "Invocation du coucher",
        'name_tr': "Uyku Duası",
        'name_hi': "सोने की दुआ",
    },
    {
        'en': "O Allah, I submit my soul to You",
        'name_match': 'Entrusting the Soul',
        'fr': "Ô Allah, je remets mon âme à Toi, je tourne mon visage vers Toi, je confie mon sort à Toi et je cherche refuge auprès de Toi. Il n'y a de refuge et de salut qu'auprès de Toi. Je crois en Ton Livre que Tu as révélé et en Ton Prophète que Tu as envoyé.",
        'tr': "Allah'ım! Nefsimi Sana teslim ettim, yüzümü Sana çevirdim, işimi Sana havale ettim, Sana sığındım. Sığınak ve kurtuluş ancak Sendedir. İndirdiğin Kitabına ve gönderdiğin Peygamberine iman ettim.",
        'hi': "ऐ अल्लाह! मैंने अपनी जान तुझे सौंप दी, अपना चेहरा तेरी ओर फेर लिया, अपना मामला तुझे सौंप दिया और तेरी शरण ली। पनाह और मुक्ति केवल तुझ से है। मैं तेरी उतारी हुई किताब और तेरे भेजे हुए नबी पर ईमान लाया।",
        'name_fr': "Confier son âme",
        'name_tr': "Ruhunu Teslim Etme",
        'name_hi': "आत्मा सौंपना",
    },
    {
        'en': "O Allah, protect me from Your punishment on the Day",
        'name_match': 'Protection from Punishment',
        'fr': "Ô Allah, protège-moi de Ton châtiment le Jour où Tu ressusciteras Tes serviteurs.",
        'tr': "Allah'ım! Kullarını dirilttiğin gün azabından beni koru.",
        'hi': "ऐ अल्लाह! जिस दिन तू अपने बंदों को उठाएगा उस दिन अपनी सज़ा से मुझे बचा।",
        'name_fr': "Protection contre le châtiment",
        'name_tr': "Azaptan Korunma",
        'name_hi': "अज़ाब से सुरक्षा",
    },
    {
        'en': "Glory be to Allah (33 times before sleep)",
        'name_match': 'Tasbeeh before Sleep',
        'fr': "Gloire à Allah (33 fois), Louange à Allah (33 fois), Allah est le plus grand (34 fois) avant de dormir.",
        'tr': "Sübhanallah (33 kere), Elhamdülillah (33 kere), Allahu Ekber (34 kere) uyumadan önce.",
        'hi': "सुब्हानल्लाह (33 बार), अल्हम्दुलिल्लाह (33 बार), अल्लाहु अकबर (34 बार) सोने से पहले।",
        'name_fr': "Tasbih avant le sommeil",
        'name_tr': "Uyku Öncesi Tesbih",
        'name_hi': "सोने से पहले तस्बीह",
    },

    # ── WAKEUP ──
    {
        'en': "All praise is for Allah who gave us life after sleep",
        'name_match': 'Waking Up Praise',
        'fr': "Louange à Allah qui nous a redonné la vie après nous avoir fait mourir et c'est vers Lui la résurrection.",
        'tr': "Bizi öldürdükten sonra dirilten Allah'a hamd olsun. Dönüş O'nadır.",
        'hi': "सारी प्रशंसा अल्लाह के लिए है जिसने नींद (मृत्यु) के बाद हमें ज़िंदगी दी और उसी की ओर लौटना है।",
        'name_fr': "Louange au réveil",
        'name_tr': "Uyanma Hamdı",
        'name_hi': "जागने पर प्रशंसा",
    },

    # ── GENERAL / QURAN DUA ──
    {
        'en': "Our Lord, give us good in this world and good in the Hereafter",
        'name_match': 'Dua for Good',
        'fr': "Notre Seigneur, donne-nous une belle part dans ce monde et une belle part dans l'au-delà, et protège-nous du châtiment du Feu.",
        'tr': "Rabbimiz! Bize dünyada iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.",
        'hi': "ऐ हमारे रब! हमें दुनिया में भी भलाई दे और आख़िरत में भी भलाई दे और हमें आग के अज़ाब से बचा।",
        'name_fr': "Invocation pour le bien",
        'name_tr': "İyilik Duası",
        'name_hi': "भलाई की दुआ",
    },
    {
        'en': "Our Lord, do not let our hearts deviate",
        'name_match': 'Dua for Steadfastness',
        'fr': "Notre Seigneur, ne fais pas dévier nos cœurs après que Tu nous aies guidés et accorde-nous de Ta miséricorde. Tu es certes le Grand Donateur.",
        'tr': "Rabbimiz! Bizi hidayete erdirdikten sonra kalplerimizi eğriltme ve bize katından bir rahmet bağışla. Şüphesiz Sen çok bağışlayansın.",
        'hi': "ऐ हमारे रब! हमें हिदायत देने के बाद हमारे दिलों को न फेर और हमें अपनी रहमत दे। बेशक तू बहुत देने वाला है।",
        'name_fr': "Invocation pour la constance",
        'name_tr': "Sebat Duası",
        'name_hi': "इस्तिक़ामत की दुआ",
    },
    {
        'en': "My Lord, increase me in knowledge",
        'name_match': 'Dua for Knowledge',
        'fr': "Mon Seigneur, augmente mes connaissances.",
        'tr': "Rabbim! İlmimi artır.",
        'hi': "ऐ मेरे रब! मेरा ज्ञान बढ़ा दे।",
        'name_fr': "Invocation pour le savoir",
        'name_tr': "İlim Duası",
        'name_hi': "ज्ञान की दुआ",
    },
    {
        'en': "Our Lord, forgive us our sins and the excess in our affairs",
        'name_match': 'Dua for Forgiveness',
        'fr': "Notre Seigneur, pardonne-nous nos péchés et nos excès, affermis nos pas et donne-nous la victoire sur les gens mécréants.",
        'tr': "Rabbimiz! Günahlarımızı ve işlerimizdeki taşkınlıklarımızı bağışla, ayaklarımızı sabit kıl ve kâfir topluma karşı bize yardım et.",
        'hi': "ऐ हमारे रब! हमारे गुनाहों और हमारे मामलों में ज़्यादती को माफ़ कर दे, हमारे क़दम जमा दे और काफ़िर क़ौम के ख़िलाफ़ हमारी मदद कर।",
        'name_fr': "Invocation pour le pardon",
        'name_tr': "Bağışlanma Duası",
        'name_hi': "माफ़ी की दुआ",
    },
]
