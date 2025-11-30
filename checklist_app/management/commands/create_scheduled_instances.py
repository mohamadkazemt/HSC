"""
Management command to create scheduled checklist instances for today and future dates.

This command should be run daily (e.g., via cron job) to create scheduled instances
for upcoming dates based on active ChecklistSchedule configurations.

Usage:
    python manage.py create_scheduled_instances
    python manage.py create_scheduled_instances --days-ahead 7
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from checklist_app.services import create_scheduled_instances_for_date


class Command(BaseCommand):
    help = 'Create scheduled checklist instances for today and future dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=7,
            help='Number of days ahead to create instances (default: 7)',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to create instances for (format: YYYY-MM-DD). If not provided, uses today.',
        )

    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        specific_date = options.get('date')
        
        if specific_date:
            try:
                target_date = date.fromisoformat(specific_date)
                dates_to_process = [target_date]
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'Invalid date format: {specific_date}. Use YYYY-MM-DD format.')
                )
                return
        else:
            # Process today and next N days
            today = timezone.now().date()
            dates_to_process = [today + timedelta(days=i) for i in range(days_ahead + 1)]
        
        created_count = 0
        for target_date in dates_to_process:
            self.stdout.write(f'Processing date: {target_date}')
            try:
                create_scheduled_instances_for_date(target_date)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed {target_date}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {target_date}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted processing {created_count} date(s).'
            )
        )

