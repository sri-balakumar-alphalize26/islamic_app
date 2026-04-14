import logging
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class IslamicSubscriptionPlan(models.Model):
    _name = 'islamic.subscription.plan'
    _description = 'Subscription Plan'
    _order = 'sequence'

    name = fields.Char(string='Plan Name', required=True)
    name_ar = fields.Char(string='Arabic Name')
    name_fr = fields.Char(string='French Name')
    name_tr = fields.Char(string='Turkish Name')
    name_hi = fields.Char(string='Hindi Name')
    code = fields.Char(string='Plan Code', required=True)
    plan_type = fields.Selection([
        ('free', 'Free'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ], string='Plan Type', required=True)

    price = fields.Float(string='Price (USD)', required=True, default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency')
    original_price = fields.Float(string='Original Price (before discount)')
    discount_percentage = fields.Integer(string='Discount %')
    duration_days = fields.Integer(string='Duration (days)')
    trial_days = fields.Integer(string='Free Trial (days)', default=0)

    # Features
    has_ads = fields.Boolean(string='Shows Ads', default=True)
    full_audio_access = fields.Boolean(string='Full Audio Library', default=False)
    ai_access = fields.Boolean(string='AI Assistant Access', default=False)
    offline_download = fields.Boolean(string='Offline Downloads', default=False)
    tajweed_features = fields.Boolean(string='Advanced Tajweed', default=False)
    hifz_features = fields.Boolean(string='Hifz (Memorization) Tools', default=False)
    advanced_search = fields.Boolean(string='Advanced AI Search', default=False)
    family_sharing = fields.Boolean(string='Family Sharing', default=False)
    max_bookmarks = fields.Integer(string='Max Bookmarks', default=10)
    max_custom_dhikr = fields.Integer(string='Max Custom Dhikr', default=3)

    description_en = fields.Text(string='Description (English)')
    description_ar = fields.Text(string='Description (Arabic)')
    features_json = fields.Text(string='Features List (JSON)')

    is_popular = fields.Boolean(string='Most Popular', default=False)
    badge_text = fields.Char(string='Badge Text', help='e.g., "Save 70%", "Best Value"')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # Store identifiers
    apple_product_id = fields.Char(string='Apple Product ID')
    google_product_id = fields.Char(string='Google Product ID')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Plan code must be unique!'),
    ]

    def to_dict(self, lang='en'):
        self.ensure_one()
        name_map = {
            'en': self.name,
            'ar': self.name_ar or self.name,
            'fr': self.name_fr or self.name,
            'tr': self.name_tr or self.name,
            'hi': self.name_hi or self.name,
        }
        return {
            'id': self.id,
            'name': name_map.get(lang, self.name),
            'code': self.code,
            'plan_type': self.plan_type,
            'price': self.price,
            'original_price': self.original_price,
            'discount_percentage': self.discount_percentage,
            'trial_days': self.trial_days,
            'is_popular': self.is_popular,
            'badge_text': self.badge_text,
            'features': {
                'ad_free': not self.has_ads,
                'full_audio': self.full_audio_access,
                'ai_assistant': self.ai_access,
                'offline_download': self.offline_download,
                'tajweed': self.tajweed_features,
                'hifz': self.hifz_features,
                'advanced_search': self.advanced_search,
                'family_sharing': self.family_sharing,
                'max_bookmarks': self.max_bookmarks,
                'max_custom_dhikr': self.max_custom_dhikr,
            },
            'store_ids': {
                'apple': self.apple_product_id,
                'google': self.google_product_id,
            },
        }


class IslamicSubscription(models.Model):
    _name = 'islamic.subscription'
    _description = 'User Subscription'
    _order = 'create_date desc'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    plan_id = fields.Many2one('islamic.subscription.plan', string='Plan', required=True)
    state = fields.Selection([
        ('trial', 'Free Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ], string='Status', default='trial')

    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date(string='End Date')
    trial_end_date = fields.Date(string='Trial End Date')
    cancelled_date = fields.Date(string='Cancelled Date')
    auto_renew = fields.Boolean(string='Auto Renew', default=True)

    # Payment
    payment_method = fields.Selection([
        ('apple', 'Apple In-App Purchase'),
        ('google', 'Google Play Billing'),
        ('stripe', 'Stripe'),
        ('manual', 'Manual'),
    ], string='Payment Method')
    store_transaction_id = fields.Char(string='Store Transaction ID')
    store_receipt = fields.Text(string='Store Receipt Data')
    amount_paid = fields.Float(string='Amount Paid')
    currency_code = fields.Char(string='Currency')

    # History
    payment_ids = fields.One2many('islamic.payment', 'subscription_id', string='Payment History')

    def action_activate(self):
        for rec in self:
            vals = {'state': 'active'}
            if rec.plan_id.duration_days and not rec.end_date:
                vals['end_date'] = fields.Date.today() + timedelta(days=rec.plan_id.duration_days)
            if rec.plan_id.plan_type == 'lifetime':
                vals['end_date'] = False  # No expiry
            rec.write(vals)

    def action_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancelled',
                'cancelled_date': fields.Date.today(),
                'auto_renew': False,
            })

    @api.model
    def check_expired_subscriptions(self):
        """Cron job: check and expire subscriptions"""
        expired = self.search([
            ('state', 'in', ['active', 'trial']),
            ('end_date', '<', fields.Date.today()),
            ('plan_id.plan_type', '!=', 'lifetime'),
        ])
        expired.write({'state': 'expired'})
        _logger.info(f"Expired {len(expired)} subscriptions")

    def to_dict(self, lang='en'):
        self.ensure_one()
        return {
            'id': self.id,
            'plan': self.plan_id.to_dict(lang),
            'state': self.state,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'auto_renew': self.auto_renew,
            'payment_method': self.payment_method,
        }


class IslamicPayment(models.Model):
    _name = 'islamic.payment'
    _description = 'Payment Record'
    _order = 'create_date desc'

    subscription_id = fields.Many2one('islamic.subscription', string='Subscription', ondelete='cascade')
    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True)
    amount = fields.Float(string='Amount', required=True)
    currency_code = fields.Char(string='Currency', default='USD')
    payment_method = fields.Selection([
        ('apple', 'Apple'),
        ('google', 'Google'),
        ('stripe', 'Stripe'),
        ('manual', 'Manual'),
    ], string='Payment Method')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], string='Status', default='pending')
    transaction_id = fields.Char(string='Transaction ID')
    receipt_data = fields.Text(string='Receipt Data')
    payment_date = fields.Datetime(string='Payment Date', default=fields.Datetime.now)
    notes = fields.Text(string='Notes')
