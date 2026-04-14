import logging
from odoo import http
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_lang

_logger = logging.getLogger(__name__)


class IslamicAdhkarController(http.Controller):

    @http.route('/api/v1/adhkar/categories', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_categories(self, **kwargs):
        lang = get_lang()
        categories = request.env['islamic.adhkar.category'].sudo().search([], order='sequence')
        return json_response({
            'success': True,
            'data': [c.to_dict(lang) for c in categories],
        })

    @http.route('/api/v1/adhkar/category/<string:code>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_by_category(self, code, **kwargs):
        lang = get_lang()
        category = request.env['islamic.adhkar.category'].sudo().search([('code', '=', code)], limit=1)
        if not category:
            return error_response('Category not found', 404)

        adhkar = request.env['islamic.adhkar'].sudo().search([
            ('category_id', '=', category.id),
            ('state', '=', 'published'),
        ], order='sequence')

        return json_response({
            'success': True,
            'data': {
                'category': category.to_dict(lang),
                'adhkar': [a.to_dict(lang) for a in adhkar],
            },
        })

    @http.route('/api/v1/adhkar/<int:adhkar_id>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_adhkar(self, adhkar_id, **kwargs):
        lang = get_lang()
        adhkar = request.env['islamic.adhkar'].sudo().browse(adhkar_id)
        if not adhkar.exists():
            return error_response('Adhkar not found', 404)
        return json_response({'success': True, 'data': adhkar.to_dict(lang)})

    @http.route('/api/v1/adhkar/time/<string:time_of_day>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_by_time(self, time_of_day, **kwargs):
        lang = get_lang()
        adhkar = request.env['islamic.adhkar'].sudo().search([
            ('time_of_day', '=', time_of_day),
            ('state', '=', 'published'),
        ], order='sequence')
        return json_response({
            'success': True,
            'data': [a.to_dict(lang) for a in adhkar],
        })

    @http.route('/api/v1/adhkar/featured', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_featured(self, **kwargs):
        lang = get_lang()
        featured = request.env['islamic.adhkar'].sudo().search([
            ('is_featured', '=', True),
            ('state', '=', 'published'),
        ], limit=10, order='sequence')
        return json_response({
            'success': True,
            'data': [a.to_dict(lang) for a in featured],
        })
