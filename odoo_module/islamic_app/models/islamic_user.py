import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta

from odoo import models, fields, api, Command
from odoo.exceptions import AccessDenied, ValidationError

_logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = 'islamic_app_jwt_secret_change_in_production'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 72
JWT_REFRESH_EXPIRY_DAYS = 30


def _base64url_encode(data):
    """Base64url encode bytes"""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data):
    """Base64url decode string"""
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def generate_jwt(payload, secret=JWT_SECRET_KEY):
    """Generate a simple JWT token"""
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b64 = _base64url_encode(json.dumps(header).encode())
    payload_b64 = _base64url_encode(json.dumps(payload).encode())
    signature_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), signature_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_jwt(token, secret=JWT_SECRET_KEY):
    """Verify and decode a JWT token"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        signature_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(secret.encode(), signature_input, hashlib.sha256).digest()
        actual_sig = _base64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_base64url_decode(payload_b64))
        if payload.get('exp', 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class IslamicAppUser(models.Model):
    _name = 'islamic.app.user'
    _description = 'Islamic App Mobile User'
    _inherits = {'res.users': 'user_id'}
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='System User', required=True, ondelete='cascade')

    # Profile
    display_name_app = fields.Char(string='Display Name')
    phone_number = fields.Char(string='Phone Number')
    profile_image = fields.Binary(string='Profile Image')
    profile_image_url = fields.Char(string='Profile Image URL')
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender')
    bio = fields.Text(string='Bio')
    country_id = fields.Many2one('res.country', string='Country')
    city = fields.Char(string='City')

    # App Settings
    preferred_language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('tr', 'Turkish'),
        ('hi', 'Hindi'),
    ], string='Preferred Language', default='en')
    app_role = fields.Selection([
        ('user', 'Regular User'),
        ('special', 'Special User'),
        ('admin', 'Administrator'),
    ], string='App Role', default='user')
    is_premium = fields.Boolean(string='Premium User', compute='_compute_is_premium', store=True)

    # Device & Push Notifications
    device_token_fcm = fields.Char(string='FCM Device Token')
    device_type = fields.Selection([
        ('ios', 'iOS'),
        ('android', 'Android'),
    ], string='Device Type')
    device_model = fields.Char(string='Device Model')
    app_version = fields.Char(string='App Version')
    last_active = fields.Datetime(string='Last Active')
    timezone = fields.Char(string='Timezone', default='UTC')

    # Authentication
    jwt_refresh_token = fields.Char(string='Refresh Token')
    jwt_refresh_expiry = fields.Datetime(string='Refresh Token Expiry')
    failed_login_attempts = fields.Integer(string='Failed Login Attempts', default=0)
    is_locked = fields.Boolean(string='Account Locked', default=False)
    locked_until = fields.Datetime(string='Locked Until')
    last_login = fields.Datetime(string='Last Login')
    auth_provider = fields.Selection([
        ('email', 'Email/Password'),
        ('google', 'Google'),
        ('apple', 'Apple'),
        ('phone', 'Phone Number'),
    ], string='Auth Provider', default='email')
    social_auth_id = fields.Char(string='Social Auth ID')

    # Password Reset
    reset_otp = fields.Char(string='Reset OTP')
    reset_otp_expiry = fields.Datetime(string='Reset OTP Expiry')

    # Islamic Preferences
    prayer_calculation_method = fields.Selection([
        ('mwl', 'Muslim World League'),
        ('isna', 'ISNA'),
        ('egypt', 'Egyptian Authority'),
        ('makkah', 'Umm al-Qura'),
        ('karachi', 'University of Karachi'),
        ('tehran', 'Tehran'),
        ('jafari', 'Shia Ithna-Ashari'),
    ], string='Prayer Calculation Method', default='mwl')
    madhab = fields.Selection([
        ('hanafi', 'Hanafi'),
        ('shafi', 'Shafi\'i'),
        ('maliki', 'Maliki'),
        ('hanbali', 'Hanbali'),
    ], string='Madhab (School of Thought)')
    quran_reciter_preference = fields.Char(string='Preferred Quran Reciter')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))

    # Statistics
    total_dhikr_count = fields.Integer(string='Total Dhikr Count', default=0)
    current_streak = fields.Integer(string='Current Streak (Days)', default=0)
    longest_streak = fields.Integer(string='Longest Streak (Days)', default=0)
    total_quran_pages_read = fields.Integer(string='Total Quran Pages Read', default=0)
    total_listening_minutes = fields.Float(string='Total Listening Minutes', default=0.0)

    # Subscription
    subscription_id = fields.Many2one('islamic.subscription', string='Active Subscription')

    # Notifications preferences
    prayer_notification = fields.Boolean(string='Prayer Time Notifications', default=True)
    adhkar_morning_notification = fields.Boolean(string='Morning Adhkar Reminder', default=True)
    adhkar_evening_notification = fields.Boolean(string='Evening Adhkar Reminder', default=True)
    family_ties_notification = fields.Boolean(string='Family Ties Reminders', default=True)
    wakeup_alarm = fields.Boolean(string='Wake-up Supplication Alarm', default=False)
    wakeup_alarm_time = fields.Float(string='Wake-up Alarm Time')

    _sql_constraints = [
        ('phone_unique', 'UNIQUE(phone_number)', 'Phone number must be unique!'),
    ]

    @api.depends('subscription_id', 'subscription_id.state', 'subscription_id.end_date')
    def _compute_is_premium(self):
        for rec in self:
            if rec.subscription_id and rec.subscription_id.state == 'active':
                if rec.subscription_id.plan_id.plan_type == 'lifetime':
                    rec.is_premium = True
                elif rec.subscription_id.end_date and rec.subscription_id.end_date >= fields.Date.today():
                    rec.is_premium = True
                else:
                    rec.is_premium = False
            else:
                rec.is_premium = False

    def generate_auth_tokens(self):
        """Generate JWT access and refresh tokens"""
        self.ensure_one()
        now = time.time()

        # Access token
        access_payload = {
            'uid': self.user_id.id,
            'app_user_id': self.id,
            'role': self.app_role,
            'lang': self.preferred_language,
            'is_premium': self.is_premium,
            'iat': now,
            'exp': now + (JWT_EXPIRY_HOURS * 3600),
        }
        access_token = generate_jwt(access_payload)

        # Refresh token
        refresh_token = secrets.token_urlsafe(64)
        self.write({
            'jwt_refresh_token': refresh_token,
            'jwt_refresh_expiry': datetime.now() + timedelta(days=JWT_REFRESH_EXPIRY_DAYS),
            'last_login': fields.Datetime.now(),
            'last_active': fields.Datetime.now(),
            'failed_login_attempts': 0,
        })

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': JWT_EXPIRY_HOURS * 3600,
            'token_type': 'Bearer',
        }

    @api.model
    def authenticate_user(self, login, password, auth_provider='email'):
        """Authenticate user and return tokens"""
        # Find app user by email or phone
        domain = [('is_locked', '=', False)]
        if '@' in login:
            user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        else:
            app_user = self.sudo().search([('phone_number', '=', login)], limit=1)
            user = app_user.user_id if app_user else False

        if not user:
            raise AccessDenied("Invalid credentials")

        app_user = self.sudo().search([('user_id', '=', user.id)], limit=1)
        if not app_user:
            raise AccessDenied("User not found in app")

        if app_user.is_locked and app_user.locked_until and app_user.locked_until > datetime.now():
            raise AccessDenied("Account is temporarily locked. Please try again later.")

        # Verify password
        try:
            self.env['res.users'].sudo().with_user(user)._check_credentials({'type': 'password', 'password': password}, {'interactive': False})
        except AccessDenied:
            app_user.sudo().write({
                'failed_login_attempts': app_user.failed_login_attempts + 1,
            })
            if app_user.failed_login_attempts >= 5:
                app_user.sudo().write({
                    'is_locked': True,
                    'locked_until': datetime.now() + timedelta(minutes=30),
                })
            raise AccessDenied("Invalid credentials")

        return app_user.generate_auth_tokens()

    @api.model
    def register_user(self, vals):
        """Register a new mobile app user"""
        # Validate required fields
        if not vals.get('email') and not vals.get('phone_number'):
            raise ValidationError("Email or phone number is required")

        # Create system user
        user_vals = {
            'name': vals.get('name', vals.get('email', vals.get('phone_number'))),
            'login': vals.get('email') or vals.get('phone_number'),
            'password': vals.get('password'),
            'group_ids': [Command.link(self.env.ref('islamic_app.group_islamic_app_user').id)],
        }
        if vals.get('email'):
            user_vals['email'] = vals['email']

        user = self.env['res.users'].sudo().create(user_vals)

        # Create app user profile
        app_user_vals = {
            'user_id': user.id,
            'display_name_app': vals.get('name'),
            'phone_number': vals.get('phone_number'),
            'preferred_language': vals.get('language', 'en'),
            'auth_provider': vals.get('auth_provider', 'email'),
            'social_auth_id': vals.get('social_auth_id'),
            'gender': vals.get('gender'),
            'device_type': vals.get('device_type'),
            'device_token_fcm': vals.get('device_token'),
        }
        app_user = self.sudo().create(app_user_vals)

        # Auto-create free subscription
        free_plan = self.env['islamic.subscription.plan'].sudo().search(
            [('plan_type', '=', 'free')], limit=1
        )
        if free_plan:
            self.env['islamic.subscription'].sudo().create({
                'app_user_id': app_user.id,
                'plan_id': free_plan.id,
                'state': 'active',
                'start_date': fields.Date.today(),
            })

        return app_user.generate_auth_tokens()

    def refresh_access_token(self, refresh_token):
        """Generate new access token using refresh token"""
        app_user = self.sudo().search([
            ('jwt_refresh_token', '=', refresh_token),
            ('jwt_refresh_expiry', '>', fields.Datetime.now()),
        ], limit=1)
        if not app_user:
            raise AccessDenied("Invalid or expired refresh token")
        return app_user.generate_auth_tokens()

    def update_device_info(self, device_data):
        """Update device token and info"""
        self.ensure_one()
        vals = {}
        if device_data.get('device_token'):
            vals['device_token_fcm'] = device_data['device_token']
        if device_data.get('device_type'):
            vals['device_type'] = device_data['device_type']
        if device_data.get('device_model'):
            vals['device_model'] = device_data['device_model']
        if device_data.get('app_version'):
            vals['app_version'] = device_data['app_version']
        vals['last_active'] = fields.Datetime.now()
        self.sudo().write(vals)

    def to_dict(self):
        """Serialize user profile for API response"""
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.display_name_app or self.name,
            'email': self.user_id.login if '@' in (self.user_id.login or '') else None,
            'phone': self.phone_number,
            'profile_image_url': self.profile_image_url,
            'language': self.preferred_language,
            'role': self.app_role,
            'is_premium': self.is_premium,
            'gender': self.gender,
            'country': self.country_id.name if self.country_id else None,
            'city': self.city,
            'prayer_method': self.prayer_calculation_method,
            'madhab': self.madhab,
            'stats': {
                'total_dhikr': self.total_dhikr_count,
                'current_streak': self.current_streak,
                'longest_streak': self.longest_streak,
                'quran_pages': self.total_quran_pages_read,
                'listening_minutes': round(self.total_listening_minutes, 1),
            },
            'notifications': {
                'prayer': self.prayer_notification,
                'morning_adhkar': self.adhkar_morning_notification,
                'evening_adhkar': self.adhkar_evening_notification,
                'family_ties': self.family_ties_notification,
                'wakeup_alarm': self.wakeup_alarm,
                'wakeup_time': self.wakeup_alarm_time,
            },
        }
