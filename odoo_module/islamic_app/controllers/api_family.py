import json
import logging
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body

_logger = logging.getLogger(__name__)


class IslamicFamilyController(http.Controller):

    @http.route('/api/v1/family/members', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_members(self, **kwargs):
        members = request.env['islamic.family.member'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
        ], order='relationship, name')
        return json_response({
            'success': True,
            'data': [m.to_dict() for m in members],
        })

    @http.route('/api/v1/family/members', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def add_member(self, **kwargs):
        data = get_json_body()
        member = request.env['islamic.family.member'].sudo().create({
            'app_user_id': request.app_user.id,
            'name': data.get('name'),
            'relationship': data.get('relationship'),
            'phone_number': data.get('phone'),
            'contact_frequency_days': data.get('reminder_days', 7),
            'notes': data.get('notes'),
        })
        return json_response({'success': True, 'data': member.to_dict()}, 201)

    @http.route('/api/v1/family/members/<int:member_id>', type='http', auth='public',
                methods=['PUT'], csrf=False, cors='*')
    @jwt_required
    def update_member(self, member_id, **kwargs):
        data = get_json_body()
        member = request.env['islamic.family.member'].sudo().search([
            ('id', '=', member_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not member:
            return error_response('Not found', 404)

        allowed = {'name', 'relationship', 'phone_number', 'contact_frequency_days', 'notes'}
        vals = {k: v for k, v in data.items() if k in allowed}
        if vals:
            member.write(vals)
        return json_response({'success': True, 'data': member.to_dict()})

    @http.route('/api/v1/family/members/<int:member_id>', type='http', auth='public',
                methods=['DELETE'], csrf=False, cors='*')
    @jwt_required
    def delete_member(self, member_id, **kwargs):
        member = request.env['islamic.family.member'].sudo().search([
            ('id', '=', member_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not member:
            return error_response('Not found', 404)
        member.unlink()
        return json_response({'success': True})

    @http.route('/api/v1/family/members/<int:member_id>/contact', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    def log_contact(self, member_id, **kwargs):
        data = get_json_body()
        member = request.env['islamic.family.member'].sudo().search([
            ('id', '=', member_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not member:
            return error_response('Not found', 404)
        member.log_contact(
            contact_type=data.get('type', 'call'),
            notes=data.get('notes', ''),
        )
        return json_response({'success': True, 'data': member.to_dict()})

    @http.route('/api/v1/family/overdue', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_overdue(self, **kwargs):
        members = request.env['islamic.family.member'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
            ('is_overdue', '=', True),
        ], order='next_reminder_date')
        return json_response({
            'success': True,
            'data': [m.to_dict() for m in members],
        })

    @http.route('/api/v1/family/members/<int:member_id>/history', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_contact_history(self, member_id, **kwargs):
        logs = request.env['islamic.family.contact.log'].sudo().search([
            ('family_member_id', '=', member_id),
            ('app_user_id', '=', request.app_user.id),
        ], order='date desc', limit=50)
        return json_response({
            'success': True,
            'data': [l.to_dict() for l in logs],
        })
