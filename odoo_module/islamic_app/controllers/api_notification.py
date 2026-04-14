import json
import logging
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicNotificationController(http.Controller):

    @http.route('/api/v1/notifications', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_notifications(self, **kwargs):
        lang = get_lang()
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit
        unread_only = kwargs.get('unread', '0') == '1'

        domain = [('app_user_id', '=', request.app_user.id)]
        if unread_only:
            domain.append(('is_read', '=', False))

        notifs = request.env['islamic.notification'].sudo().search(
            domain, limit=limit, offset=offset, order='create_date desc')
        total = request.env['islamic.notification'].sudo().search_count(domain)
        unread_count = request.env['islamic.notification'].sudo().search_count([
            ('app_user_id', '=', request.app_user.id),
            ('is_read', '=', False),
        ])

        return json_response({
            'success': True,
            'data': [n.to_dict(lang) for n in notifs],
            'unread_count': unread_count,
            'pagination': {'page': page, 'limit': limit, 'total': total},
        })

    @http.route('/api/v1/notifications/<int:notif_id>/read', type='http', auth='public',
                methods=['PUT'], csrf=False, cors='*')
    @jwt_required
    def mark_read(self, notif_id, **kwargs):
        notif = request.env['islamic.notification'].sudo().search([
            ('id', '=', notif_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if notif:
            notif.mark_as_read()
        return json_response({'success': True})

    @http.route('/api/v1/notifications/read-all', type='http', auth='public',
                methods=['PUT'], csrf=False, cors='*')
    @jwt_required
    def mark_all_read(self, **kwargs):
        notifs = request.env['islamic.notification'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
            ('is_read', '=', False),
        ])
        notifs.mark_as_read()
        return json_response({'success': True, 'count': len(notifs)})

    @http.route('/api/v1/prayer-times', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_prayer_times(self, **kwargs):
        """Get prayer times for today (or specified date)"""
        date_str = kwargs.get('date')
        if date_str:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = fields.Date.today()

        prayer = request.env['islamic.prayer.time'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
            ('date', '=', date),
        ], limit=1)

        if prayer:
            return json_response({'success': True, 'data': prayer.to_dict()})

        # Calculate prayer times if not cached
        # In production, use a prayer time calculation library
        return json_response({
            'success': True,
            'data': {
                'date': date.isoformat(),
                'message': 'Prayer times should be calculated on client using location',
                'calculation_method': request.app_user.prayer_calculation_method,
                'latitude': request.app_user.latitude,
                'longitude': request.app_user.longitude,
            },
        })
