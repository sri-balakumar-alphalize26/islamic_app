import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    ('en', 'English'),
    ('ar', 'العربية (Arabic)'),
    ('fr', 'Français (French)'),
    ('tr', 'Türkçe (Turkish)'),
    ('hi', 'हिन्दी (Hindi)'),
]


class IslamicAppLanguage(models.Model):
    _name = 'islamic.app.language'
    _description = 'Supported Application Languages'
    _order = 'sequence, id'

    name = fields.Char(string='Language Name', required=True, translate=True)
    code = fields.Selection(SUPPORTED_LANGUAGES, string='Language Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_rtl = fields.Boolean(string='Right-to-Left', default=False)
    active = fields.Boolean(string='Active', default=True)
    font_family = fields.Char(string='Font Family', help='Recommended font for this language')
    flag_icon = fields.Char(string='Flag Icon Code', help='Country flag emoji or icon code')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Language code must be unique!'),
    ]


class IslamicTranslation(models.Model):
    """Generic translation model for any content that needs multi-language support"""
    _name = 'islamic.translation'
    _description = 'Content Translation'
    _order = 'language_code'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    res_model = fields.Char(string='Related Model', required=True, index=True)
    res_id = fields.Integer(string='Related Record ID', required=True, index=True)
    res_field = fields.Char(string='Translated Field', required=True)
    language_code = fields.Selection(SUPPORTED_LANGUAGES, string='Language', required=True)
    value_text = fields.Text(string='Translated Text')
    value_html = fields.Html(string='Translated HTML')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
    ], string='Status', default='draft')
    translator_id = fields.Many2one('res.users', string='Translated By')
    reviewed_by_id = fields.Many2one('res.users', string='Reviewed By')

    @api.depends('res_model', 'res_id', 'res_field', 'language_code')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.res_model}/{rec.res_id}/{rec.res_field}/{rec.language_code}"

    _sql_constraints = [
        ('unique_translation', 'UNIQUE(res_model, res_id, res_field, language_code)',
         'A translation for this field and language already exists!'),
    ]

    @api.model
    def get_translation(self, model, record_id, field_name, lang_code):
        """Get translation for a specific record field in given language"""
        trans = self.search([
            ('res_model', '=', model),
            ('res_id', '=', record_id),
            ('res_field', '=', field_name),
            ('language_code', '=', lang_code),
            ('state', '=', 'approved'),
        ], limit=1)
        return trans.value_text or trans.value_html or False

    @api.model
    def set_translation(self, model, record_id, field_name, lang_code, value, is_html=False):
        """Set or update translation for a specific record field"""
        existing = self.search([
            ('res_model', '=', model),
            ('res_id', '=', record_id),
            ('res_field', '=', field_name),
            ('language_code', '=', lang_code),
        ], limit=1)
        vals = {
            'res_model': model,
            'res_id': record_id,
            'res_field': field_name,
            'language_code': lang_code,
        }
        if is_html:
            vals['value_html'] = value
        else:
            vals['value_text'] = value
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)
