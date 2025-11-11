# management/commands/list_users_without_rubika.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dashboard.models import Notification
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'List users who have notifications but are not connected to Rubika bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Check notifications from last N days (default: 30)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['table', 'csv'],
            default='table',
            help='Output format (default: table)',
        )

    def handle(self, *args, **options):
        days = options['days']
        output_format = options['format']
        
        since_date = timezone.now() - timedelta(days=days)
        
        # Get users with notifications but no rubika connection
        users_with_notifs = User.objects.filter(
            notifications__created_at__gte=since_date
        ).distinct()
        
        results = []
        for user in users_with_notifs:
            profile = getattr(user, 'rubika_profile', None)
            has_rubika = bool(profile and getattr(profile, 'chat_id', None))
            
            if not has_rubika:
                notif_count = user.notifications.filter(
                    created_at__gte=since_date
                ).count()
                unread_count = user.notifications.filter(
                    created_at__gte=since_date,
                    is_read=False
                ).count()
                
                results.append({
                    'username': user.username,
                    'full_name': user.get_full_name() or '-',
                    'email': user.email or '-',
                    'notif_count': notif_count,
                    'unread_count': unread_count,
                })
        
        # Sort by notification count
        results.sort(key=lambda x: x['notif_count'], reverse=True)
        
        if output_format == 'csv':
            self._output_csv(results, days)
        else:
            self._output_table(results, days)
    
    def _output_table(self, results, days):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS(f'Users with notifications (last {days} days) but NO Rubika connection'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        if not results:
            self.stdout.write(self.style.WARNING('No users found!'))
            return
        
        self.stdout.write(f'Total users: {len(results)}\n')
        
        # Header
        self.stdout.write(
            f"{'Username':<20} {'Full Name':<30} {'Notifs':<8} {'Unread':<8}"
        )
        self.stdout.write('-' * 80)
        
        # Rows
        for r in results:
            self.stdout.write(
                f"{r['username']:<20} {r['full_name']:<30} {r['notif_count']:<8} {r['unread_count']:<8}"
            )
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS(f'Total: {len(results)} users need to connect to Rubika bot'))
        self.stdout.write('='*80 + '\n')
    
    def _output_csv(self, results, days):
        import csv
        import sys
        
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=['username', 'full_name', 'email', 'notif_count', 'unread_count']
        )
        writer.writeheader()
        writer.writerows(results)
