import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicSurah(models.Model):
    _name = 'islamic.surah'
    _description = 'Quran Surah'
    _order = 'number'

    name = fields.Char(string='Surah Name (English)', required=True)
    name_arabic = fields.Char(string='Surah Name (Arabic)', required=True)
    name_french = fields.Char(string='Surah Name (French)')
    name_turkish = fields.Char(string='Surah Name (Turkish)')
    name_hindi = fields.Char(string='Surah Name (Hindi)')
    number = fields.Integer(string='Surah Number', required=True)
    total_ayahs = fields.Integer(string='Total Ayahs', required=True)
    revelation_type = fields.Selection([
        ('meccan', 'Meccan'),
        ('medinan', 'Medinan'),
    ], string='Revelation Type', required=True)
    juz_start = fields.Integer(string='Starting Juz')
    juz_end = fields.Integer(string='Ending Juz')
    page_start = fields.Integer(string='Starting Page')
    page_end = fields.Integer(string='Ending Page')
    description_en = fields.Text(string='Description (English)')
    description_ar = fields.Text(string='Description (Arabic)')
    description_fr = fields.Text(string='Description (French)')
    description_tr = fields.Text(string='Description (Turkish)')
    description_hi = fields.Text(string='Description (Hindi)')
    bismillah_pre = fields.Boolean(string='Has Bismillah', default=True)
    ayah_ids = fields.One2many('islamic.ayah', 'surah_id', string='Ayahs')
    audio_ids = fields.One2many('islamic.audio', 'surah_id', string='Audio Recitations')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('number_unique', 'UNIQUE(number)', 'Surah number must be unique!'),
    ]

    def get_name_by_lang(self, lang_code='en'):
        """Get surah name in specified language"""
        self.ensure_one()
        lang_map = {
            'en': self.name,
            'ar': self.name_arabic,
            'fr': self.name_french or self.name,
            'tr': self.name_turkish or self.name,
            'hi': self.name_hindi or self.name,
        }
        return lang_map.get(lang_code, self.name)

    def to_dict(self, lang='en'):
        """Serialize for API"""
        self.ensure_one()
        return {
            'id': self.id,
            'number': self.number,
            'name': self.get_name_by_lang(lang),
            'name_arabic': self.name_arabic,
            'total_ayahs': self.total_ayahs,
            'revelation_type': self.revelation_type,
            'juz_start': self.juz_start,
            'juz_end': self.juz_end,
            'page_start': self.page_start,
            'page_end': self.page_end,
            'has_bismillah': self.bismillah_pre,
        }


