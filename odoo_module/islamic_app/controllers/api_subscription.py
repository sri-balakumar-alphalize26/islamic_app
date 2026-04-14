import json
import logging
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicSubscriptionController(http.Controller):

    @http.route('/api/v1/subscription/plans', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_plans(self, **kwargs):
        lang = get_lang()
        plans = request.env['islamic.subscription.plan'].sudo().search(
            [('active', '=', True)], order='sequence')
        return json_response({
            'success': True,
            'data': [p.to_dict(lang) for p in plans],
        })

    @http.route('/api/v1/subscription/current', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_current(self, **kwargs):
        lang = get_lang()
        sub = request.app_user.subscription_id
        return json_response({
            'success': True,
            'data': sub.to_dict(lang) if sub else None,
            'is_premium': request.app_user.is_premium,
        })

    @http.route('/api/v1/subscription/purchase', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def purchase(self, **kwargs):
        """Process subscription purchase"""
        data = get_json_body()
        plan_id = data.get('plan_id')
        payment_method = data.get('payment_method')
        transaction_id = data.get('transaction_id')
        receipt_data = data.get('receipt')

        plan = request.env['islamic.subscription.plan'].sudo().browse(plan_id)
        if not plan.exists():
            return error_response('Plan not found', 404)

        # Cancel existing active subscription
        existing = request.env['islamic.subscription'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
            ('state', 'in', ['active', 'trial']),
        ])
        existing.write({'state': 'cancelled'})

        # Create new subscription
        from datetime import timedelta
        end_date = None
        if plan.duration_days and plan.plan_type != 'lifetime':
            end_date = fields.Date.today() + timedelta(days=plan.duration_days)

        trial_end = None
        state = 'active'
        if plan.trial_days > 0:
            trial_end = fields.Date.today() + timedelta(days=plan.trial_days)
            state = 'trial'
            if not end_date:
                end_date = trial_end

        sub = request.env['islamic.subscription'].sudo().create({
            'app_user_id': request.app_user.id,
            'plan_id': plan.id,
            'state': state,
            'start_date': fields.Date.today(),
            'end_date': end_date,
            'trial_end_date': trial_end,
            'payment_method': payment_method,
            'store_transaction_id': transaction_id,
            'store_receipt': receipt_data,
            'amount_paid': plan.price,
            'auto_renew': plan.plan_type != 'lifetime',
        })

        # Record payment
        request.env['islamic.payment'].sudo().create({
            'subscription_id': sub.id,
            'app_user_id': request.app_user.id,
            'amount': plan.price,
            'payment_method': payment_method,
            'state': 'completed',
            'transaction_id': transaction_id,
            'receipt_data': receipt_data,
        })

        # Update user subscription reference
        request.app_user.sudo().write({'subscription_id': sub.id})

        lang = get_lang()
        return json_response({
            'success': True,
            'data': sub.to_dict(lang),
        }, 201)

    @http.route('/api/v1/subscription/verify-receipt', type='http', auth='public',
                methods=['POST'], csrf=False, cors='*')
    @jwt_required
    def verify_receipt(self, **kwargs):
        """Verify App Store / Play Store receipt"""
        data = get_json_body()
        platform = data.get('platform')  # 'apple' or 'google'
        receipt = data.get('receipt')

        # TODO: Implement actual receipt verification with Apple/Google servers
        # For now, return success placeholder
        return json_response({
            'success': True,
            'data': {'valid': True, 'platform': platform},
        })

    @http.route('/api/v1/subscription/cancel', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def cancel(self, **kwargs):
        sub = request.app_user.subscription_id
        if not sub or sub.state not in ('active', 'trial'):
            return error_response('No active subscription to cancel')
        sub.action_cancel()
        return json_response({'success': True, 'message': 'Subscription cancelled'})

    @http.route('/api/v1/subscription/restore', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def restore(self, **kwargs):
        """Restore purchases (for reinstalls)"""
        data = get_json_body()
        transaction_id = data.get('transaction_id')
        if not transaction_id:
            return error_response('Transaction ID required')

        payment = request.env['islamic.payment'].sudo().search([
            ('transaction_id', '=', transaction_id),
            ('state', '=', 'completed'),
        ], limit=1)
        if payment and payment.subscription_id:
            sub = payment.subscription_id
            if sub.plan_id.plan_type == 'lifetime' or (sub.end_date and sub.end_date >= fields.Date.today()):
                sub.write({'state': 'active'})
                request.app_user.sudo().write({'subscription_id': sub.id})
                lang = get_lang()
                return json_response({
                    'success': True,
                    'data': sub.to_dict(lang),
                    'message': 'Purchase restored successfully',
                })
        return error_response('No valid purchase found to restore', 404)
