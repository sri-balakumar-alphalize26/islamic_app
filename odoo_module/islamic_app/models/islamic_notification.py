import logging
import json
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicNotificationType(models.Model):
    _name = 'islamic.notification.type'
    _description = 'Notification Type'
    _order = 'sequence'

    name = fields.Char(string='Type Name', required=True)
    code = fields.Char(string='Code', required=True)
    icon = fields.Char(string='Icon')
    color = fields.Char(string='Color')
    is_push = fields.Boolean(string='Send as Push', default=True)
    is_in_app = fields.Boolean(string='Show In-App', default=True)
    template_en = fields.Text(string='Template (English)')
    template_ar = fields.Text(string='Template (Arabic)')
    template_fr = fields.Text(string='Template (French)')
    template_tr = fields.Text(string='Template (Turkish)')
    template_hi = fields.Text(string='Template (Hindi)')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Notification type code must be unique!'),
    ]


class IslamicNotification(models.Model):
    _name = 'islamic.notification'
    _description = 'User Notification'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade', index=True)
    notification_type_id = fields.Many2one('islamic.notification.type', string='Type')
    notification_category = fields.Selection([
        ('prayer_time', 'Prayer Time'),
        ('adhkar_morning', 'Morning Adhkar'),
        ('adhkar_evening', 'Evening Adhkar'),
        ('family_ties', 'Family Ties'),
        ('wakeup', 'Wake-up Supplication'),
        ('streak', 'Streak Reminder'),
        ('content', 'New Content'),
        ('subscription', 'Subscription'),
        ('system', 'System'),
        ('custom', 'Custom'),
    ], string='Category', required=True)

    title = fields.Char(string='Title', required=True)
    title_ar = fields.Char(string='Title (Arabic)')
    body = fields.Text(string='Body', required=True)
    body_ar = fields.Text(string='Body (Arabic)')
    image_url = fields.Char(string='Image URL')

    # Delivery
    is_read = fields.Boolean(string='Read', default=False)
    read_at = fields.Datetime(string='Read At')
    is_push_sent = fields.Boolean(string='Push Sent', default=False)
    push_sent_at = fields.Datetime(string='Push Sent At')
    fcm_message_id = fields.Char(string='FCM Message ID')

    # Action
    action_type = fields.Selection([
        ('open_app', 'Open App'),
        ('open_surah', 'Open Surah'),
        ('open_adhkar', 'Open Adhkar'),
        ('open_audio', 'Open Audio'),
        ('open_content', 'Open Content'),
        ('open_subscription', 'Open Subscription'),
        ('open_url', 'Open URL'),
    ], string='Action Type', default='open_app')
    action_data = fields.Text(string='Action Data (JSON)')

    # Scheduling
    scheduled_at = fields.Datetime(string='Scheduled At')
    is_recurring = fields.Boolean(string='Recurring', default=False)
    recurrence_rule = fields.Char(string='Recurrence Rule')

    def mark_as_read(self):
        self.write({
            'is_read': True,
            'read_at': fields.Datetime.now(),
        })

    def to_dict(self, lang='en'):
        self.ensure_one()
        return {
            'id': self.id,
            'category': self.notification_category,
            'title': self.title_ar if lang == 'ar' and self.title_ar else self.title,
            'body': self.body_ar if lang == 'ar' and self.body_ar else self.body,
            'image_url': self.image_url,
            'is_read': self.is_read,
            'action_type': self.action_type,
            'action_data': json.loads(self.action_data) if self.action_data else None,
            'created_at': self.create_date.isoformat() if self.create_date else None,
        }