class IslamicAyah(models.Model):
    _name = 'islamic.ayah'
    _description = 'Quran Ayah (Verse)'
    _order = 'surah_id, number'

    surah_id = fields.Many2one('islamic.surah', string='Surah', required=True, ondelete='cascade')
    number = fields.Integer(string='Ayah Number', required=True)
    number_in_quran = fields.Integer(string='Ayah Number in Quran')
    text_arabic = fields.Text(string='Arabic Text', required=True)
    text_uthmani = fields.Text(string='Uthmani Script')
    text_simple = fields.Text(string='Simple Arabic Script')

    # Translations
    translation_en = fields.Text(string='English Translation')
    translation_fr = fields.Text(string='French Translation')
    translation_tr = fields.Text(string='Turkish Translation')
    translation_hi = fields.Text(string='Hindi Translation')

    # Transliteration
    transliteration_en = fields.Text(string='English Transliteration')

    # Tafsir (Interpretation)
    tafsir_en = fields.Text(string='Tafsir (English)')
    tafsir_ar = fields.Text(string='Tafsir (Arabic)')
    tafsir_fr = fields.Text(string='Tafsir (French)')
    tafsir_tr = fields.Text(string='Tafsir (Turkish)')
    tafsir_hi = fields.Text(string='Tafsir (Hindi)')

    # Metadata
    juz = fields.Integer(string='Juz Number')
    hizb = fields.Integer(string='Hizb Number')
    page = fields.Integer(string='Page Number')
    ruku = fields.Integer(string='Ruku Number')
    sajda = fields.Boolean(string='Has Sajda', default=False)
    sajda_type = fields.Selection([
        ('recommended', 'Recommended'),
        ('obligatory', 'Obligatory'),
    ], string='Sajda Type')

    # Tajweed
    text_tajweed = fields.Text(string='Tajweed Annotated Text', help='HTML with tajweed color coding')

    # Audio
    audio_url = fields.Char(string='Ayah Audio URL')
    audio_duration = fields.Float(string='Audio Duration (seconds)')

    _sql_constraints = [
        ('ayah_unique', 'UNIQUE(surah_id, number)', 'Ayah number must be unique per Surah!'),
    ]

    def get_translation(self, lang='en'):
        """Get translation in specified language"""
        self.ensure_one()
        lang_map = {
            'en': self.translation_en,
            'ar': self.text_arabic,
            'fr': self.translation_fr or self.translation_en,
            'tr': self.translation_tr or self.translation_en,
            'hi': self.translation_hi or self.translation_en,
        }
        return lang_map.get(lang, self.translation_en)

    def get_tafsir(self, lang='en'):
        """Get tafsir in specified language"""
        self.ensure_one()
        lang_map = {
            'en': self.tafsir_en,
            'ar': self.tafsir_ar,
            'fr': self.tafsir_fr or self.tafsir_en,
            'tr': self.tafsir_tr or self.tafsir_en,
            'hi': self.tafsir_hi or self.tafsir_en,
        }
        return lang_map.get(lang, self.tafsir_en)

    def to_dict(self, lang='en', include_tafsir=False):
        """Serialize for API"""
        self.ensure_one()
        result = {
            'id': self.id,
            'surah_number': self.surah_id.number,
            'ayah_number': self.number,
            'text_arabic': self.text_uthmani or self.text_arabic,
            'translation': self.get_translation(lang),
            'transliteration': self.transliteration_en,
            'juz': self.juz,
            'page': self.page,
            'has_sajda': self.sajda,
            'audio_url': self.audio_url,
        }
        if include_tafsir:
            result['tafsir'] = self.get_tafsir(lang)
        if self.text_tajweed:
            result['tajweed_text'] = self.text_tajweed
        return result


class IslamicContent(models.Model):
    """General Islamic content - daily wisdom, articles, reminders"""
    _name = 'islamic.content'
    _description = 'Islamic Content'
    _order = 'sequence, create_date desc'

    name = fields.Char(string='Title (English)', required=True)
    content_type = fields.Selection([
        ('daily_wisdom', 'Daily Wisdom'),
        ('article', 'Article'),
        ('behavioral_reminder', 'Behavioral Reminder'),
        ('dua', 'Dua (Supplication)'),
        ('hadith', 'Hadith'),
        ('tip', 'Islamic Tip'),
        ('story', 'Story of the Prophets'),
    ], string='Content Type', required=True)
    category_id = fields.Many2one('islamic.content.category', string='Category')

    # Multi-language content
    title_ar = fields.Char(string='Title (Arabic)')
    title_fr = fields.Char(string='Title (French)')
    title_tr = fields.Char(string='Title (Turkish)')
    title_hi = fields.Char(string='Title (Hindi)')

    body_en = fields.Html(string='Body (English)')
    body_ar = fields.Html(string='Body (Arabic)')
    body_fr = fields.Html(string='Body (French)')
    body_tr = fields.Html(string='Body (Turkish)')
    body_hi = fields.Html(string='Body (Hindi)')

    arabic_text = fields.Text(string='Arabic Text (Original)')
    reference = fields.Char(string='Reference (Book/Hadith)')

    # Media
    image = fields.Binary(string='Image')
    image_url = fields.Char(string='Image URL')
    audio_id = fields.Many2one('islamic.audio', string='Related Audio')

    # Publishing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='Status', default='draft')
    published_date = fields.Datetime(string='Published Date')
    author_id = fields.Many2one('islamic.app.user', string='Author')
    sequence = fields.Integer(string='Sequence', default=10)
    is_featured = fields.Boolean(string='Featured', default=False)
    is_daily = fields.Boolean(string='Daily Content', default=False)
    scheduled_date = fields.Date(string='Scheduled Display Date')

    # Engagement
    view_count = fields.Integer(string='View Count', default=0)
    like_count = fields.Integer(string='Like Count', default=0)
    share_count = fields.Integer(string='Share Count', default=0)
    bookmark_count = fields.Integer(string='Bookmark Count', default=0)

    # Tags
    tag_ids = fields.Many2many('islamic.content.tag', string='Tags')

    active = fields.Boolean(default=True)

    def get_title_by_lang(self, lang='en'):
        self.ensure_one()
        lang_map = {
            'en': self.name,
            'ar': self.title_ar or self.name,
            'fr': self.title_fr or self.name,
            'tr': self.title_tr or self.name,
            'hi': self.title_hi or self.name,
        }
        return lang_map.get(lang, self.name)

    def get_body_by_lang(self, lang='en'):
        self.ensure_one()
        lang_map = {
            'en': self.body_en,
            'ar': self.body_ar or self.body_en,
            'fr': self.body_fr or self.body_en,
            'tr': self.body_tr or self.body_en,
            'hi': self.body_hi or self.body_en,
        }
        return lang_map.get(lang, self.body_en)

    def to_dict(self, lang='en'):
        self.ensure_one()
        return {
            'id': self.id,
            'title': self.get_title_by_lang(lang),
            'body': self.get_body_by_lang(lang),
            'arabic_text': self.arabic_text,
            'content_type': self.content_type,
            'reference': self.reference,
            'image_url': self.image_url,
            'audio_id': self.audio_id.id if self.audio_id else None,
            'is_featured': self.is_featured,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'tags': [t.name for t in self.tag_ids],
        }


