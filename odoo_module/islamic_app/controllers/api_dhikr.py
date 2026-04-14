import json
import logging
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body

_logger = logging.getLogger(__name__)


class IslamicDhikrController(http.Controller):

    @http.route('/api/v1/dhikr/log', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def log_dhikr(self, **kwargs):
        """Log dhikr counting session"""
        data = get_json_body()
        vals = {
            'app_user_id': request.app_user.id,
            'count': data.get('count', 0),
            'target_count': data.get('target', 0),
            'time_of_day': data.get('time_of_day', 'custom'),
            'date': fields.Date.today(),
        }
        if data.get('adhkar_id'):
            vals['adhkar_id'] = data['adhkar_id']
        elif data.get('custom_text'):
            vals['custom_dhikr_text'] = data['custom_text']

        if data.get('session_start'):
            vals['session_start'] = data['session_start']
        if data.get('session_end'):
            vals['session_end'] = data['session_end']

        log = request.env['islamic.dhikr.log'].sudo().create(vals)

        # Update user total
        request.app_user.sudo().write({
            'total_dhikr_count': request.app_user.total_dhikr_count + data.get('count', 0),
        })

        # Update streak
        streak_model = request.env['islamic.dhikr.streak'].sudo()
        today = fields.Date.today()
        streak_rec = streak_model.search([
            ('app_user_id', '=', request.app_user.id),
            ('date', '=', today),
        ], limit=1)
        if streak_rec:
            streak_rec.write({
                'has_activity': True,
                'total_count': streak_rec.total_count + data.get('count', 0),
                'sessions': streak_rec.sessions + 1,
            })
        else:
            streak_model.create({
                'app_user_id': request.app_user.id,
                'date': today,
                'has_activity': True,
                'total_count': data.get('count', 0),
                'sessions': 1,
            })

        # Recalculate streak
        current_streak = streak_model.update_streak(request.app_user.id)

        return json_response({
            'success': True,
            'data': {
                'log_id': log.id,
                'total_dhikr': request.app_user.total_dhikr_count,
                'current_streak': current_streak,
            },
        }, 201)

    @http.route('/api/v1/dhikr/increment', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def increment_dhikr(self, **kwargs):
        """Quick increment for active counting session"""
        data = get_json_body()
        log_id = data.get('log_id')
        amount = data.get('amount', 1)

        if log_id:
            log = request.env['islamic.dhikr.log'].sudo().search([
                ('id', '=', log_id),
                ('app_user_id', '=', request.app_user.id),
            ], limit=1)
            if log:
                log.increment_count(amount)
                return json_response({
                    'success': True,
                    'data': {'count': log.count, 'completed': log.completed},
                })
        return error_response('Log not found', 404)

    @http.route('/api/v1/dhikr/stats', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_stats(self, **kwargs):
        """Get dhikr statistics"""
        user = request.app_user
        today = fields.Date.today()

        # Today's stats
        today_logs = request.env['islamic.dhikr.log'].sudo().search([
            ('app_user_id', '=', user.id),
            ('date', '=', today),
        ])
        today_count = sum(today_logs.mapped('count'))
        today_sessions = len(today_logs)

        # Week stats
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        week_logs = request.env['islamic.dhikr.log'].sudo().search([
            ('app_user_id', '=', user.id),
            ('date', '>=', week_start),
            ('date', '<=', today),
        ])
        week_count = sum(week_logs.mapped('count'))

        # Monthly stats
        month_start = today.replace(day=1)
        month_logs = request.env['islamic.dhikr.log'].sudo().search([
            ('app_user_id', '=', user.id),
            ('date', '>=', month_start),
            ('date', '<=', today),
        ])
        month_count = sum(month_logs.mapped('count'))

        # Daily breakdown for the week
        daily_data = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_logs = request.env['islamic.dhikr.log'].sudo().search([
                ('app_user_id', '=', user.id),
                ('date', '=', day),
            ])
            daily_data.append({
                'date': day.isoformat(),
                'count': sum(day_logs.mapped('count')),
                'sessions': len(day_logs),
            })

        return json_response({
            'success': True,
            'data': {
                'today': {'count': today_count, 'sessions': today_sessions},
                'week': {'count': week_count},
                'month': {'count': month_count},
                'total': user.total_dhikr_count,
                'current_streak': user.current_streak,
                'longest_streak': user.longest_streak,
                'daily_breakdown': daily_data,
            },
        })

    @http.route('/api/v1/dhikr/history', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_history(self, **kwargs):
        """Get dhikr history"""
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit

        logs = request.env['islamic.dhikr.log'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
        ], limit=limit, offset=offset, order='date desc, create_date desc')

        return json_response({
            'success': True,
            'data': [l.to_dict() for l in logs],
        })

    @http.route('/api/v1/dhikr/custom', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_custom_dhikr(self, **kwargs):
        """Get user's custom dhikr list"""
        customs = request.env['islamic.dhikr.custom'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
        ], order='sequence')
        return json_response({
            'success': True,
            'data': [c.to_dict() for c in customs],
        })

    @http.route('/api/v1/dhikr/custom', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def create_custom_dhikr(self, **kwargs):
        """Create a custom dhikr"""
        data = get_json_body()
        # Check limit for free users
        if not request.app_user.is_premium:
            count = request.env['islamic.dhikr.custom'].sudo().search_count([
                ('app_user_id', '=', request.app_user.id),
            ])
            if count >= 3:
                return error_response('Free users can create up to 3 custom dhikr. Upgrade to premium.', 403)

        custom = request.env['islamic.dhikr.custom'].sudo().create({
            'app_user_id': request.app_user.id,
            'name': data.get('name'),
            'arabic_text': data.get('arabic_text'),
            'target_count': data.get('target_count', 33),
            'icon': data.get('icon'),
            'color': data.get('color'),
        })
        return json_response({'success': True, 'data': custom.to_dict()}, 201)

    @http.route('/api/v1/dhikr/custom/<int:custom_id>', type='http', auth='public',
                methods=['DELETE'], csrf=False, cors='*')
    @jwt_required
    def delete_custom_dhikr(self, custom_id, **kwargs):
        custom = request.env['islamic.dhikr.custom'].sudo().search([
            ('id', '=', custom_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not custom:
            return error_response('Not found', 404)
        custom.unlink()
        return json_response({'success': True})
