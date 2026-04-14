import json
import logging
import base64
from odoo import http
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicUserController(http.Controller):

    @http.route('/api/v1/user/profile', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_profile(self, **kwargs):
        """Get current user profile"""
        return json_response({
            'success': True,
            'data': request.app_user.to_dict(),
        })

    @http.route('/api/v1/user/profile', type='http', auth='public', methods=['PUT'],
                csrf=False, cors='*')
    @jwt_required
    def update_profile(self, **kwargs):
        """Update user profile"""
        try:
            data = get_json_body()
            allowed_fields = {
                'display_name_app', 'phone_number', 'date_of_birth', 'gender',
                'bio', 'city', 'preferred_language', 'prayer_calculation_method',
                'madhab', 'quran_reciter_preference', 'latitude', 'longitude',
                'timezone',
            }
            vals = {k: v for k, v in data.items() if k in allowed_fields}

            if 'profile_image_base64' in data:
                vals['profile_image'] = base64.b64decode(data['profile_image_base64'])

            if vals:
                request.app_user.sudo().write(vals)

            return json_response({
                'success': True,
                'data': request.app_user.to_dict(),
            })
        except Exception as e:
            _logger.exception("Profile update error")
            return error_response(str(e), 500)

    @http.route('/api/v1/user/notifications/settings', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_notification_settings(self, **kwargs):
        """Get notification preferences"""
        user = request.app_user
        return json_response({
            'success': True,
            'data': {
                'prayer_notification': user.prayer_notification,
                'adhkar_morning_notification': user.adhkar_morning_notification,
                'adhkar_evening_notification': user.adhkar_evening_notification,
                'family_ties_notification': user.family_ties_notification,
                'wakeup_alarm': user.wakeup_alarm,
                'wakeup_alarm_time': user.wakeup_alarm_time,
            },
        })

    @http.route('/api/v1/user/notifications/settings', type='http', auth='public', methods=['PUT'],
                csrf=False, cors='*')
    @jwt_required
    def update_notification_settings(self, **kwargs):
        """Update notification preferences"""
        data = get_json_body()
        allowed = {
            'prayer_notification', 'adhkar_morning_notification',
            'adhkar_evening_notification', 'family_ties_notification',
            'wakeup_alarm', 'wakeup_alarm_time',
        }
        vals = {k: v for k, v in data.items() if k in allowed}
        if vals:
            request.app_user.sudo().write(vals)
        return json_response({'success': True})

    @http.route('/api/v1/user/device', type='http', auth='public', methods=['PUT'],
                csrf=False, cors='*')
    @jwt_required
    def update_device(self, **kwargs):
        """Update device token and info"""
        data = get_json_body()
        request.app_user.update_device_info(data)
        return json_response({'success': True})

    @http.route('/api/v1/user/stats', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_stats(self, **kwargs):
        """Get user statistics"""
        user = request.app_user
        return json_response({
            'success': True,
            'data': {
                'total_dhikr': user.total_dhikr_count,
                'current_streak': user.current_streak,
                'longest_streak': user.longest_streak,
                'quran_pages': user.total_quran_pages_read,
                'listening_minutes': round(user.total_listening_minutes, 1),
                'is_premium': user.is_premium,
                'member_since': user.create_date.isoformat() if user.create_date else None,
            },
        })

    @http.route('/api/v1/user/listening', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def log_listening(self, **kwargs):
        """Log audio listening duration in minutes"""
        try:
            data = get_json_body()
            minutes = float(data.get('minutes', 0))
            if minutes <= 0:
                return error_response('Invalid duration')
            # Cap per-session log at 3 hours to prevent bad data
            minutes = min(minutes, 180)
            user = request.app_user
            user.sudo().write({
                'total_listening_minutes': user.total_listening_minutes + minutes,
            })
            return json_response({
                'success': True,
                'data': {
                    'total_listening_minutes': round(user.total_listening_minutes, 1),
                },
            })
        except Exception as e:
            _logger.exception("Listening log error")
            return error_response(str(e), 500)

    @http.route('/api/v1/user/pages', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def log_pages(self, **kwargs):
        """Log Quran pages read when user finishes reading a surah.
        Uses standard approximation: 1 page ≈ 15 ayahs (Uthmani Mushaf)."""
        try:
            data = get_json_body()
            ayah_count = int(data.get('ayah_count', 0))
            if ayah_count <= 0:
                return error_response('Invalid ayah count')
            pages = max(1, round(ayah_count / 15))
            user = request.app_user
            user.sudo().write({
                'total_quran_pages_read': user.total_quran_pages_read + pages,
            })
            return json_response({
                'success': True,
                'data': {
                    'pages_added': pages,
                    'total_pages': user.total_quran_pages_read,
                },
            })
        except Exception as e:
            _logger.exception("Pages log error")
            return error_response(str(e), 500)

    @http.route('/api/v1/user/language', type='http', auth='public', methods=['PUT'],
                csrf=False, cors='*')
    @jwt_required
    def change_language(self, **kwargs):
        """Change preferred language"""
        data = get_json_body()
        lang = data.get('language')
        if lang not in ('en', 'ar', 'fr', 'tr', 'hi'):
            return error_response('Invalid language code')
        request.app_user.sudo().write({'preferred_language': lang})
        return json_response({'success': True, 'language': lang})

    @http.route('/api/v1/user/delete-account', type='http', auth='public', methods=['DELETE'],
                csrf=False, cors='*')
    @jwt_required
    def delete_account(self, **kwargs):
        """Delete user account (GDPR compliance)"""
        try:
            user = request.app_user
            system_user = user.user_id
            user.sudo().unlink()
            system_user.sudo().write({'active': False})
            return json_response({'success': True, 'message': 'Account deleted successfully'})
        except Exception as e:
            return error_response('Account deletion failed', 500)
