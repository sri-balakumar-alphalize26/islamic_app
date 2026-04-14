import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicDhikrLog(models.Model):
    _name = 'islamic.dhikr.log'
    _description = 'Dhikr Counter Log'
    _order = 'date desc, create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade', index=True)
    adhkar_id = fields.Many2one('islamic.adhkar', string='Adhkar', ondelete='set null')
    custom_dhikr_text = fields.Char(string='Custom Dhikr Text', help='For user-defined dhikr')

    count = fields.Integer(string='Count', required=True, default=0)
    target_count = fields.Integer(string='Target Count')
    completed = fields.Boolean(string='Target Reached', compute='_compute_completed', store=True)
    date = fields.Date(string='Date', default=fields.Date.today, index=True)
    time_of_day = fields.Selection([
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('after_prayer', 'After Prayer'),
        ('custom', 'Custom Time'),
    ], string='Time of Day')

    # Session details
    session_start = fields.Datetime(string='Session Start')
    session_end = fields.Datetime(string='Session End')
    session_duration = fields.Float(string='Session Duration (minutes)', compute='_compute_session_duration',
                                    store=True)

    @api.depends('count', 'target_count')
    def _compute_completed(self):
        for rec in self:
            rec.completed = rec.target_count > 0 and rec.count >= rec.target_count

    @api.depends('session_start', 'session_end')
    def _compute_session_duration(self):
        for rec in self:
            if rec.session_start and rec.session_end:
                delta = rec.session_end - rec.session_start
                rec.session_duration = delta.total_seconds() / 60
            else:
                rec.session_duration = 0

    def increment_count(self, amount=1):
        """Increment dhikr count and update user stats"""
        self.ensure_one()
        self.write({'count': self.count + amount})
        # Update user total
        self.app_user_id.sudo().write({
            'total_dhikr_count': self.app_user_id.total_dhikr_count + amount,
        })

    def to_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'adhkar_id': self.adhkar_id.id if self.adhkar_id else None,
            'adhkar_title': self.adhkar_id.name if self.adhkar_id else self.custom_dhikr_text,
            'count': self.count,
            'target': self.target_count,
            'completed': self.completed,
            'date': self.date.isoformat() if self.date else None,
            'time_of_day': self.time_of_day,
            'duration_minutes': round(self.session_duration, 1),
        }


class IslamicDhikrStreak(models.Model):
    _name = 'islamic.dhikr.streak'
    _description = 'Dhikr Streak Tracking'
    _order = 'date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade', index=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    has_activity = fields.Boolean(string='Had Dhikr Activity', default=False)
    total_count = fields.Integer(string='Total Count for Day', default=0)
    sessions = fields.Integer(string='Number of Sessions', default=0)

    _sql_constraints = [
        ('unique_user_date', 'UNIQUE(app_user_id, date)', 'Only one streak record per user per day!'),
    ]

    @api.model
    def update_streak(self, app_user_id):
        """Recalculate streak for a user"""
        user = self.env['islamic.app.user'].browse(app_user_id)
        today = fields.Date.today()
        current_streak = 0
        check_date = today

        while True:
            record = self.search([
                ('app_user_id', '=', app_user_id),
                ('date', '=', check_date),
                ('has_activity', '=', True),
            ], limit=1)
            if record:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        user.sudo().write({
            'current_streak': current_streak,
            'longest_streak': max(current_streak, user.longest_streak),
        })
        return current_streak


class IslamicDhikrCustom(models.Model):
    """User-created custom dhikr"""
    _name = 'islamic.dhikr.custom'
    _description = 'Custom User Dhikr'
    _order = 'sequence'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    name = fields.Char(string='Dhikr Name', required=True)
    arabic_text = fields.Text(string='Arabic Text')
    target_count = fields.Integer(string='Target Count', default=33)
    icon = fields.Char(string='Icon')
    color = fields.Char(string='Color')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    def to_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'arabic_text': self.arabic_text,
            'target_count': self.target_count,
            'icon': self.icon,
            'color': self.color,
        }


class IslamicDhikrStats(models.Model):
    """Aggregated daily dhikr statistics"""
    _name = 'islamic.dhikr.stats'
    _description = 'Dhikr Daily Statistics'
    _order = 'date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    total_count = fields.Integer(string='Total Dhikr Count')
    unique_adhkar = fields.Integer(string='Unique Adhkar Performed')
    total_sessions = fields.Integer(string='Total Sessions')
    total_minutes = fields.Float(string='Total Minutes')
    morning_completed = fields.Boolean(string='Morning Adhkar Done')
    evening_completed = fields.Boolean(string='Evening Adhkar Done')

    _sql_constraints = [
        ('unique_user_date', 'UNIQUE(app_user_id, date)', 'One stats record per day!'),
    ]
