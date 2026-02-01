# rubika_bot/management/commands/register_webhook.py

import asyncio
import logging
from django.core.management.base import BaseCommand
from rubika_bot.models import RubikaBotSettings, WebhookLog
from rubpy.bot.bot import BotClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Register webhook URL for Rubika bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Webhook URL (default: https://miepcoj.ir/rubika_bot/webhook/)',
            default='https://miepcoj.ir/rubika_bot/webhook/'
        )

    def handle(self, *args, **options):
        webhook_url = options['url']
        
        self.stdout.write(self.style.SUCCESS(f'🔄 Registering webhook: {webhook_url}'))
        
        # Get bot token
        settings = RubikaBotSettings.objects.first()
        if not settings:
            self.stdout.write(self.style.ERROR('❌ Bot settings not found!'))
            return
        
        token = settings.get_token_safe()
        if not token:
            self.stdout.write(self.style.ERROR('❌ Bot token not found!'))
            return
        
        # Register webhook
        try:
            result = asyncio.run(self.register_webhook(token, webhook_url))
            
            if result:
                self.stdout.write(self.style.SUCCESS('✅ Webhook registered successfully!'))
                WebhookLog.log_info(
                    'Webhook Registered',
                    f'Successfully registered webhook: {webhook_url}',
                    {'url': webhook_url, 'result': result}
                )
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to register webhook'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            logger.error(f"Failed to register webhook: {e}", exc_info=True)
            WebhookLog.log_error(
                'Webhook Registration Failed',
                str(e),
                {'url': webhook_url}
            )
    
    async def register_webhook(self, token: str, webhook_url: str):
        """Register webhook using RubPy client"""
        client = BotClient(token=token, use_webhook=True)
        
        try:
            await client.start()
            self.stdout.write('📡 Bot client connected...')
            
            # Register for all update types
            results = {}
            for update_type in ["ReceiveUpdate", "ReceiveInlineMessage", "ReceiveQuery"]:
                try:
                    self.stdout.write(f'  Registering {update_type}...')
                    response = await client.update_bot_endpoints(webhook_url, update_type)
                    results[update_type] = response
                    self.stdout.write(self.style.SUCCESS(f'    ✅ {update_type}: OK'))
                except Exception as e:
                    results[update_type] = {'error': str(e)}
                    self.stdout.write(self.style.WARNING(f'    ⚠️  {update_type}: {e}'))
            
            return results
            
        finally:
            try:
                await client.stop()
            except:
                pass

