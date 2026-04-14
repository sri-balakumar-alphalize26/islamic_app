import json
import logging
import functools
from odoo import http, fields
from odoo.http import request, Response
from odoo.exceptions import AccessDenied, ValidationError
from ..models.islamic_user import verify_jwt

_logger = logging.getLogger(__name__)


def json_response(data, status=200):
    """Helper to return JSON responses"""
    return Response(
        json.dumps(data, default=str),
        status=status,
        content_type='application/json',
    )


def error_response(message, status=400, code=None):
    """Helper to return error responses"""
    body = {'error': True, 'message': message}
    if code:
        body['code'] = code
    return json_response(body, status=status)


def jwt_required(f):
    """Decorator to require JWT authentication on API endpoints"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return error_response('Missing or invalid authorization header', 401, 'AUTH_REQUIRED')

        token = auth_header[7:]
        payload = verify_jwt(token)
        if not payload:
            return error_response('Invalid or expired token', 401, 'TOKEN_EXPIRED')

        # Attach user info to request
        app_user = request.env['islamic.app.user'].sudo().browse(payload.get('app_user_id'))
        if not app_user.exists():
            return error_response('User not found', 401, 'USER_NOT_FOUND')

        request.app_user = app_user
        request.app_user_payload = payload

        # Update last active
        app_user.sudo().write({'last_active': fields.Datetime.now()})

        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Decorator to require admin or special user role"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(request, 'app_user'):
            return error_response('Authentication required', 401)
        if request.app_user.app_role not in ('admin', 'special'):
            return error_response('Admin access required', 403, 'ADMIN_REQUIRED')
        return f(*args, **kwargs)
    return wrapper


def get_json_body():
    """Parse JSON body from request"""
    try:
        return json.loads(request.httprequest.data)
    except (json.JSONDecodeError, TypeError):
        return {}


def get_lang():
    """Get preferred language from request.
    Priority: Accept-Language header > user preference > default 'en'.
    Header takes priority so language changes take effect immediately."""
    header_lang = request.httprequest.headers.get('Accept-Language', '')[:2]
    if header_lang in ('en', 'ar', 'fr', 'tr', 'hi'):
        return header_lang
    if hasattr(request, 'app_user') and request.app_user:
        return request.app_user.preferred_language or 'en'
    return 'en'


class IslamicAuthController(http.Controller):
    """Authentication API endpoints"""

    @http.route('/api/v1/auth/register', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def register(self, **kwargs):
        """Register a new user"""
        try:
            data = get_json_body()

            required = ['password']
            if not data.get('email') and not data.get('phone_number'):
                return error_response('Email or phone number is required')

            if not data.get('password') or len(data['password']) < 6:
                return error_response('Password must be at least 6 characters')

            # Check if email already exists
            if data.get('email'):
                existing = request.env['res.users'].sudo().search([
                    ('login', '=', data['email'])
                ], limit=1)
                if existing:
                    return error_response('Email already registered', 409, 'EMAIL_EXISTS')

            # Check if phone already exists
            if data.get('phone_number'):
                existing = request.env['islamic.app.user'].sudo().search([
                    ('phone_number', '=', data['phone_number'])
                ], limit=1)
                if existing:
                    return error_response('Phone number already registered', 409, 'PHONE_EXISTS')

            tokens = request.env['islamic.app.user'].sudo().register_user({
                'name': data.get('name', ''),
                'email': data.get('email'),
                'phone_number': data.get('phone_number'),
                'password': data['password'],
                'language': data.get('language', 'en'),
                'auth_provider': data.get('auth_provider', 'email'),
                'social_auth_id': data.get('social_auth_id'),
                'gender': data.get('gender'),
                'device_type': data.get('device_type'),
                'device_token': data.get('device_token'),
            })

            return json_response({
                'success': True,
                'message': 'Registration successful',
                'data': tokens,
            }, 201)

        except ValidationError as e:
            return error_response(str(e))
        except Exception as e:
            _logger.exception("Registration error")
            return error_response('Registration failed. Please try again.', 500)

    @http.route('/api/v1/auth/login', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def login(self, **kwargs):
        """Login with email/phone and password"""
        try:
            data = get_json_body()
            login = data.get('email') or data.get('phone') or data.get('login')
            password = data.get('password')

            if not login or not password:
                return error_response('Email/phone and password are required')

            tokens = request.env['islamic.app.user'].sudo().authenticate_user(
                login, password, data.get('auth_provider', 'email')
            )

            # Update device info if provided
            if data.get('device_token') or data.get('device_type'):
                app_user = request.env['islamic.app.user'].sudo().search([
                    ('jwt_refresh_token', '=', tokens['refresh_token'])
                ], limit=1)
                if app_user:
                    app_user.update_device_info(data)

            return json_response({
                'success': True,
                'message': 'Login successful',
                'data': tokens,
            })

        except AccessDenied as e:
            return error_response(str(e), 401, 'INVALID_CREDENTIALS')
        except Exception as e:
            _logger.exception("Login error")
            return error_response('Login failed', 500)

    @http.route('/api/v1/auth/refresh', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def refresh_token(self, **kwargs):
        """Refresh access token"""
        try:
            data = get_json_body()
            refresh_token = data.get('refresh_token')
            if not refresh_token:
                return error_response('Refresh token is required')

            tokens = request.env['islamic.app.user'].sudo().refresh_access_token(refresh_token)
            return json_response({
                'success': True,
                'data': tokens,
            })

        except AccessDenied as e:
            return error_response(str(e), 401, 'TOKEN_EXPIRED')
        except Exception as e:
            _logger.exception("Token refresh error")
            return error_response('Token refresh failed', 500)

    @http.route('/api/v1/auth/social', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def social_login(self, **kwargs):
        """Social authentication (Google, Apple)"""
        try:
            data = get_json_body()
            provider = data.get('provider')  # 'google' or 'apple'
            social_token = data.get('token')
            social_id = data.get('social_id')

            if not provider or not social_id:
                return error_response('Provider and social ID are required')

            # Check if user exists with this social ID
            app_user = request.env['islamic.app.user'].sudo().search([
                ('auth_provider', '=', provider),
                ('social_auth_id', '=', social_id),
            ], limit=1)

            if app_user:
                # Existing user - generate tokens
                tokens = app_user.generate_auth_tokens()
            else:
                # New user - register
                tokens = request.env['islamic.app.user'].sudo().register_user({
                    'name': data.get('name', ''),
                    'email': data.get('email'),
                    'password': social_id + '_social_auth',
                    'language': data.get('language', 'en'),
                    'auth_provider': provider,
                    'social_auth_id': social_id,
                    'device_type': data.get('device_type'),
                    'device_token': data.get('device_token'),
                })

            return json_response({
                'success': True,
                'data': tokens,
            })

        except Exception as e:
            _logger.exception("Social login error")
            return error_response('Social authentication failed', 500)

    @http.route('/api/v1/auth/logout', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def logout(self, **kwargs):
        """Logout and invalidate refresh token"""
        try:
            request.app_user.sudo().write({
                'jwt_refresh_token': False,
                'jwt_refresh_expiry': False,
                'device_token_fcm': False,
            })
            return json_response({'success': True, 'message': 'Logged out successfully'})
        except Exception as e:
            return error_response('Logout failed', 500)

    @http.route('/api/v1/auth/forgot-password', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def forgot_password(self, **kwargs):
        """Send a 6-digit OTP to the user's email for password reset."""
        import random
        try:
            data = get_json_body()
            email = data.get('email', '').strip().lower()
            if not email:
                return error_response('Email is required')

            # Always return success to prevent email enumeration
            success_msg = 'If an account exists with this email, a reset code has been sent'

            app_user = request.env['islamic.app.user'].sudo().search([
                ('user_id.login', '=', email)
            ], limit=1)
            if not app_user:
                return json_response({'success': True, 'message': success_msg})

            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            expiry = fields.Datetime.now() + __import__('datetime').timedelta(minutes=15)
            app_user.sudo().write({
                'reset_otp': otp,
                'reset_otp_expiry': expiry,
            })
            _logger.info(f"Password reset OTP for {email}: {otp}")

            # Try to send email via Odoo (best-effort)
            try:
                template_body = (
                    f"<p>Your password reset code is: <b>{otp}</b></p>"
                    f"<p>This code expires in 15 minutes.</p>"
                    f"<p>If you did not request this, please ignore this email.</p>"
                )
                mail_values = {
                    'subject': 'Islamic App - Password Reset Code',
                    'body_html': template_body,
                    'email_to': email,
                    'email_from': request.env.company.sudo().email or 'noreply@islamicapp.com',
                    'auto_delete': True,
                }
                request.env['mail.mail'].sudo().create(mail_values).send()
                _logger.info(f"Reset email sent to {email}")
            except Exception as mail_err:
                _logger.warning(f"Could not send reset email: {mail_err}")
                # OTP is still stored — admin can check logs if email fails

            # DEV MODE: include OTP in response for testing (remove in production!)
            return json_response({'success': True, 'message': success_msg, 'dev_otp': otp})

        except Exception as e:
            _logger.exception("Forgot password error")
            return error_response('Password reset failed', 500)

    @http.route('/api/v1/auth/reset-password', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    def reset_password(self, **kwargs):
        """Verify OTP and reset the password."""
        try:
            data = get_json_body()
            email = data.get('email', '').strip().lower()
            otp = data.get('otp', '').strip()
            new_password = data.get('new_password', '')

            if not email or not otp or not new_password:
                return error_response('Email, OTP, and new password are required')
            if len(new_password) < 6:
                return error_response('Password must be at least 6 characters')

            app_user = request.env['islamic.app.user'].sudo().search([
                ('user_id.login', '=', email)
            ], limit=1)
            if not app_user:
                return error_response('Invalid code or email', 400, 'INVALID_OTP')

            # Verify OTP and expiry
            if not app_user.reset_otp or app_user.reset_otp != otp:
                return error_response('Invalid reset code', 400, 'INVALID_OTP')
            if app_user.reset_otp_expiry and app_user.reset_otp_expiry < fields.Datetime.now():
                return error_response('Reset code has expired. Please request a new one.', 400, 'OTP_EXPIRED')

            # Reset password
            app_user.user_id.sudo().write({'password': new_password})
            # Clear OTP
            app_user.sudo().write({'reset_otp': False, 'reset_otp_expiry': False})
            _logger.info(f"Password reset successful for {email}")

            return json_response({
                'success': True,
                'message': 'Password reset successful. You can now sign in.',
            })

        except Exception as e:
            _logger.exception("Reset password error")
            return error_response('Password reset failed', 500)
