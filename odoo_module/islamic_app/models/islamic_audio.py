import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicAudio(models.Model):
    _name = 'islamic.audio'
    _description = 'Islamic Audio Content'
    _order = 'sequence, create_date desc'

    name = fields.Char(string='Title (English)', required=True)
    name_ar = fields.Char(string='Title (Arabic)')
    name_fr = fields.Char(string='Title (French)')
    name_tr = fields.Char(string='Title (Turkish)')
    name_hi = fields.Char(string='Title (Hindi)')

    audio_type = fields.Selection([
        ('quran_recitation', 'Quran Recitation'),
        ('surah_recitation', 'Full Surah Recitation'),
        ('adhkar_audio', 'Adhkar Audio'),
        ('dua', 'Dua'),
        ('lecture', 'Lecture'),
        ('nasheeed', 'Nasheed'),
        ('reminder', 'Reminder'),
        ('wakeup_supplication', 'Wake-up Supplication'),
    ], string='Audio Type', required=True)

    # Linked content
    surah_id = fields.Many2one('islamic.surah', string='Related Surah')
    adhkar_id = fields.Many2one('islamic.adhkar', string='Related Adhkar')
    content_id = fields.Many2one('islamic.content', string='Related Content')

    # Reciter / Speaker info
    reciter_name = fields.Char(string='Reciter / Speaker')
    reciter_name_ar = fields.Char(string='Reciter Name (Arabic)')
    is_sister_nasira = fields.Boolean(string='By Sister Nasira', default=False)
    is_brother_ibrahim = fields.Boolean(string='By Brother Ibrahim', default=False)

    # File details
    audio_file = fields.Binary(string='Audio File (Upload)')
    audio_file_name = fields.Char(string='Audio Filename')
    audio_url = fields.Char(string='Audio URL (CDN)')
    audio_url_hq = fields.Char(string='High Quality URL')
    audio_url_lq = fields.Char(string='Low Quality URL')
    file_size_mb = fields.Float(string='File Size (MB)')
    duration_seconds = fields.Float(string='Duration (seconds)')
    duration_display = fields.Char(string='Duration', compute='_compute_duration_display')
    bitrate = fields.Integer(string='Bitrate (kbps)', default=128)
    format = fields.Selection([
        ('mp3', 'MP3'),
        ('ogg', 'OGG'),
        ('aac', 'AAC'),
        ('wav', 'WAV'),
    ], string='Format', default='mp3')
    sample_rate = fields.Integer(string='Sample Rate (Hz)', default=44100)

    # Audio processing
    is_enhanced = fields.Boolean(string='Audio Enhanced', default=False)
    enhancement_notes = fields.Text(string='Enhancement Notes')
    original_audio = fields.Binary(string='Original (Pre-enhancement)')

    # Publishing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='Status', default='draft')
    uploaded_by = fields.Many2one('islamic.app.user', string='Uploaded By')
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    published_date = fields.Datetime(string='Published Date')
    sequence = fields.Integer(string='Sequence', default=10)

    # Categories & tags
    category_id = fields.Many2one('islamic.audio.category', string='Category')
    tag_ids = fields.Many2many('islamic.audio.tag', string='Tags')
    language = fields.Selection([
        ('ar', 'Arabic'),
        ('en', 'English'),
        ('fr', 'French'),
        ('tr', 'Turkish'),
        ('hi', 'Hindi'),
        ('multi', 'Multi-language'),
    ], string='Language', default='ar')

    # Engagement
    play_count = fields.Integer(string='Play Count', default=0)
    download_count = fields.Integer(string='Download Count', default=0)
    like_count = fields.Integer(string='Like Count', default=0)
    is_premium = fields.Boolean(string='Premium Only', default=False)
    is_downloadable = fields.Boolean(string='Allow Offline Download', default=True)

    # Playlist
    playlist_ids = fields.Many2many('islamic.audio.playlist', string='Playlists')

    # Cover art
    cover_image = fields.Binary(string='Cover Image')
    cover_image_url = fields.Char(string='Cover Image URL')

    active = fields.Boolean(default=True)

    @api.depends('duration_seconds')
    def _compute_duration_display(self):
        for rec in self:
            if rec.duration_seconds:
                mins = int(rec.duration_seconds // 60)
                secs = int(rec.duration_seconds % 60)
                rec.duration_display = f"{mins}:{secs:02d}"
            else:
                rec.duration_display = "0:00"

    def action_publish(self):
        for rec in self:
            rec.write({
                'state': 'published',
                'published_date': fields.Datetime.now(),
            })

    def action_archive(self):
        for rec in self:
            rec.write({'state': 'archived'})

    def to_dict(self, lang='en'):
        self.ensure_one()
        lang_map = {
            'en': self.name,
            'ar': self.name_ar or self.name,
            'fr': self.name_fr or self.name,
            'tr': self.name_tr or self.name,
            'hi': self.name_hi or self.name,
        }
        return {
            'id': self.id,
            'title': lang_map.get(lang, self.name),
            'audio_type': self.audio_type,
            'reciter': self.reciter_name,
            'audio_url': self.audio_url,
            'audio_url_hq': self.audio_url_hq,
            'audio_url_lq': self.audio_url_lq,
            'duration': self.duration_display,
            'duration_seconds': self.duration_seconds,
            'file_size_mb': self.file_size_mb,
            'is_premium': self.is_premium,
            'is_downloadable': self.is_downloadable,
            'cover_image_url': self.cover_image_url,
            'play_count': self.play_count,
            'like_count': self.like_count,
            'surah_number': self.surah_id.number if self.surah_id else None,
            'language': self.language,
        }


class IslamicAudioCategory(models.Model):
    _name = 'islamic.audio.category'
    _description = 'Audio Category'
    _order = 'sequence'

    name = fields.Char(string='Category Name', required=True)
    name_ar = fields.Char(string='Arabic Name')
    code = fields.Char(string='Code')
    icon = fields.Char(string='Icon')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class IslamicAudioTag(models.Model):
    _name = 'islamic.audio.tag'
    _description = 'Audio Tag'

    name = fields.Char(string='Tag', required=True)
    color = fields.Integer(string='Color Index')


class IslamicAudioPlaylist(models.Model):
    _name = 'islamic.audio.playlist'
    _description = 'Audio Playlist'
    _order = 'sequence'

    name = fields.Char(string='Playlist Name', required=True)
    name_ar = fields.Char(string='Arabic Name')
    description = fields.Text(string='Description')
    audio_ids = fields.Many2many('islamic.audio', string='Audio Tracks')
    app_user_id = fields.Many2one('islamic.app.user', string='Created By')
    is_system = fields.Boolean(string='System Playlist', default=False,
                               help='System playlists are created by admin and available to all')
    cover_image_url = fields.Char(string='Cover Image URL')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    def to_dict(self, lang='en'):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name_ar if lang == 'ar' and self.name_ar else self.name,
            'description': self.description,
            'track_count': len(self.audio_ids),
            'cover_image_url': self.cover_image_url,
            'is_system': self.is_system,
            'tracks': [a.to_dict(lang) for a in self.audio_ids[:20]],
        }


class IslamicListeningHistory(models.Model):
    _name = 'islamic.listening.history'
    _description = 'User Listening History'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    audio_id = fields.Many2one('islamic.audio', string='Audio', required=True, ondelete='cascade')
    listened_seconds = fields.Float(string='Listened Duration (seconds)')
    completed = fields.Boolean(string='Completed', default=False)
    date = fields.Datetime(string='Listened At', default=fields.Datetime.now)
