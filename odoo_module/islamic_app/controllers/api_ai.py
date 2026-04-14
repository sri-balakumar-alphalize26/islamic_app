import json
import logging
import time
from odoo import http, fields
from odoo.http import request
from .api_auth import jwt_required, json_response, error_response, get_json_body, get_lang

_logger = logging.getLogger(__name__)


class IslamicAIController(http.Controller):

    @http.route('/api/v1/ai/ask', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def ask_ai(self, **kwargs):
        """Send a question to the AI assistant"""
        data = get_json_body()
        question = data.get('question', '').strip()
        conversation_id = data.get('conversation_id')
        lang = get_lang()

        if not question:
            return error_response('Question is required')

        # Rate limiting
        config = request.env['islamic.ai.config'].sudo().get_active_config()
        if not config:
            return error_response('AI service is not configured', 503)

        daily_count = request.env['islamic.ai.query.log'].sudo().get_user_daily_count(
            request.app_user.id)
        daily_limit = config.max_daily_queries_premium if request.app_user.is_premium \
            else config.max_daily_queries_free
        if daily_count >= daily_limit:
            return error_response(
                f'Daily query limit reached ({daily_limit}). Upgrade to premium for more.',
                429, 'RATE_LIMIT'
            )

        # Get or create conversation
        conversation = None
        if conversation_id:
            conversation = request.env['islamic.ai.conversation'].sudo().search([
                ('id', '=', conversation_id),
                ('app_user_id', '=', request.app_user.id),
                ('state', '=', 'active'),
            ], limit=1)

        if not conversation:
            conversation = request.env['islamic.ai.conversation'].sudo().create({
                'app_user_id': request.app_user.id,
                'title': question[:80],
                'language': lang,
            })

        # Save user message
        request.env['islamic.ai.message'].sudo().create({
            'conversation_id': conversation.id,
            'role': 'user',
            'content': question,
            'language': lang,
        })

        # Build message history for AI
        messages = []
        for msg in conversation.message_ids.sorted('create_date'):
            messages.append({
                'role': msg.role,
                'content': msg.content,
            })

        # Call AI service
        start_time = time.time()
        try:
            ai_response = self._call_ai_service(config, messages, lang)
            response_time = int((time.time() - start_time) * 1000)

            # Save AI response
            ai_message = request.env['islamic.ai.message'].sudo().create({
                'conversation_id': conversation.id,
                'role': 'assistant',
                'content': ai_response.get('content', ''),
                'language': lang,
                'model_used': config.model_name,
                'tokens_used': ai_response.get('tokens_used', 0),
                'response_time_ms': response_time,
                'referenced_ayahs': json.dumps(ai_response.get('references', [])),
            })

            # Log query
            request.env['islamic.ai.query.log'].sudo().create({
                'app_user_id': request.app_user.id,
                'query': question,
                'response_preview': ai_response.get('content', '')[:200],
                'language': lang,
                'tokens_used': ai_response.get('tokens_used', 0),
                'response_time_ms': response_time,
                'is_premium_user': request.app_user.is_premium,
            })

            return json_response({
                'success': True,
                'data': {
                    'conversation_id': conversation.id,
                    'message': ai_message.to_dict(),
                    'daily_queries_remaining': daily_limit - daily_count - 1,
                },
            })

        except Exception as e:
            _logger.exception("AI service error")
            return error_response('AI service temporarily unavailable', 503)

    def _call_ai_service(self, config, messages, lang):
        """Call external AI API (Anthropic Claude / OpenAI)"""
        import urllib.request
        import urllib.error

        lang_instruction = {
            'en': 'Respond in English.',
            'ar': 'Respond in Arabic (العربية).',
            'fr': 'Respond in French (Français).',
            'tr': 'Respond in Turkish (Türkçe).',
            'hi': 'Respond in Hindi (हिन्दी).',
        }.get(lang, 'Respond in English.')

        system_prompt = (config.system_prompt or '') + f"\n\n{lang_instruction}"

        if config.ai_provider == 'anthropic':
            return self._call_anthropic(config, system_prompt, messages)
        elif config.ai_provider == 'openai':
            return self._call_openai(config, system_prompt, messages)
        else:
            return self._call_custom(config, system_prompt, messages)

    def _call_anthropic(self, config, system_prompt, messages):
        """Call Anthropic Claude API"""
        import urllib.request
        url = config.api_url or 'https://api.anthropic.com/v1/messages'
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': config.api_key,
            'anthropic-version': '2023-06-01',
        }
        # Convert message format for Anthropic
        api_messages = []
        for msg in messages:
            if msg['role'] in ('user', 'assistant'):
                api_messages.append({
                    'role': msg['role'],
                    'content': msg['content'],
                })

        payload = json.dumps({
            'model': config.model_name or 'claude-sonnet-4-20250514',
            'max_tokens': config.max_tokens or 1024,
            'system': system_prompt,
            'messages': api_messages,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                content = ''
                for block in result.get('content', []):
                    if block.get('type') == 'text':
                        content += block.get('text', '')
                return {
                    'content': content,
                    'tokens_used': result.get('usage', {}).get('output_tokens', 0),
                }
        except urllib.error.HTTPError as e:
            _logger.error(f"Anthropic API error: {e.code} - {e.read().decode()}")
            raise

    def _call_openai(self, config, system_prompt, messages):
        """Call OpenAI API"""
        import urllib.request
        url = config.api_url or 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.api_key}',
        }
        api_messages = [{'role': 'system', 'content': system_prompt}]
        for msg in messages:
            if msg['role'] in ('user', 'assistant'):
                api_messages.append({'role': msg['role'], 'content': msg['content']})

        payload = json.dumps({
            'model': config.model_name or 'gpt-4',
            'max_tokens': config.max_tokens or 1024,
            'temperature': config.temperature or 0.7,
            'messages': api_messages,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return {
                'content': result['choices'][0]['message']['content'],
                'tokens_used': result.get('usage', {}).get('total_tokens', 0),
            }

    def _call_custom(self, config, system_prompt, messages):
        """Call custom AI API"""
        return {'content': 'Custom AI provider not yet implemented', 'tokens_used': 0}

    @http.route('/api/v1/ai/conversations', type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @jwt_required
    def get_conversations(self, **kwargs):
        """Get user's AI conversation list"""
        page = int(kwargs.get('page', 1))
        limit = min(int(kwargs.get('limit', 20)), 50)
        offset = (page - 1) * limit

        convos = request.env['islamic.ai.conversation'].sudo().search([
            ('app_user_id', '=', request.app_user.id),
            ('state', '=', 'active'),
        ], limit=limit, offset=offset, order='create_date desc')
        return json_response({
            'success': True,
            'data': [{
                'id': c.id,
                'title': c.title,
                'topic': c.topic,
                'message_count': c.message_count,
                'created_at': c.create_date.isoformat(),
            } for c in convos],
        })

    @http.route('/api/v1/ai/conversations/<int:conv_id>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    @jwt_required
    def get_conversation(self, conv_id, **kwargs):
        """Get full conversation with messages"""
        convo = request.env['islamic.ai.conversation'].sudo().search([
            ('id', '=', conv_id),
            ('app_user_id', '=', request.app_user.id),
        ], limit=1)
        if not convo:
            return error_response('Conversation not found', 404)
        return json_response({'success': True, 'data': convo.to_dict()})

    @http.route('/api/v1/ai/feedback', type='http', auth='public', methods=['POST'],
                csrf=False, cors='*')
    @jwt_required
    def submit_feedback(self, **kwargs):
        """Submit feedback on AI response"""
        data = get_json_body()
        message = request.env['islamic.ai.message'].sudo().browse(data.get('message_id'))
        if message.exists() and message.conversation_id.app_user_id.id == request.app_user.id:
            vals = {}
            if 'helpful' in data:
                vals['is_helpful'] = data['helpful']
            if data.get('flagged'):
                vals['is_flagged'] = True
                vals['flag_reason'] = data.get('flag_reason', '')
            message.write(vals)
        return json_response({'success': True})