class IslamicPrayerTime(models.Model):
    """Pre-calculated prayer times for notification scheduling"""
    _name = 'islamic.prayer.time'
    _description = 'Prayer Time'
    _order = 'date, fajr'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    calculation_method = fields.Char(string='Calculation Method')

    fajr = fields.Char(string='Fajr')
    sunrise = fields.Char(string='Sunrise')
    dhuhr = fields.Char(string='Dhuhr')
    asr = fields.Char(string='Asr')
    maghrib = fields.Char(string='Maghrib')
    isha = fields.Char(string='Isha')

    fajr_notified = fields.Boolean(default=False)
    dhuhr_notified = fields.Boolean(default=False)
    asr_notified = fields.Boolean(default=False)
    maghrib_notified = fields.Boolean(default=False)
    isha_notified = fields.Boolean(default=False)

    _sql_constraints = [
        ('unique_user_date', 'UNIQUE(app_user_id, date)', 'One prayer time record per user per day!'),
    ]

    def to_dict(self):
        self.ensure_one()
        return {
            'date': self.date.isoformat(),
            'fajr': self.fajr,
            'sunrise': self.sunrise,
            'dhuhr': self.dhuhr,
            'asr': self.asr,
            'maghrib': self.maghrib,
            'isha': self.isha,
        }


class IslamicNotificationScheduler(models.Model):
    _name = 'islamic.notification.scheduler'
    _description = 'Notification Scheduler'

    name = fields.Char(string='Scheduler Name', required=True)
    notification_type = fields.Selection([
        ('prayer_time', 'Prayer Time'),
        ('morning_adhkar', 'Morning Adhkar'),
        ('evening_adhkar', 'Evening Adhkar'),
        ('family_ties', 'Family Ties Check'),
        ('wakeup', 'Wake-up Alarm'),
        ('streak_reminder', 'Streak Reminder'),
        ('weekly_summary', 'Weekly Summary'),
    ], string='Type', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    cron_id = fields.Many2one('ir.cron', string='Scheduled Action')
    last_run = fields.Datetime(string='Last Run')
    next_run = fields.Datetime(string='Next Run')

    @api.model
    def send_morning_adhkar_reminders(self):
        """Cron: Send morning adhkar reminders to opted-in users"""
        users = self.env['islamic.app.user'].sudo().search([
            ('adhkar_morning_notification', '=', True),
            ('device_token_fcm', '!=', False),
        ])
        for user in users:
            self.env['islamic.notification'].sudo().create({
                'app_user_id': user.id,
                'notification_category': 'adhkar_morning',
                'title': 'Morning Adhkar',
                'title_ar': 'أذكار الصباح',
                'body': 'Start your day with morning supplications',
                'body_ar': 'ابدأ يومك بأذكار الصباح',
                'action_type': 'open_adhkar',
                'action_data': json.dumps({'category': 'morning'}),
            })
        _logger.info(f"Sent morning adhkar reminders to {len(users)} users")

    @api.model
    def send_evening_adhkar_reminders(self):
        """Cron: Send evening adhkar reminders"""
        users = self.env['islamic.app.user'].sudo().search([
            ('adhkar_evening_notification', '=', True),
            ('device_token_fcm', '!=', False),
        ])
        for user in users:
            self.env['islamic.notification'].sudo().create({
                'app_user_id': user.id,
                'notification_category': 'adhkar_evening',
                'title': 'Evening Adhkar',
                'title_ar': 'أذكار المساء',
                'body': 'Time for your evening supplications',
                'body_ar': 'حان وقت أذكار المساء',
                'action_type': 'open_adhkar',
                'action_data': json.dumps({'category': 'evening'}),
            })
        _logger.info(f"Sent evening adhkar reminders to {len(users)} users")

    @api.model
    def send_streak_reminders(self):
        """Cron: Remind users to maintain their dhikr streak"""
        today = fields.Date.today()
        users_with_streaks = self.env['islamic.app.user'].sudo().search([
            ('current_streak', '>', 0),
            ('device_token_fcm', '!=', False),
        ])
        for user in users_with_streaks:
            # Check if they had activity today
            today_log = self.env['islamic.dhikr.log'].sudo().search([
                ('app_user_id', '=', user.id),
                ('date', '=', today),
            ], limit=1)
            if not today_log:
                self.env['islamic.notification'].sudo().create({
                    'app_user_id': user.id,
                    'notification_category': 'streak',
                    'title': f'Keep your {user.current_streak}-day streak!',
                    'body': 'Don\'t forget your daily dhikr to maintain your streak',
                    'action_type': 'open_adhkar',
                })
