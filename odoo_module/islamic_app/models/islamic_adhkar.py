import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicAdhkarCategory(models.Model):
    _name = 'islamic.adhkar.category'
    _description = 'Adhkar Category'
    _order = 'sequence'

    name = fields.Char(string='Category (English)', required=True)
    name_ar = fields.Char(string='Category (Arabic)')
    name_fr = fields.Char(string='Category (French)')
    name_tr = fields.Char(string='Category (Turkish)')
    name_hi = fields.Char(string='Category (Hindi)')
    code = fields.Char(string='Code', required=True)
    icon = fields.Char(string='Icon Name')
    color = fields.Char(string='Color Code')
    description = fields.Text(string='Description')
    adhkar_ids = fields.One2many('islamic.adhkar', 'category_id', string='Adhkar')
    adhkar_count = fields.Integer(string='Adhkar Count', compute='_compute_adhkar_count')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.depends('adhkar_ids')
    def _compute_adhkar_count(self):
        for rec in self:
            rec.adhkar_count = len(rec.adhkar_ids.filtered(lambda a: a.state == 'published'))

    def get_name_by_lang(self, lang='en'):
        self.ensure_one()
        return {
            'en': self.name,
            'ar': self.name_ar or self.name,
            'fr': self.name_fr or self.name,
            'tr': self.name_tr or self.name,
            'hi': self.name_hi or self.name,
        }.get(lang, self.name)

    def to_dict(self, lang='en'):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.get_name_by_lang(lang),
            'code': self.code,
            'icon': self.icon,
            'color': self.color,
            'adhkar_count': self.adhkar_count,
        }


class IslamicAdhkar(models.Model):
    _name = 'islamic.adhkar'
    _description = 'Individual Dhikr/Supplication'
    _order = 'category_id, sequence'

    name = fields.Char(string='Title (English)', required=True)
    name_ar = fields.Char(string='Title (Arabic)')
    name_fr = fields.Char(string='Title (French)')
    name_tr = fields.Char(string='Title (Turkish)')
    name_hi = fields.Char(string='Title (Hindi)')

    category_id = fields.Many2one('islamic.adhkar.category', string='Category', required=True, ondelete='cascade')

    # Arabic text (primary)
    arabic_text = fields.Text(string='Arabic Text', required=True)
    arabic_diacritics = fields.Text(string='Arabic with Diacritics')

    # Translations
    translation_en = fields.Text(string='English Translation')
    translation_fr = fields.Text(string='French Translation')
    translation_tr = fields.Text(string='Turkish Translation')
    translation_hi = fields.Text(string='Hindi Translation')

    # Transliteration
    transliteration_en = fields.Text(string='Transliteration (English)')
    transliteration_fr = fields.Text(string='Transliteration (French)')
    transliteration_tr = fields.Text(string='Transliteration (Turkish)')

    # Reference & source
    reference = fields.Char(string='Reference (Hadith/Book)')
    reference_ar = fields.Char(string='Reference (Arabic)')
    source_book = fields.Char(string='Source Book')
    hadith_number = fields.Char(string='Hadith Number')
    narrator = fields.Char(string='Narrator')

    # Repetition
    repeat_count = fields.Integer(string='Recommended Repeat Count', default=1)
    repeat_after_prayer = fields.Boolean(string='Repeat After Each Prayer', default=False)

    # Virtue / benefit
    virtue_en = fields.Text(string='Virtue (English)')
    virtue_ar = fields.Text(string='Virtue (Arabic)')
    virtue_fr = fields.Text(string='Virtue (French)')
    virtue_tr = fields.Text(string='Virtue (Turkish)')
    virtue_hi = fields.Text(string='Virtue (Hindi)')

    # Time specification
    time_of_day = fields.Selection([
        ('morning', 'Morning (After Fajr)'),
        ('evening', 'Evening (After Asr)'),
        ('after_prayer', 'After Prayer'),
        ('before_sleep', 'Before Sleep'),
        ('wakeup', 'Upon Waking Up'),
        ('anytime', 'Any Time'),
        ('specific', 'Specific Occasion'),
    ], string='Time of Day', default='anytime')
    occasion = fields.Char(string='Specific Occasion')

    # Audio
    audio_id = fields.Many2one('islamic.audio', string='Audio Recitation')
    audio_url = fields.Char(string='Quick Audio URL')

    # Publishing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='Status', default='draft')
    sequence = fields.Integer(default=10)
    is_featured = fields.Boolean(string='Featured', default=False)
    is_premium = fields.Boolean(string='Premium Only', default=False)

    active = fields.Boolean(default=True)

    def get_translation(self, lang='en'):
        self.ensure_one()
        return {
            'en': self.translation_en,
            'ar': self.arabic_text,
            'fr': self.translation_fr or self.translation_en,
            'tr': self.translation_tr or self.translation_en,
            'hi': self.translation_hi or self.translation_en,
        }.get(lang, self.translation_en)

    def get_virtue(self, lang='en'):
        self.ensure_one()
        return {
            'en': self.virtue_en,
            'ar': self.virtue_ar or self.virtue_en,
            'fr': self.virtue_fr or self.virtue_en,
            'tr': self.virtue_tr or self.virtue_en,
            'hi': self.virtue_hi or self.virtue_en,
        }.get(lang, self.virtue_en)

    def to_dict(self, lang='en'):
        self.ensure_one()
        title_map = {
            'en': self.name,
            'ar': self.name_ar or self.name,
            'fr': self.name_fr or self.name,
            'tr': self.name_tr or self.name,
            'hi': self.name_hi or self.name,
        }
        return {
            'id': self.id,
            'title': title_map.get(lang, self.name),
            'arabic_text': self.arabic_diacritics or self.arabic_text,
            'translation': self.get_translation(lang),
            'transliteration': self.transliteration_en,
            'reference': self.reference,
            'repeat_count': self.repeat_count,
            'virtue': self.get_virtue(lang),
            'time_of_day': self.time_of_day,
            'audio_url': self.audio_url or (self.audio_id.audio_url if self.audio_id else None),
            'is_featured': self.is_featured,
            'is_premium': self.is_premium,
            'category': self.category_id.to_dict(lang) if self.category_id else None,
        }