class IslamicContentCategory(models.Model):
    _name = 'islamic.content.category'
    _description = 'Content Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    name_ar = fields.Char(string='Arabic Name')
    name_fr = fields.Char(string='French Name')
    name_tr = fields.Char(string='Turkish Name')
    name_hi = fields.Char(string='Hindi Name')
    code = fields.Char(string='Code', required=True)
    parent_id = fields.Many2one('islamic.content.category', string='Parent Category')
    child_ids = fields.One2many('islamic.content.category', 'parent_id', string='Sub Categories')
    icon = fields.Char(string='Icon Name')
    color = fields.Char(string='Color Code')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class IslamicContentTag(models.Model):
    _name = 'islamic.content.tag'
    _description = 'Content Tag'

    name = fields.Char(string='Tag', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tag name must be unique!'),
    ]


class IslamicContentBookmark(models.Model):
    _name = 'islamic.content.bookmark'
    _description = 'User Content Bookmark'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    bookmark_type = fields.Selection([
        ('ayah', 'Quran Ayah'),
        ('content', 'Content'),
        ('audio', 'Audio'),
        ('adhkar', 'Adhkar'),
    ], string='Bookmark Type', required=True)
    ayah_id = fields.Many2one('islamic.ayah', string='Bookmarked Ayah')
    content_id = fields.Many2one('islamic.content', string='Bookmarked Content')
    audio_id = fields.Many2one('islamic.audio', string='Bookmarked Audio')
    adhkar_id = fields.Many2one('islamic.adhkar', string='Bookmarked Adhkar')
    note = fields.Text(string='Note')

    _sql_constraints = [
        ('unique_ayah_bookmark', 'UNIQUE(app_user_id, ayah_id)',
         'You have already bookmarked this ayah!'),
    ]


class IslamicQuranProgress(models.Model):
    _name = 'islamic.quran.progress'
    _description = 'Quran Reading Progress'
    _order = 'date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    surah_id = fields.Many2one('islamic.surah', string='Surah')
    last_ayah = fields.Integer(string='Last Ayah Read')
    last_page = fields.Integer(string='Last Page Read')
    last_juz = fields.Integer(string='Last Juz Read')
    pages_read_today = fields.Integer(string='Pages Read Today', default=0)
    total_pages_read = fields.Integer(string='Total Pages in Session', default=0)
    date = fields.Date(string='Date', default=fields.Date.today)
    reading_duration = fields.Float(string='Reading Duration (minutes)')
    mode = fields.Selection([
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('memorizing', 'Memorizing'),
    ], string='Mode', default='reading')
