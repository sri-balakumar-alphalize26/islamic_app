import logging
import json
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

AI_SYSTEM_PROMPT = """You are an Islamic knowledge assistant integrated into a Quran and Dhikr mobile application.
Your role is to help Muslims with:
- Answering questions about Islam, Quran, Hadith, and Fiqh
- Explaining meanings of Quranic verses and supplications
- Providing guidance on Islamic practices and daily worship
- Recommending relevant adhkar and duas for specific situations
- Sharing wisdom from authentic Islamic sources

Guidelines:
- Always cite Quran references as (Surah Name:Ayah Number)
- Cite Hadith with their source (e.g., Sahih Bukhari, Sahih Muslim)
- Be respectful of all Islamic schools of thought
- If unsure, say so and recommend consulting a local scholar
- Respond in the user's preferred language
- Keep responses concise but informative
- Focus on authentic, mainstream Islamic teachings
"""


class IslamicAIConversation(models.Model):
    _name = 'islamic.ai.conversation'
    _description = 'AI Conversation'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade', index=True)
    title = fields.Char(string='Conversation Title')
    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('tr', 'Turkish'),
        ('hi', 'Hindi'),
    ], string='Language', default='en')
    message_ids = fields.One2many('islamic.ai.message', 'conversation_id', string='Messages')
    message_count = fields.Integer(compute='_compute_message_count')
    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string='Status', default='active')
    topic = fields.Selection([
        ('quran', 'Quran'),
        ('hadith', 'Hadith'),
        ('fiqh', 'Fiqh'),
        ('dua', 'Dua & Adhkar'),
        ('seerah', 'Seerah'),
        ('general', 'General Islamic'),
        ('personal', 'Personal Guidance'),
    ], string='Topic')

    @api.depends('message_ids')
    def _compute_message_count(self):
        for rec in self:
            rec.message_count = len(rec.message_ids)

    def to_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'title': self.title,
            'language': self.language,
            'topic': self.topic,
            'message_count': self.message_count,
            'created_at': self.create_date.isoformat() if self.create_date else None,
            'messages': [m.to_dict() for m in self.message_ids.sorted('create_date')],
        }


class IslamicAIMessage(models.Model):
    _name = 'islamic.ai.message'
    _description = 'AI Conversation Message'
    _order = 'create_date'

    conversation_id = fields.Many2one('islamic.ai.conversation', string='Conversation',
                                       required=True, ondelete='cascade')
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ], string='Role', required=True)
    content = fields.Text(string='Message Content', required=True)
    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('tr', 'Turkish'),
        ('hi', 'Hindi'),
    ], string='Language')

    # AI metadata
    model_used = fields.Char(string='AI Model')
    tokens_used = fields.Integer(string='Tokens Used')
    response_time_ms = fields.Integer(string='Response Time (ms)')

    # Content references found
    referenced_ayahs = fields.Text(string='Referenced Ayahs (JSON)')
    referenced_content = fields.Text(string='Referenced Content (JSON)')

    # Feedback
    is_helpful = fields.Boolean(string='Marked Helpful')
    is_flagged = fields.Boolean(string='Flagged for Review')
    flag_reason = fields.Text(string='Flag Reason')

    def to_dict(self):
        self.ensure_one()
        result = {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'language': self.language,
            'created_at': self.create_date.isoformat() if self.create_date else None,
        }
        if self.referenced_ayahs:
            try:
                result['references'] = json.loads(self.referenced_ayahs)
            except (json.JSONDecodeError, TypeError):
                pass
        return result


class IslamicAIConfig(models.Model):
    _name = 'islamic.ai.config'
    _description = 'AI Configuration'

    name = fields.Char(string='Config Name', required=True, default='Default')
    ai_provider = fields.Selection([
        ('anthropic', 'Anthropic (Claude)'),
        ('openai', 'OpenAI (GPT)'),
        ('custom', 'Custom API'),
    ], string='AI Provider', default='anthropic', required=True)
    api_key = fields.Char(string='API Key')
    api_url = fields.Char(string='API URL')
    model_name = fields.Char(string='Model Name', default='claude-sonnet-4-20250514')
    max_tokens = fields.Integer(string='Max Response Tokens', default=1024)
    temperature = fields.Float(string='Temperature', default=0.7)
    system_prompt = fields.Text(string='System Prompt', default=AI_SYSTEM_PROMPT)
    system_prompt_ar = fields.Text(string='System Prompt (Arabic)')

    # Rate limiting
    max_daily_queries_free = fields.Integer(string='Daily Limit (Free)', default=5)
    max_daily_queries_premium = fields.Integer(string='Daily Limit (Premium)', default=50)

    is_active = fields.Boolean(default=True)

    @api.model
    def get_active_config(self):
        return self.search([('is_active', '=', True)], limit=1)


class IslamicAIQueryLog(models.Model):
    """Track AI usage for rate limiting and analytics"""
    _name = 'islamic.ai.query.log'
    _description = 'AI Query Log'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    query = fields.Text(string='User Query')
    response_preview = fields.Char(string='Response Preview')
    language = fields.Char(string='Language')
    topic = fields.Char(string='Detected Topic')
    tokens_used = fields.Integer(string='Tokens Used')
    cost_usd = fields.Float(string='Estimated Cost (USD)')
    response_time_ms = fields.Integer(string='Response Time (ms)')
    date = fields.Date(string='Date', default=fields.Date.today, index=True)
    is_premium_user = fields.Boolean(string='Premium User')

    @api.model
    def get_user_daily_count(self, app_user_id, date=None):
        """Get number of AI queries a user has made today"""
        if not date:
            date = fields.Date.today()
        return self.search_count([
            ('app_user_id', '=', app_user_id),
            ('date', '=', date),
        ])
