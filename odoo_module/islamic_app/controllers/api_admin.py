import json
import logging
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, admin_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicAdminController(http.Controller):

    # ── Content Management ──
    @http.route('/api/v1/admin/content', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    @admin_required
    def create_content(self, **kwargs):
        data = get_json_body()
        vals = {
            'name': data.get('title_en'),
            'title_ar': data.get('title_ar'),
            'title_fr': data.get('title_fr'),
            'title_tr': data.get('title_tr'),
            'title_hi': data.get('title_hi'),
            'content_type': data.get('content_type'),
            'body_en': data.get('body_en'),
            'body_ar': data.get('body_ar'),
            'body_fr': data.get('body_fr'),
            'body_tr': data.get('body_tr'),
            'body_hi': data.get('body_hi'),
            'arabic_text': data.get('arabic_text'),
            'reference': data.get('reference'),
            'state': 'draft',
            'author_id': request.app_user.id,
            'is_featured': data.get('is_featured', False),
            'is_daily': data.get('is_daily', False),
            'scheduled_date': data.get('scheduled_date'),
        }
        if data.get('category_code'):
            cat = request.env['islamic.content.category'].sudo().search(
                [('code', '=', data['category_code'])], limit=1)
            if cat:
                vals['category_id'] = cat.id

        content = request.env['islamic.content'].sudo().create(vals)
        lang = get_lang()
        return json_response({'success': True, 'data': content.to_dict(lang)}, 201)

    @http.route('/api/v1/admin/content/<int:content_id>', type='http', auth='public',
                methods=['PUT'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def update_content(self, content_id, **kwargs):
        data = get_json_body()
        content = request.env['islamic.content'].sudo().browse(content_id)
        if not content.exists():
            return error_response('Content not found', 404)

        allowed = {
            'name', 'title_ar', 'title_fr', 'title_tr', 'title_hi',
            'body_en', 'body_ar', 'body_fr', 'body_tr', 'body_hi',
            'arabic_text', 'reference', 'is_featured', 'is_daily',
            'scheduled_date', 'content_type', 'image_url',
        }
        vals = {k: v for k, v in data.items() if k in allowed}
        if vals:
            content.write(vals)
        lang = get_lang()
        return json_response({'success': True, 'data': content.to_dict(lang)})

    @http.route('/api/v1/admin/content/<int:content_id>/publish', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def publish_content(self, content_id, **kwargs):
        content = request.env['islamic.content'].sudo().browse(content_id)
        if not content.exists():
            return error_response('Not found', 404)
        content.write({'state': 'published', 'published_date': fields.Datetime.now()})
        return json_response({'success': True})

    # ── Adhkar Management ──
    @http.route('/api/v1/admin/adhkar', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    @admin_required
    def create_adhkar(self, **kwargs):
        data = get_json_body()
        vals = {
            'name': data.get('title_en'),
            'name_ar': data.get('title_ar'),
            'name_fr': data.get('title_fr'),
            'name_tr': data.get('title_tr'),
            'name_hi': data.get('title_hi'),
            'arabic_text': data.get('arabic_text'),
            'arabic_diacritics': data.get('arabic_diacritics'),
            'translation_en': data.get('translation_en'),
            'translation_fr': data.get('translation_fr'),
            'translation_tr': data.get('translation_tr'),
            'translation_hi': data.get('translation_hi'),
            'transliteration_en': data.get('transliteration_en'),
            'reference': data.get('reference'),
            'repeat_count': data.get('repeat_count', 1),
            'time_of_day': data.get('time_of_day', 'anytime'),
            'virtue_en': data.get('virtue_en'),
            'virtue_ar': data.get('virtue_ar'),
            'state': 'draft',
        }
        if data.get('category_code'):
            cat = request.env['islamic.adhkar.category'].sudo().search(
                [('code', '=', data['category_code'])], limit=1)
            if cat:
                vals['category_id'] = cat.id

        adhkar = request.env['islamic.adhkar'].sudo().create(vals)
        lang = get_lang()
        return json_response({'success': True, 'data': adhkar.to_dict(lang)}, 201)

    @http.route('/api/v1/admin/adhkar/<int:adhkar_id>/publish', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def publish_adhkar(self, adhkar_id, **kwargs):
        adhkar = request.env['islamic.adhkar'].sudo().browse(adhkar_id)
        if not adhkar.exists():
            return error_response('Not found', 404)
        adhkar.write({'state': 'published'})
        return json_response({'success': True})

    # ── Audio Management ──
    @http.route('/api/v1/admin/audio/<int:audio_id>/publish', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def publish_audio(self, audio_id, **kwargs):
        audio = request.env['islamic.audio'].sudo().browse(audio_id)
        if not audio.exists():
            return error_response('Not found', 404)
        audio.action_publish()
        return json_response({'success': True})

    # ── User Management ──
    @http.route('/api/v1/admin/users', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    @admin_required
    def list_users(self, **kwargs):
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit
        search = kwargs.get('search', '')

        domain = []
        if search:
            domain = ['|', '|',
                ('display_name_app', 'ilike', search),
                ('phone_number', 'ilike', search),
                ('user_id.login', 'ilike', search),
            ]

        users = request.env['islamic.app.user'].sudo().search(
            domain, limit=limit, offset=offset, order='create_date desc')
        total = request.env['islamic.app.user'].sudo().search_count(domain)

        return json_response({
            'success': True,
            'data': [u.to_dict() for u in users],
            'pagination': {'page': page, 'limit': limit, 'total': total},
        })

    @http.route('/api/v1/admin/users/<int:user_id>/role', type='http', auth='public',
                methods=['PUT'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def update_user_role(self, user_id, **kwargs):
        data = get_json_body()
        user = request.env['islamic.app.user'].sudo().browse(user_id)
        if not user.exists():
            return error_response('User not found', 404)
        role = data.get('role')
        if role not in ('user', 'special', 'admin'):
            return error_response('Invalid role')

        # Only full admins can promote to admin
        if role == 'admin' and request.app_user.app_role != 'admin':
            return error_response('Only admins can promote to admin', 403)

        user.write({'app_role': role})
        return json_response({'success': True})

    # ── Analytics Dashboard ──
    @http.route('/api/v1/admin/analytics/overview', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def analytics_overview(self, **kwargs):
        today = fields.Date.today()
        from datetime import timedelta
        last_30 = today - timedelta(days=30)
        last_7 = today - timedelta(days=7)

        total_users = request.env['islamic.app.user'].sudo().search_count([])
        new_users_30d = request.env['islamic.app.user'].sudo().search_count([
            ('create_date', '>=', last_30)])
        new_users_7d = request.env['islamic.app.user'].sudo().search_count([
            ('create_date', '>=', last_7)])
        active_users_7d = request.env['islamic.app.user'].sudo().search_count([
            ('last_active', '>=', last_7)])
        premium_users = request.env['islamic.app.user'].sudo().search_count([
            ('is_premium', '=', True)])
        total_revenue = sum(request.env['islamic.payment'].sudo().search([
            ('state', '=', 'completed'),
        ]).mapped('amount'))
        revenue_30d = sum(request.env['islamic.payment'].sudo().search([
            ('state', '=', 'completed'),
            ('create_date', '>=', last_30),
        ]).mapped('amount'))
        total_dhikr_today = sum(request.env['islamic.dhikr.log'].sudo().search([
            ('date', '=', today),
        ]).mapped('count'))
        ai_queries_today = request.env['islamic.ai.query.log'].sudo().search_count([
            ('date', '=', today)])

        return json_response({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'new_30d': new_users_30d,
                    'new_7d': new_users_7d,
                    'active_7d': active_users_7d,
                    'premium': premium_users,
                },
                'revenue': {
                    'total': round(total_revenue, 2),
                    'last_30d': round(revenue_30d, 2),
                },
                'engagement': {
                    'dhikr_today': total_dhikr_today,
                    'ai_queries_today': ai_queries_today,
                },
            },
        })

    @http.route('/api/v1/admin/analytics/content', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    @admin_required
    def analytics_content(self, **kwargs):
        total_surahs = request.env['islamic.surah'].sudo().search_count([])
        total_adhkar = request.env['islamic.adhkar'].sudo().search_count([('state', '=', 'published')])
        total_audio = request.env['islamic.audio'].sudo().search_count([('state', '=', 'published')])
        total_content = request.env['islamic.content'].sudo().search_count([('state', '=', 'published')])
        pending_audio = request.env['islamic.audio'].sudo().search_count([('state', '=', 'draft')])
        pending_content = request.env['islamic.content'].sudo().search_count([('state', '=', 'draft')])

        return json_response({
            'success': True,
            'data': {
                'surahs': total_surahs,
                'adhkar_published': total_adhkar,
                'audio_published': total_audio,
                'content_published': total_content,
                'audio_pending': pending_audio,
                'content_pending': pending_content,
            },
        })
