from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _


class Command(BaseCommand):
    help = 'Setup emergency portal groups and initial configuration'

    def handle(self, *args, **options):
        """Create emergency groups"""
        self.stdout.write(self.style.SUCCESS('Setting up Emergency Portal...'))
        
        # Create emergency groups
        groups = [
            ('EmergencyManager', 'مدیر اورژانس'),
            ('EmergencyDoctor', 'پزشک اورژانس'),
            ('EmergencyNurse', 'پرستار اورژانس'),
        ]
        
        created_count = 0
        for group_name, display_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {display_name} ({group_name})')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'• Group already exists: {display_name} ({group_name})')
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Emergency Portal setup complete! Created {created_count} new groups.'
        ))
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Next Steps:'))
        self.stdout.write('1. Assign permissions to these groups using the Django admin')
        self.stdout.write('2. Create emergency personnel users using the data management page')
        self.stdout.write('3. Test login at /emergency/login/')
