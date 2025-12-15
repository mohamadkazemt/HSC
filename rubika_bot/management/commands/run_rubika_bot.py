# rubika_bot/management/commands/run_rubika_bot.py

import logging
import signal
import sys
import time
from django.core.management.base import BaseCommand
from rubika_bot.services import RubPyIntegrationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs the Rubika bot using polling or long-running webhook handler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stop-timeout',
            type=int,
            default=10,
            help='Timeout in seconds to wait for graceful shutdown (default: 10)'
        )

    def handle(self, *args, **options):
        stop_timeout = options['stop_timeout']
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting Rubika Bot...'))
        logger.info("Starting Rubika Bot service")
        
        # Get the service instance
        service = RubPyIntegrationService.get_instance()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING(f'\n⚠️  Received signal {signum}, shutting down...'))
            logger.info(f"Received signal {signum}, initiating shutdown")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.stdout.write(self.style.SUCCESS('✅ Rubika Bot is running!'))
            self.stdout.write(self.style.SUCCESS('   Press Ctrl+C to stop'))
            logger.info("Rubika Bot service started successfully")
            
            # Keep the service running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⚠️  Keyboard interrupt received'))
            logger.info("Keyboard interrupt received")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            logger.error(f"Error in Rubika Bot service: {e}", exc_info=True)
            raise
        finally:
            self.stdout.write(self.style.SUCCESS('🛑 Stopping Rubika Bot...'))
            logger.info("Stopping Rubika Bot service")
            
            try:
                # Clean shutdown
                RubPyIntegrationService.reset()
                self.stdout.write(self.style.SUCCESS('✅ Rubika Bot stopped successfully'))
                logger.info("Rubika Bot service stopped successfully")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'⚠️  Error during shutdown: {e}'))
                logger.error(f"Error during shutdown: {e}", exc_info=True)
