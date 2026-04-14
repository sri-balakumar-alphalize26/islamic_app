import json
import logging
from odoo import http
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicContentController(http.Controller):

    @http.route('/api/v1/content/surahs', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_surahs(self, **kwargs):
        """Get list of all surahs"""
        lang = get_lang()
        surahs = request.env['islamic.surah'].sudo().search([], order='number')
        return json_response({
            'success': True,
            'data': [s.to_dict(lang) for s in surahs],
        })

    @http.route('/api/v1/content/surahs/<int:surah_number>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_surah(self, surah_number, **kwargs):
        """Get a single surah with its ayahs"""
        lang = get_lang()
        surah = request.env['islamic.surah'].sudo().search([('number', '=', surah_number)], limit=1)
        if not surah:
            return error_response('Surah not found', 404)

        include_tafsir = kwargs.get('tafsir', '0') == '1'
        data = surah.to_dict(lang)
        data['ayahs'] = [a.to_dict(lang, include_tafsir) for a in surah.ayah_ids.sorted('number')]
        return json_response({'success': True, 'data': data})

    @http.route('/api/v1/content/ayahs/<int:surah_number>/<int:ayah_number>', type='http',
                auth='public', methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_ayah(self, surah_number, ayah_number, **kwargs):
        """Get a specific ayah"""
        lang = get_lang()
        ayah = request.env['islamic.ayah'].sudo().search([
            ('surah_id.number', '=', surah_number),
            ('number', '=', ayah_number),
        ], limit=1)
        if not ayah:
            return error_response('Ayah not found', 404)
        return json_response({
            'success': True,
            'data': ayah.to_dict(lang, include_tafsir=True),
        })

    @http.route('/api/v1/content/ayahs/page/<int:page_number>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_page(self, page_number, **kwargs):
        """Get all ayahs on a specific page"""
        lang = get_lang()
        ayahs = request.env['islamic.ayah'].sudo().search([
            ('page', '=', page_number),
        ], order='surah_id, number')
        return json_response({
            'success': True,
            'data': {
                'page': page_number,
                'ayahs': [a.to_dict(lang) for a in ayahs],
            },
        })

    @http.route('/api/v1/content/juz/<int:juz_number>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_juz(self, juz_number, **kwargs):
        """Get all ayahs in a specific juz"""
        lang = get_lang()
        ayahs = request.env['islamic.ayah'].sudo().search([
            ('juz', '=', juz_number),
        ], order='surah_id, number')
        return json_response({
            'success': True,
            'data': {
                'juz': juz_number,
                'ayah_count': len(ayahs),
                'ayahs': [a.to_dict(lang) for a in ayahs],
            },
        })

    @http.route('/api/v1/content/search', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def search_content(self, **kwargs):
        """Search across Quran and content"""
        lang = get_lang()
        query = kwargs.get('q', '')
        search_type = kwargs.get('type', 'all')  # all, quran, content
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit

        results = {'quran': [], 'content': []}

        if search_type in ('all', 'quran'):
            # Search in translations based on language
            lang_field = f'translation_{lang}' if lang != 'ar' else 'text_arabic'
            domain = ['|', (lang_field, 'ilike', query), ('text_arabic', 'ilike', query)]
            ayahs = request.env['islamic.ayah'].sudo().search(domain, limit=limit, offset=offset)
            results['quran'] = [a.to_dict(lang) for a in ayahs]

        if search_type in ('all', 'content'):
            content = request.env['islamic.content'].sudo().search([
                ('state', '=', 'published'),
                '|', ('name', 'ilike', query), ('body_en', 'ilike', query),
            ], limit=limit, offset=offset)
            results['content'] = [c.to_dict(lang) for c in content]

        return json_response({'success': True, 'data': results, 'query': query, 'page': page})

    @http.route('/api/v1/content/daily-wisdom', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_daily_wisdom(self, **kwargs):
        """Get today's daily wisdom content"""
        lang = get_lang()
        from odoo import fields as f
        today = f.Date.today()
        wisdom = request.env['islamic.content'].sudo().search([
            ('content_type', '=', 'daily_wisdom'),
            ('state', '=', 'published'),
            '|',
            ('scheduled_date', '=', today),
            ('scheduled_date', '=', False),
        ], limit=1, order='scheduled_date desc, create_date desc')

        if not wisdom:
            wisdom = request.env['islamic.content'].sudo().search([
                ('content_type', '=', 'daily_wisdom'),
                ('state', '=', 'published'),
            ], limit=1, order='create_date desc')

        return json_response({
            'success': True,
            'data': wisdom.to_dict(lang) if wisdom else None,
        })

    @http.route('/api/v1/content/featured', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_featured(self, **kwargs):
        """Get featured content for home screen"""
        lang = get_lang()
        featured = request.env['islamic.content'].sudo().search([
            ('state', '=', 'published'),
            ('is_featured', '=', True),
        ], limit=10, order='sequence, create_date desc')
        return json_response({
            'success': True,
            'data': [c.to_dict(lang) for c in featured],
        })

    @http.route('/api/v1/content/bookmarks', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_bookmarks(self, **kwargs):
        """Get user's bookmarks"""
        lang = get_lang()
        bookmark_type = kwargs.get('type')
        domain = [('app_user_id', '=', request.app_user.id)]
        if bookmark_type:
            domain.append(('bookmark_type', '=', bookmark_type))

        bookmarks = request.env['islamic.content.bookmark'].sudo().search(domain, order='create_date desc')
        result = []
        for b in bookmarks:
            item = {
                'id': b.id,
                'type': b.bookmark_type,
                'note': b.note,
                'created_at': b.create_date.isoformat(),
            }
            if b.ayah_id:
                item['ayah'] = b.ayah_id.to_dict(lang)
            if b.content_id:
                item['content'] = b.content_id.to_dict(lang)
            if b.audio_id:
                item['audio'] = b.audio_id.to_dict(lang)
            result.append(item)

        return json_response({'success': True, 'data': result})

    @http.route('/api/v1/content/bookmarks', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def add_bookmark(self, **kwargs):
        """Add a bookmark"""
        data = get_json_body()
        vals = {
            'app_user_id': request.app_user.id,
            'bookmark_type': data.get('type'),
            'note': data.get('note'),
        }
        if data.get('type') == 'ayah':
            vals['ayah_id'] = data.get('ayah_id')
        elif data.get('type') == 'content':
            vals['content_id'] = data.get('content_id')
        elif data.get('type') == 'audio':
            vals['audio_id'] = data.get('audio_id')

        try:
            bookmark = request.env['islamic.content.bookmark'].sudo().create(vals)
            return json_response({'success': True, 'data': {'id': bookmark.id}}, 201)
        except Exception as e:
            return error_response(str(e))

    @http.route('/api/v1/content/bookmarks/<int:bookmark_id>', type='http', auth='public',
                methods=['DELETE'], csrf=False, cors='*')
    @jwt_required
    def delete_bookmark(self, bookmark_id, **kwargs):
        """Delete a bookmark"""
        bookmark = request.env['islamic.content.bookmark'].sudo().search([
            ('id', '=', bookmark_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not bookmark:
            return error_response('Bookmark not found', 404)
        bookmark.unlink()
        return json_response({'success': True})

    @http.route('/api/v1/content/quran/progress', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def update_reading_progress(self, **kwargs):
        """Update Quran reading progress"""
        data = get_json_body()
        vals = {
            'app_user_id': request.app_user.id,
            'last_page': data.get('page'),
            'last_juz': data.get('juz'),
            'pages_read_today': data.get('pages_read', 0),
            'mode': data.get('mode', 'reading'),
        }
        if data.get('surah_id'):
            vals['surah_id'] = data['surah_id']
            vals['last_ayah'] = data.get('last_ayah')

        request.env['islamic.quran.progress'].sudo().create(vals)

        # Update user stats
        if data.get('pages_read', 0) > 0:
            request.app_user.sudo().write({
                'total_quran_pages_read': request.app_user.total_quran_pages_read + data['pages_read'],
            })

        return json_response({'success': True})
