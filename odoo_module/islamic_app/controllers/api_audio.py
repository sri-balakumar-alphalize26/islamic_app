import json
import logging
import base64
from odoo import http
from odoo.http import request
from .api_auth import jwt_required, admin_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicAudioController(http.Controller):

    @http.route('/api/v1/audio/list', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def list_audio(self, **kwargs):
        lang = get_lang()
        audio_type = kwargs.get('type')
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit

        domain = [('state', '=', 'published')]
        if audio_type:
            domain.append(('audio_type', '=', audio_type))
        if not request.app_user.is_premium:
            domain.append(('is_premium', '=', False))

        audios = request.env['islamic.audio'].sudo().search(domain, limit=limit, offset=offset, order='sequence')
        total = request.env['islamic.audio'].sudo().search_count(domain)

        return json_response({
            'success': True,
            'data': [a.to_dict(lang) for a in audios],
            'pagination': {'page': page, 'limit': limit, 'total': total},
        })

    @http.route('/api/v1/audio/<int:audio_id>', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_audio(self, audio_id, **kwargs):
        lang = get_lang()
        audio = request.env['islamic.audio'].sudo().browse(audio_id)
        if not audio.exists() or audio.state != 'published':
            return error_response('Audio not found', 404)
        if audio.is_premium and not request.app_user.is_premium:
            return error_response('Premium content', 403, 'PREMIUM_REQUIRED')

        # Increment play count
        audio.sudo().write({'play_count': audio.play_count + 1})
        return json_response({'success': True, 'data': audio.to_dict(lang)})

    @http.route('/api/v1/audio/stream/<int:audio_id>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def stream_audio(self, audio_id, **kwargs):
        """Get streaming URL for audio"""
        audio = request.env['islamic.audio'].sudo().browse(audio_id)
        if not audio.exists():
            return error_response('Audio not found', 404)
        if audio.is_premium and not request.app_user.is_premium:
            return error_response('Premium content', 403)

        quality = kwargs.get('quality', 'normal')
        url = audio.audio_url_hq if quality == 'high' and audio.audio_url_hq else audio.audio_url
        return json_response({
            'success': True,
            'data': {'url': url, 'duration': audio.duration_seconds},
        })

    @http.route('/api/v1/audio/surah/<int:surah_number>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_surah_audio(self, surah_number, **kwargs):
        lang = get_lang()
        audios = request.env['islamic.audio'].sudo().search([
            ('surah_id.number', '=', surah_number),
            ('state', '=', 'published'),
        ], order='reciter_name')
        return json_response({
            'success': True,
            'data': [a.to_dict(lang) for a in audios],
        })

    @http.route('/api/v1/audio/playlists', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_playlists(self, **kwargs):
        lang = get_lang()
        playlists = request.env['islamic.audio.playlist'].sudo().search([
            '|',
            ('is_system', '=', True),
            ('app_user_id', '=', request.app_user.id),
        ], order='sequence')
        return json_response({
            'success': True,
            'data': [p.to_dict(lang) for p in playlists],
        })

    @http.route('/api/v1/audio/upload', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    @admin_required
    def upload_audio(self, **kwargs):
        """Admin: Upload new audio content"""
        try:
            data = get_json_body()
            vals = {
                'name': data.get('title'),
                'name_ar': data.get('title_ar'),
                'audio_type': data.get('audio_type', 'lecture'),
                'reciter_name': data.get('reciter'),
                'is_sister_nasira': data.get('is_sister_nasira', False),
                'is_brother_ibrahim': data.get('is_brother_ibrahim', False),
                'language': data.get('language', 'ar'),
                'state': 'draft',
                'uploaded_by': request.app_user.id,
            }
            if data.get('audio_base64'):
                vals['audio_file'] = base64.b64decode(data['audio_base64'])
                vals['audio_file_name'] = data.get('filename', 'audio.mp3')

            if data.get('audio_url'):
                vals['audio_url'] = data['audio_url']

            if data.get('surah_number'):
                surah = request.env['islamic.surah'].sudo().search(
                    [('number', '=', data['surah_number'])], limit=1)
                if surah:
                    vals['surah_id'] = surah.id

            audio = request.env['islamic.audio'].sudo().create(vals)
            return json_response({
                'success': True,
                'data': {'id': audio.id, 'state': audio.state},
            }, 201)
        except Exception as e:
            _logger.exception("Audio upload error")
            return error_response(str(e), 500)

    @http.route('/api/v1/audio/listening-history', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def log_listening(self, **kwargs):
        """Log audio listening activity"""
        data = get_json_body()
        request.env['islamic.listening.history'].sudo().create({
            'app_user_id': request.app_user.id,
            'audio_id': data.get('audio_id'),
            'listened_seconds': data.get('duration', 0),
            'completed': data.get('completed', False),
        })
        # Update total listening minutes
        minutes = data.get('duration', 0) / 60
        request.app_user.sudo().write({
            'total_listening_minutes': request.app_user.total_listening_minutes + minutes,
        })
        return json_response({'success': True})
