from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rubika_bot.models import RubikaUser


class Command(BaseCommand):
    help = 'بررسی اتصالات کاربران به ربات روبیکا'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 بررسی اتصالات کاربران به ربات روبیکا...'))
        self.stdout.write('')
        
        # لیست تمام کاربران
        users = User.objects.all().select_related('userprofile')
        
        connected_count = 0
        not_connected_count = 0
        
        for user in users:
            rubika_profile = getattr(user, 'rubika_profile', None)
            
            if rubika_profile and rubika_profile.chat_id:
                connected_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {user.username} ({user.get_full_name()}) '
                        f'- Chat ID: {rubika_profile.chat_id}'
                    )
                )
            else:
                not_connected_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ {user.username} ({user.get_full_name()}) '
                        f'- متصل نیست'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'📊 خلاصه:'))
        self.stdout.write(f'   - متصل: {connected_count}')
        self.stdout.write(f'   - متصل نشده: {not_connected_count}')
        self.stdout.write(f'   - جمع کل: {users.count()}')
