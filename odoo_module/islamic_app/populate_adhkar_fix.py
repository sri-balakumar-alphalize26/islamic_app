#!/usr/bin/env python3
"""Fix adhkar translations - match by database ID."""
import xmlrpc.client

ODOO_URL = 'http://192.168.255.246:8069'
ODOO_DB = 'odookra'
ODOO_USER = 'aghniesh@gmail.com'
ODOO_PASS = '1234'

common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
print(f'Connected uid={uid}')

def w(ids, vals):
    models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'islamic.adhkar', 'write', [ids, vals])

# Map: DB ID -> {fr, tr, hi, name_fr, name_tr, name_hi}
TRANSLATIONS = {
    7: {
        'name_fr': "Trois Qul du matin", 'name_tr': "Sabah Uc Kul", 'name_hi': "सुबह की तीन क़ुल",
        'fr': "Dis : Il est Allah, Unique. Allah, Le Seul à être imploré. Il n'a jamais engendré, n'a pas été engendré. Et nul n'est égal à Lui. / Dis : Je cherche protection auprès du Seigneur de l'aube naissante. / Dis : Je cherche protection auprès du Seigneur des hommes.",
        'tr': "De ki: O Allah'tır, bir tektir. Allah Samed'dir. Doğurmamış ve doğmamıştır. Hiçbir şey O'nun dengi değildir. / De ki: Sabahın Rabbine sığınırım. / De ki: İnsanların Rabbine sığınırım.",
        'hi': "कहो: वह अल्लाह एक है। अल्लाह निराधार है। न उसने जन्म दिया न वह जन्मा। और कोई उसकी बराबरी का नहीं। / कहो: मैं सुबह के रब की शरण लेता हूँ। / कहो: मैं लोगों के रब की शरण लेता हूँ।",
    },
    8: {
        'name_fr': "Refuge dans le Seigneur de l'aube", 'name_tr': "Felak Suresi", 'name_hi': "सूरह फ़लक़",
        'fr': "Dis : Je cherche protection auprès du Seigneur de l'aube naissante, contre le mal de ce qu'Il a créé.",
        'tr': "De ki: Yarattığı şeylerin şerrinden, sabahın Rabbine sığınırım.",
        'hi': "कहो: मैं सुबह के रब की शरण लेता हूँ, उसकी सृष्टि की बुराई से।",
    },
    9: {
        'name_fr': "Refuge dans le Seigneur des hommes", 'name_tr': "Nas Suresi", 'name_hi': "सूरह नास",
        'fr': "Dis : Je cherche protection auprès du Seigneur des hommes, le Souverain des hommes, le Dieu des hommes.",
        'tr': "De ki: İnsanların Rabbine, insanların Melikine, insanların İlahına sığınırım.",
        'hi': "कहो: मैं लोगों के रब, लोगों के बादशाह, लोगों के माबूद की शरण लेता हूँ।",
    },
    11: {
        'name_fr': "Prière sur le Prophète", 'name_tr': "Salavat", 'name_hi': "नबी पर दुरूद",
        'fr': "Ô Allah, envoie Tes prières, Ta paix et Tes bénédictions sur notre Prophète Muhammad.",
        'tr': "Allah'ım! Peygamberimiz Muhammed'e salat, selam ve bereket ihsan eyle.",
        'hi': "ऐ अल्लाह! हमारे नबी मुहम्मद पर दुरूद, सलाम और बरकत भेज।",
    },
    13: {
        'name_fr': "Témoignage de foi du matin", 'name_tr': "Sabah Şehadet", 'name_hi': "सुबह की शहादत",
        'fr': "Je témoigne ce matin que si Tu as révélé à Jésus un esprit de Toi et une preuve manifeste.",
        'tr': "Sabahleyin şehadet ederim ki İsa'ya Senden bir ruh ve açık bir delil indirdin.",
        'hi': "मैं सुबह गवाही देता हूँ कि तूने ईसा को अपनी ओर से एक रूह और स्पष्ट प्रमाण दिया।",
    },
    14: {
        'name_fr': "Prière pour la santé et le bien-être", 'name_tr': "Sağlık ve Afiyet Duası", 'name_hi': "स्वास्थ्य और कुशलता की दुआ",
        'fr': "Ô Allah, je Te demande le pardon et le bien-être dans ce monde et dans l'au-delà.",
        'tr': "Allah'ım! Dünyada ve ahirette Senden af ve afiyet dilerim.",
        'hi': "ऐ अल्लाह! मैं तुझसे इस दुनिया और आख़िरत में माफ़ी और आफ़ियत माँगता हूँ।",
    },
    15: {
        'name_fr': "Gratitude et contentement", 'name_tr': "Şükür ve Rıza", 'name_hi': "कृतज्ञता और संतोष",
        'fr': "Je suis satisfait d'Allah comme Seigneur, de l'Islam comme religion et de Muhammad comme Prophète.",
        'tr': "Rab olarak Allah'tan, din olarak İslam'dan, peygamber olarak Muhammed'den razı oldum.",
        'hi': "मैं अल्लाह को रब, इस्लाम को दीन और मुहम्मद को नबी मानकर राज़ी हूँ।",
    },
    17: {
        'name_fr': "Istighfar du soir", 'name_tr': "Akşam Seyyidul İstiğfar", 'name_hi': "शाम का सय्यिदुल इस्तिग़फ़ार",
        'fr': "Ô Allah, Tu es mon Seigneur, il n'y a de divinité que Toi. Tu m'as créé et je suis Ton serviteur. Pardonne-moi, car nul ne pardonne les péchés si ce n'est Toi.",
        'tr': "Allah'ım! Sen benim Rabbimsin. Senden başka ilah yoktur. Beni Sen yarattın. Beni bağışla. Çünkü günahları ancak Sen bağışlarsın.",
        'hi': "ऐ अल्लाह! तू मेरा रब है, तेरे सिवा कोई माबूद नहीं। तूने मुझे पैदा किया। मुझे माफ़ कर दे, क्योंकि तेरे सिवा गुनाहों को कोई माफ़ नहीं करता।",
    },
    18: {
        'name_fr': "Ayat al-Kursi du soir", 'name_tr': "Akşam Ayetel Kürsi", 'name_hi': "शाम की आयतुल कुर्सी",
        'fr': "Allah! Point de divinité à part Lui, le Vivant, Celui qui subsiste par Lui-même.",
        'tr': "Allah, O'ndan başka ilah yoktur. Hayy'dır, Kayyum'dur.",
        'hi': "अल्लाह, उसके सिवा कोई माबूद नहीं, वह सदा जीवित, सबका संभालने वाला है।",
    },
    19: {
        'name_fr': "Tasbih du soir", 'name_tr': "Akşam Tesbihi", 'name_hi': "शाम की तस्बीह",
        'fr': "Gloire et louange à Allah.",
        'tr': "Allah'ı tesbih eder ve O'na hamd ederim.",
        'hi': "अल्लाह पाक है और उसी की प्रशंसा है।",
    },
    20: {
        'name_fr': "Trois Qul du soir", 'name_tr': "Akşam Uc Kul", 'name_hi': "शाम की तीन क़ुल",
        'fr': "Dis : Il est Allah, Unique. / Dis : Je cherche protection auprès du Seigneur de l'aube. / Dis : Je cherche protection auprès du Seigneur des hommes.",
        'tr': "De ki: O Allah'tır, bir tektir. / De ki: Sabahın Rabbine sığınırım. / De ki: İnsanların Rabbine sığınırım.",
        'hi': "कहो: वह अल्लाह एक है। / कहो: मैं सुबह के रब की शरण लेता हूँ। / कहो: मैं लोगों के रब की शरण लेता हूँ।",
    },
    23: {
        'name_fr': "Protection contre le châtiment", 'name_tr': "Azaptan Korunma", 'name_hi': "अज़ाब से सुरक्षा",
        'fr': "Ô Allah, je cherche refuge auprès de Toi contre le châtiment de la tombe et le châtiment de l'Enfer.",
        'tr': "Allah'ım! Kabir azabından, cehennem azabından Sana sığınırım.",
        'hi': "ऐ अल्लाह! मैं क़ब्र के अज़ाब और जहन्नम के अज़ाब से तेरी शरण चाहता हूँ।",
    },
    24: {
        'name_fr': "La ilaha illallah du soir", 'name_tr': "Akşam Tevhid", 'name_hi': "शाम का तौहीद",
        'fr': "Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé. À Lui la royauté et la louange.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है। बादशाहत और प्रशंसा उसकी है।",
    },
    25: {
        'name_fr': "Tawakkul du soir", 'name_tr': "Akşam Tevekkül", 'name_hi': "शाम का तवक्कुल",
        'fr': "Allah me suffit. Nulle divinité n'est digne d'adoration sauf Lui. Je place ma confiance en Lui.",
        'tr': "Allah bana yeter. O'ndan başka ilah yoktur. O'na tevekkül ettim.",
        'hi': "अल्लाह मुझे काफ़ी है। उसके सिवा कोई माबूद नहीं। उसी पर मैंने भरोसा किया।",
    },
    26: {
        'name_fr': "Bien de la nuit", 'name_tr': "Gecenin Hayrı", 'name_hi': "रात की भलाई की दुआ",
        'fr': "Ô Allah, je Te demande le bien de cette nuit et le bien qu'elle contient.",
        'tr': "Allah'ım! Bu gecenin hayrını ve içindeki hayrı Senden isterim.",
        'hi': "ऐ अल्लाह! मैं इस रात की भलाई और इसमें जो भलाई है वह माँगता हूँ।",
    },
    27: {
        'name_fr': "Prière pour les parents", 'name_tr': "Anne-Baba Duası", 'name_hi': "माता-पिता की दुआ",
        'fr': "Mon Seigneur, pardonne-moi ainsi qu'à mes parents et fais-leur miséricorde comme ils m'ont élevé tout petit.",
        'tr': "Rabbim! Beni ve anne-babamı bağışla. Küçükken beni yetiştirdikleri gibi onlara merhamet et.",
        'hi': "ऐ मेरे रब! मुझे और मेरे माता-पिता को माफ़ कर दे और उन पर रहम कर जैसे उन्होंने मुझे बचपन में पाला।",
    },
    29: {
        'name_fr': "Protection de la famille", 'name_tr': "Aile Korunma Duası", 'name_hi': "परिवार की सुरक्षा",
        'fr': "Ô Allah, protège-moi de devant et de derrière, de ma droite et de ma gauche.",
        'tr': "Allah'ım! Önümden, arkamdan, sağımdan, solumdan beni koru.",
        'hi': "ऐ अल्लाह! मुझे मेरे आगे, पीछे, दाएँ, बाएँ से बचा।",
    },
    30: {
        'name_fr': "Prière sur le Prophète (soir)", 'name_tr': "Akşam Salavat", 'name_hi': "शाम का दुरूद",
        'fr': "Ô Allah, envoie Tes prières, Ta paix et Tes bénédictions sur notre Prophète Muhammad.",
        'tr': "Allah'ım! Peygamberimiz Muhammed'e salat, selam ve bereket ihsan eyle.",
        'hi': "ऐ अल्लाह! हमारे नबी मुहम्मद पर दुरूद, सलाम और बरकत भेज।",
    },
    31: {
        'name_fr': "Istighfar après la prière", 'name_tr': "Namaz Sonrası İstiğfar", 'name_hi': "नमाज़ के बाद इस्तिग़फ़ार",
        'fr': "Je demande pardon à Allah.",
        'tr': "Allah'tan bağışlanma dilerim.",
        'hi': "मैं अल्लाह से माफ़ी माँगता हूँ।",
    },
    32: {
        'name_fr': "Allahumma Antas-Salam", 'name_tr': "Allahumme Entes-Selam", 'name_hi': "अल्लाहुम्मा अंतस्सलाम",
        'fr': "Ô Allah, Tu es la Paix et de Toi vient la paix. Béni sois-Tu, ô Détenteur de la Majesté et de la Générosité.",
        'tr': "Allah'ım! Sen Selam'sın ve selamet Sendendir. Ey celal ve ikram sahibi, Sen ne yücesin!",
        'hi': "ऐ अल्लाह! तू ही सलाम है और तुझी से शांति है। ऐ जलाल और इकराम वाले, तू बरकत वाला है।",
    },
    33: {
        'name_fr': "Subhanallah après la prière", 'name_tr': "Namaz Sonrası Sübhanallah", 'name_hi': "नमाज़ के बाद सुब्हानल्लाह",
        'fr': "Gloire à Allah.", 'tr': "Sübhanallah.", 'hi': "सुब्हानल्लाह।",
    },
    34: {
        'name_fr': "Alhamdulillah après la prière", 'name_tr': "Namaz Sonrası Elhamdülillah", 'name_hi': "नमाज़ के बाद अल्हम्दुलिल्लाह",
        'fr': "Louange à Allah.", 'tr': "Elhamdülillah.", 'hi': "अल्हम्दुलिल्लाह।",
    },
    35: {
        'name_fr': "Allahu Akbar après la prière", 'name_tr': "Namaz Sonrası Allahu Ekber", 'name_hi': "नमाज़ के बाद अल्लाहु अकबर",
        'fr': "Allah est le Plus Grand.", 'tr': "Allahu Ekber.", 'hi': "अल्लाहु अकबर।",
    },
    37: {
        'name_fr': "Prière pour la guidance", 'name_tr': "Hidayet Duası", 'name_hi': "हिदायत की दुआ",
        'fr': "Ô Allah, aide-moi à Te rappeler, à Te remercier et à T'adorer de la meilleure façon.",
        'tr': "Allah'ım! Seni zikretmem, Sana şükretmem ve güzel ibadet etmem konusunda bana yardım et.",
        'hi': "ऐ अल्लाह! मुझे तेरा ज़िक्र करने, तेरा शुक्र करने और अच्छी इबादत करने में मदद कर।",
    },
    38: {
        'name_fr': "Ayat al-Kursi après la prière", 'name_tr': "Namaz Sonrası Ayetel Kürsi", 'name_hi': "नमाज़ के बाद आयतुल कुर्सी",
        'fr': "Allah! Point de divinité à part Lui, le Vivant, Celui qui subsiste par Lui-même.",
        'tr': "Allah, O'ndan başka ilah yoktur. Hayy'dır, Kayyum'dur.",
        'hi': "अल्लाह, उसके सिवा कोई माबूद नहीं, वह सदा जीवित, सबका संभालने वाला है।",
    },
    39: {
        'name_fr': "Protection contre quatre choses", 'name_tr': "Dort Şeyden Korunma", 'name_hi': "चार चीज़ों से सुरक्षा",
        'fr': "Ô Allah, je cherche refuge auprès de Toi contre la lâcheté, l'avarice, la mauvaise vieillesse et le châtiment de la tombe.",
        'tr': "Allah'ım! Korkaklıktan, cimrilikten, kötü yaşlılıktan ve kabir azabından Sana sığınırım.",
        'hi': "ऐ अल्लाह! मैं कायरता, कंजूसी, बुरे बुढ़ापे और क़ब्र के अज़ाब से तेरी शरण चाहता हूँ।",
    },
    40: {
        'name_fr': "Prière pour le Paradis", 'name_tr': "Cennet Duası", 'name_hi': "जन्नत की दुआ",
        'fr': "Ô Allah, je Te demande le Paradis et je cherche refuge auprès de Toi contre l'Enfer.",
        'tr': "Allah'ım! Senden cenneti ister, cehennemden Sana sığınırım.",
        'hi': "ऐ अल्लाह! मैं तुझसे जन्नत माँगता हूँ और जहन्नम से तेरी शरण चाहता हूँ।",
    },
    41: {
        'name_fr': "Invocation du sommeil", 'name_tr': "Uyku Duası", 'name_hi': "सोने की दुआ",
        'fr': "En Ton nom, ô Allah, je meurs et je vis.",
        'tr': "Senin adınla Allah'ım, ölür ve dirilirim.",
        'hi': "तेरे नाम से, ऐ अल्लाह, मैं मरता और जीता हूँ।",
    },
    42: {
        'name_fr': "Récitation des trois Qul", 'name_tr': "Uc Kul Okumak", 'name_hi': "तीन क़ुल पढ़ना",
        'fr': "Dis : Il est Allah, Unique. / Dis : Je cherche protection auprès du Seigneur de l'aube. / Dis : Je cherche protection auprès du Seigneur des hommes.",
        'tr': "De ki: O Allah'tır, bir tektir. / De ki: Sabahın Rabbine sığınırım. / De ki: İnsanların Rabbine sığınırım.",
        'hi': "कहो: वह अल्लाह एक है। / कहो: मैं सुबह के रब की शरण लेता हूँ। / कहो: मैं लोगों के रब की शरण लेता हूँ।",
    },
    43: {
        'name_fr': "Prière avant le sommeil", 'name_tr': "Uyku Oncesi Dua", 'name_hi': "सोने से पहले दुआ",
        'fr': "Ô Allah, je soumets mon âme à Toi, je confie mes affaires à Toi, je tourne mon visage vers Toi.",
        'tr': "Allah'ım! Nefsimi Sana teslim ettim, işimi Sana havale ettim, yüzümü Sana çevirdim.",
        'hi': "ऐ अल्लाह! मैंने अपनी जान तुझे सौंपी, अपना मामला तुझे सौंपा, अपना चेहरा तेरी ओर फेरा।",
    },
    44: {
        'name_fr': "Tasbih de Fatimah", 'name_tr': "Fatıma Tesbihi", 'name_hi': "फ़ातिमा की तस्बीह",
        'fr': "Gloire à Allah (33 fois), Louange à Allah (33 fois), Allah est le Plus Grand (34 fois).",
        'tr': "Sübhanallah (33), Elhamdülillah (33), Allahu Ekber (34).",
        'hi': "सुब्हानल्लाह (33), अल्हम्दुलिल्लाह (33), अल्लाहु अकबर (34)।",
    },
    45: {
        'name_fr': "Deux derniers versets d'Al-Baqarah", 'name_tr': "Bakara'nın Son İki Ayeti", 'name_hi': "सूरह बक़रह की आख़िरी दो आयतें",
        'fr': "Le Messager a cru en ce qui lui a été révélé de la part de son Seigneur, ainsi que les croyants.",
        'tr': "Peygamber, Rabbinden kendisine indirilene iman etti, müminler de.",
        'hi': "रसूल ने उस पर ईमान लाया जो उसके रब की ओर से उतारा गया, और मोमिनों ने भी।",
    },
    47: {
        'name_fr': "Prière pour de bons rêves", 'name_tr': "Güzel Rüya Duası", 'name_hi': "अच्छे सपनों की दुआ",
        'fr': "Ô Allah, je cherche refuge auprès de Toi contre le diable maudit et contre le mal de toute chose.",
        'tr': "Allah'ım! Lanetlenmiş şeytandan ve her şeyin şerrinden Sana sığınırım.",
        'hi': "ऐ अल्लाह! मैं शापित शैतान और हर चीज़ की बुराई से तेरी शरण चाहता हूँ।",
    },
    48: {
        'name_fr': "Récitation d'Al-Mulk", 'name_tr': "Mülk Suresi Okumak", 'name_hi': "सूरह मुल्क पढ़ना",
        'fr': "Béni soit Celui dans la main de qui est la royauté, et Il est Omnipotent.",
        'tr': "Mülk elinde olan ne yücedir! O, her şeye kadirdir.",
        'hi': "बरकत वाला है वह जिसके हाथ में बादशाहत है और वह हर चीज़ पर सामर्थ्यवान है।",
    },
    49: {
        'name_fr': "Invocation du réveil", 'name_tr': "Uyanma Duası", 'name_hi': "जागने की दुआ",
        'fr': "Louange à Allah qui nous a redonné la vie après nous avoir fait mourir et vers Lui est la résurrection.",
        'tr': "Bizi öldürdükten sonra dirilten Allah'a hamd olsun. Dönüş O'nadır.",
        'hi': "सारी प्रशंसा अल्लाह के लिए है जिसने हमें मृत्यु के बाद जीवन दिया।",
    },
    50: {
        'name_fr': "Essuyer le visage et réciter", 'name_tr': "Yüzü Silme ve Okuma", 'name_hi': "चेहरा पोंछना और पढ़ना",
        'fr': "Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है।",
    },
    51: {
        'name_fr': "Prière en entrant aux toilettes", 'name_tr': "Tuvalete Giris Duası", 'name_hi': "शौचालय जाने की दुआ",
        'fr': "Au nom d'Allah. Ô Allah, je cherche refuge auprès de Toi contre les démons mâles et femelles.",
        'tr': "Allah'ın adıyla. Allah'ım! Erkek ve dişi şeytanlardan Sana sığınırım.",
        'hi': "अल्लाह के नाम से। ऐ अल्लाह! मैं नर और मादा शैतानों से तेरी शरण चाहता हूँ।",
    },
    52: {
        'name_fr': "Prière en sortant des toilettes", 'name_tr': "Tuvaletten Cıkıs Duası", 'name_hi': "शौचालय से निकलने की दुआ",
        'fr': "Je Te demande pardon.", 'tr': "Bağışlamanı dilerim.", 'hi': "मैं तेरी माफ़ी चाहता हूँ।",
    },
    53: {
        'name_fr': "Prière pour commencer la journée", 'name_tr': "Güne Başlama Duası", 'name_hi': "दिन शुरू करने की दुआ",
        'fr': "Ô Allah, par Toi nous entrons dans le matin et par Toi nous entrons dans le soir.",
        'tr': "Allah'ım! Senin sayende sabaha erdik, Senin sayende akşama erdik.",
        'hi': "ऐ अल्लाह! तेरी कृपा से हम सुबह करते हैं और तेरी कृपा से शाम करते हैं।",
    },
    54: {
        'name_fr': "Prière pour entrer à la maison", 'name_tr': "Eve Giris Duası", 'name_hi': "घर में प्रवेश की दुआ",
        'fr': "Ô Allah, je Te demande le bien de l'entrée et le bien de la sortie. Au nom d'Allah nous entrons.",
        'tr': "Allah'ım! Girişin hayrını ve çıkışın hayrını Senden isterim. Allah'ın adıyla gireriz.",
        'hi': "ऐ अल्लाह! मैं तुझसे प्रवेश और निकास की भलाई माँगता हूँ। अल्लाह के नाम से हम प्रवेश करते हैं।",
    },
    55: {
        'name_fr': "Prière pour quitter la maison", 'name_tr': "Evden Cıkıs Duası", 'name_hi': "घर से निकलने की दुआ",
        'fr': "Au nom d'Allah, je place ma confiance en Allah. Il n'y a de force ni de puissance qu'en Allah.",
        'tr': "Allah'ın adıyla, Allah'a tevekkül ettim. Güç ve kuvvet ancak Allah'tandır.",
        'hi': "अल्लाह के नाम से, मैंने अल्लाह पर भरोसा किया। शक्ति और ताक़त केवल अल्लाह से है।",
    },
    56: {
        'name_fr': "Avant de manger", 'name_tr': "Yemek Öncesi", 'name_hi': "खाने से पहले",
        'fr': "Au nom d'Allah.", 'tr': "Bismillah.", 'hi': "अल्लाह के नाम से।",
    },
    57: {
        'name_fr': "Après avoir mangé", 'name_tr': "Yemek Sonrası", 'name_hi': "खाने के बाद",
        'fr': "Louange à Allah qui nous a nourris et abreuvés et nous a faits musulmans.",
        'tr': "Bizi yediren, içiren ve Müslüman kılan Allah'a hamd olsun.",
        'hi': "सारी प्रशंसा अल्लाह के लिए है जिसने हमें खिलाया, पिलाया और मुसलमान बनाया।",
    },
    58: {
        'name_fr': "Entrer dans la mosquée", 'name_tr': "Mescide Giris Duası", 'name_hi': "मस्जिद में प्रवेश की दुआ",
        'fr': "Ô Allah, ouvre-moi les portes de Ta miséricorde.",
        'tr': "Allah'ım! Rahmetinin kapılarını bana aç.",
        'hi': "ऐ अल्लाह! मेरे लिए अपनी रहमत के दरवाज़े खोल दे।",
    },
    59: {
        'name_fr': "Sortir de la mosquée", 'name_tr': "Mescidden Cıkıs Duası", 'name_hi': "मस्जिद से निकलने की दुआ",
        'fr': "Ô Allah, je Te demande de Ta grâce.",
        'tr': "Allah'ım! Senden fazlını isterim.",
        'hi': "ऐ अल्लाह! मैं तुझसे तेरा फ़ज़्ल माँगता हूँ।",
    },
    60: {
        'name_fr': "Prière de Yunus dans la détresse", 'name_tr': "Yunus Duası", 'name_hi': "यूनुस की दुआ",
        'fr': "Point de divinité à part Toi! Gloire à Toi! J'étais certes du nombre des injustes.",
        'tr': "Senden başka ilah yoktur! Seni tenzih ederim! Ben zalimlerden oldum.",
        'hi': "तेरे सिवा कोई माबूद नहीं! तू पाक है! निस्संदेह मैं ज़ालिमों में से था।",
    },
    61: {
        'name_fr': "Prière pour l'anxiété et le chagrin", 'name_tr': "Kaygı ve Üzüntü Duası", 'name_hi': "चिंता और दुख की दुआ",
        'fr': "Ô Allah, je suis Ton serviteur, fils de Ton serviteur. Mon sort est entre Tes mains.",
        'tr': "Allah'ım! Ben Senin kulunum, kulunun oğluyum. Alın saçım Senin elindedir.",
        'hi': "ऐ अल्लाह! मैं तेरा बंदा हूँ, तेरे बंदे का बेटा हूँ। मेरी पेशानी तेरे हाथ में है।",
    },
    62: {
        'name_fr': "Prière en montant dans un véhicule", 'name_tr': "Araca Biniş Duası", 'name_hi': "वाहन पर सवार होने की दुआ",
        'fr': "Gloire à Celui qui a mis ceci à notre service et nous n'étions pas capables de le faire.",
        'tr': "Bunu bizim hizmetimize veren Allah'ın şanı yücedir. Yoksa biz buna güç yetiremezdik.",
        'hi': "पाक है वह जिसने इसे हमारे अधीन किया और हम इसकी ताक़त नहीं रखते थे।",
    },
    63: {
        'name_fr': "Prière de consultation (Istikhara)", 'name_tr': "İstihare Duası", 'name_hi': "इस्तिख़ारा की दुआ",
        'fr': "Ô Allah, je Te consulte par Ta science et je Te demande de me donner le pouvoir par Ta puissance.",
        'tr': "Allah'ım! İlminle Senden hayır dilerim, kudretinle Senden güç isterim.",
        'hi': "ऐ अल्लाह! मैं तेरे ज्ञान से तुझसे ख़ैर माँगता हूँ और तेरी क़ुदरत से ताक़त माँगता हूँ।",
    },
    64: {
        'name_fr': "Quand il pleut", 'name_tr': "Yağmur Duası", 'name_hi': "बारिश की दुआ",
        'fr': "Ô Allah, (accorde-nous) une pluie bénéfique.",
        'tr': "Allah'ım! Faydalı yağmur ver.",
        'hi': "ऐ अल्लाह! लाभदायक बारिश दे।",
    },
    65: {
        'name_fr': "En entendant le tonnerre", 'name_tr': "Gök Gürültüsü Duası", 'name_hi': "गरज सुनने पर",
        'fr': "Gloire à Celui que le tonnerre glorifie par Sa louange, ainsi que les anges par crainte de Lui.",
        'tr': "Gök gürültüsü O'nu hamd ile, melekler de O'nun korkusundan tesbih eder.",
        'hi': "पाक है वह जिसकी तस्बीह गरज उसकी प्रशंसा के साथ करती है और फ़रिश्ते उसके डर से।",
    },
    66: {
        'name_fr': "En éternuant", 'name_tr': "Hapşırma Duası", 'name_hi': "छींकने की दुआ",
        'fr': "Louange à Allah.", 'tr': "Elhamdülillah.", 'hi': "अल्हम्दुलिल्लाह।",
    },
    67: {
        'name_fr': "En visitant un malade", 'name_tr': "Hasta Ziyareti Duası", 'name_hi': "बीमार से मिलने की दुआ",
        'fr': "Ne t'inquiète pas, c'est une purification si Allah le veut.",
        'tr': "Endişelenme, inşaallah temizliktir (günahlara kefaret).",
        'hi': "चिंता मत करो, इंशाअल्लाह यह (बीमारी) पवित्रता (गुनाहों का कफ़्फ़ारा) है।",
    },
    68: {
        'name_fr': "Prière pour le malade", 'name_tr': "Hasta İçin Dua", 'name_hi': "बीमार के लिए दुआ",
        'fr': "Ô Allah, Seigneur des hommes, fais disparaître le mal et guéris-le, car Tu es le Guérisseur.",
        'tr': "Allah'ım! İnsanların Rabbi, sıkıntıyı gider, şifa ver. Şifa veren ancak Sensin.",
        'hi': "ऐ अल्लाह! लोगों के रब! तकलीफ़ दूर कर और शिफ़ा दे, तू ही शिफ़ा देने वाला है।",
    },
    69: {
        'name_fr': "En voyant quelqu'un éprouvé", 'name_tr': "Musibete Uğrayanı Görünce", 'name_hi': "किसी को मुसीबत में देखने पर",
        'fr': "Louange à Allah qui m'a épargné ce dont Il t'a éprouvé et m'a favorisé sur beaucoup de Ses créatures.",
        'tr': "Seni imtihan ettiği şeyden beni koruyan ve yarattıklarının çoğundan beni üstün kılan Allah'a hamd olsun.",
        'hi': "प्रशंसा अल्लाह की है जिसने मुझे उससे बचाया जिससे तुझे आज़माया और मुझे अपनी बहुत सी मख़लूक़ पर फ़ज़ीलत दी।",
    },
    70: {
        'name_fr': "Quand quelque chose plaît", 'name_tr': "Hoşa Giden Şeyde", 'name_hi': "कुछ अच्छा होने पर",
        'fr': "Louange à Allah par la grâce de qui les bonnes choses se réalisent.",
        'tr': "Nimetiyle iyi işlerin tamamlandığı Allah'a hamd olsun.",
        'hi': "प्रशंसा अल्लाह की है जिसकी कृपा से अच्छे काम पूरे होते हैं।",
    },
    71: {
        'name_fr': "Quand quelque chose déplaît", 'name_tr': "Hoşa Gitmeyen Şeyde", 'name_hi': "कुछ बुरा होने पर",
        'fr': "Louange à Allah en toutes circonstances.",
        'tr': "Her durumda Allah'a hamd olsun.",
        'hi': "हर हाल में अल्लाह की प्रशंसा है।",
    },
    72: {
        'name_fr': "Prière pour le remboursement de dette", 'name_tr': "Borç Duası", 'name_hi': "क़र्ज़ उतारने की दुआ",
        'fr': "Ô Allah, accorde-moi suffisamment de ce que Tu as rendu licite pour me passer de ce qui est illicite.",
        'tr': "Allah'ım! Helalinle bana yetecek kadar ver ki haramına muhtaç olmayayım.",
        'hi': "ऐ अल्लाह! मुझे अपने हलाल से इतना दे कि मुझे हराम की ज़रूरत न पड़े।",
    },
    73: {
        'name_fr': "Prière pour entrer au marché", 'name_tr': "Çarşıya Giriş Duası", 'name_hi': "बाज़ार जाने की दुआ",
        'fr': "Nulle divinité n'est digne d'adoration sauf Allah, Seul sans associé. À Lui la royauté et la louange.",
        'tr': "Allah'tan başka ilah yoktur, tektir, ortağı yoktur. Mülk O'nundur, hamd O'nadır.",
        'hi': "अल्लाह के सिवा कोई माबूद नहीं, वह अकेला है। बादशाहत और प्रशंसा उसकी है।",
    },
    74: {
        'name_fr': "Al-Fatihah pour la guidance", 'name_tr': "Fatiha ile Hidayet", 'name_hi': "अल-फ़ातिहा से हिदायत",
        'fr': "Guide-nous dans le droit chemin, le chemin de ceux que Tu as comblés de faveurs.",
        'tr': "Bizi doğru yola ilet. Nimet verdiklerinin yoluna.",
        'hi': "हमें सीधा रास्ता दिखा। उन लोगों का रास्ता जिन पर तूने इनाम किया।",
    },
    75: {
        'name_fr': "Prière pour les deux mondes", 'name_tr': "İki Dünya Duası", 'name_hi': "दोनों जहान की दुआ",
        'fr': "Notre Seigneur, accorde-nous une belle part dans ce monde et une belle part dans l'au-delà.",
        'tr': "Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver.",
        'hi': "ऐ हमारे रब! हमें दुनिया में भी भलाई दे और आख़िरत में भी भलाई दे।",
    },
    76: {
        'name_fr': "Prière pour le pardon et la miséricorde", 'name_tr': "Bağışlanma ve Merhamet Duası", 'name_hi': "माफ़ी और रहमत की दुआ",
        'fr': "Notre Seigneur, nous nous sommes fait du tort à nous-mêmes. Si Tu ne nous pardonnes pas, nous serons perdus.",
        'tr': "Rabbimiz! Kendimize zulmettik. Bizi bağışlamazsan hüsrana uğrayanlardan oluruz.",
        'hi': "ऐ हमारे रब! हमने अपने ऊपर ज़ुल्म किया। अगर तू हमें माफ़ न करे तो हम घाटे वालों में होंगे।",
    },
    77: {
        'name_fr': "Prière d'Ibrahim pour la famille", 'name_tr': "İbrahim'in Aile Duası", 'name_hi': "इब्राहीम की परिवार की दुआ",
        'fr': "Mon Seigneur, fais que j'accomplisse la prière et parmi ma descendance aussi.",
        'tr': "Rabbim! Beni namazı dosdoğru kılanlardan eyle, soyumdan da.",
        'hi': "ऐ मेरे रब! मुझे नमाज़ क़ायम करने वाला बना और मेरी औलाद को भी।",
    },
    78: {
        'name_fr': "Prière pour la patience", 'name_tr': "Sabır Duası", 'name_hi': "सब्र की दुआ",
        'fr': "Notre Seigneur, déverse sur nous la patience, affermis nos pas et donne-nous la victoire.",
        'tr': "Rabbimiz! Üzerimize sabır yağdır, ayaklarımızı sabit kıl ve bize zafer ver.",
        'hi': "ऐ हमारे रब! हम पर सब्र उंडेल दे, हमारे क़दम जमा दे और हमें फ़तह दे।",
    },
    79: {
        'name_fr': "Prière pour le bon caractère", 'name_tr': "İyi Karakter Duası", 'name_hi': "अच्छे चरित्र की दुआ",
        'fr': "Notre Seigneur, fais que nos épouses et descendants soient la joie de nos yeux.",
        'tr': "Rabbimiz! Eşlerimizden ve çocuklarımızdan gözümüzün aydınlığını bize bağışla.",
        'hi': "ऐ हमारे रब! हमें हमारी बीवियों और औलाद से आँखों की ठंडक दे।",
    },
    80: {
        'name_fr': "Prière de Moussa pour l'aide", 'name_tr': "Musa'nın Yardım Duası", 'name_hi': "मूसा की मदद की दुआ",
        'fr': "Mon Seigneur, j'ai grand besoin de tout bien que Tu feras descendre vers moi.",
        'tr': "Rabbim! Bana indireceğin her hayra muhtacım.",
        'hi': "ऐ मेरे रब! तू मुझ पर जो भी भलाई उतारे, मैं उसका मोहताज हूँ।",
    },
    81: {
        'name_fr': "Prière pour un cœur ferme", 'name_tr': "Kalp Sebatı Duası", 'name_hi': "दिल की मज़बूती की दुआ",
        'fr': "Notre Seigneur, ne fais pas dévier nos cœurs après nous avoir guidés.",
        'tr': "Rabbimiz! Bizi hidayete erdirdikten sonra kalplerimizi eğriltme.",
        'hi': "ऐ हमारे रब! हमें हिदायत के बाद हमारे दिलों को न फेर।",
    },
    82: {
        'name_fr': "Prière d'Ayyub pour la guérison", 'name_tr': "Eyyüb'ün Şifa Duası", 'name_hi': "अय्यूब की शिफ़ा की दुआ",
        'fr': "Le mal m'a touché et Tu es le Plus Miséricordieux.",
        'tr': "Başıma bela geldi. Sen merhametlilerin en merhametlisisin.",
        'hi': "मुझे तकलीफ़ पहुँची है और तू सबसे ज़्यादा रहम करने वाला है।",
    },
    83: {
        'name_fr': "Prière pour la miséricorde à la mort", 'name_tr': "Ölümde Merhamet Duası", 'name_hi': "मृत्यु पर रहमत की दुआ",
        'fr': "Notre Seigneur, ne nous blâme pas si nous oublions ou si nous commettons une erreur.",
        'tr': "Rabbimiz! Unutur ya da hata edersek bizi sorumlu tutma.",
        'hi': "ऐ हमारे रब! अगर हम भूलें या ग़लती करें तो हमें पकड़ मत।",
    },
}

print(f'Updating {len(TRANSLATIONS)} adhkar...')
count = 0
for db_id, vals in TRANSLATIONS.items():
    try:
        data = {}
        for k, v in vals.items():
            if k.startswith('name_'):
                data[k] = v
            elif k in ('fr', 'tr', 'hi'):
                data[f'translation_{k}'] = v
        w([db_id], data)
        count += 1
    except Exception as e:
        print(f'  Error ID {db_id}: {e}')

print(f'DONE: {count} adhkar updated')
