from django.core.management.base import BaseCommand
from accounts.models import Position
from permissions.models import PositionPermission


class Command(BaseCommand):
    help = 'Grant necessary permissions to Safety Officer position'

    def handle(self, *args, **options):
        # Get safety officer position
        safety_officer_pos = Position.objects.get(id=1)  # بازرس شیفت ایمنی
        
        # Define required views and permissions
        views_permissions = [
            ('general_checklist_list', True, False, False, False),  # view checklist list
            ('general_checklist_form', True, True, False, False),    # create new checklist
            ('general_checklist_detail', True, False, False, False), # view checklist detail
            ('submit_general_checklist', True, True, False, False),  # submit checklist
            ('get_general_questions', True, False, False, False),    # get questions
            ('daily_report_form', True, True, False, False),         # access daily report form
            ('create_daily_report', True, True, False, False),       # create daily report
            ('daily_report_list', True, False, False, False),        # view daily report list
            ('daily_report_detail', True, False, False, False),      # view daily report detail
            ('daily_report_pdf', True, False, False, False),         # export to PDF
            ('view_pending_scheduled_checklists', True, False, False, False),  # view pending checklists
            ('get_pending_tasks', True, False, False, False),        # get pending tasks
            ('view_upcoming_scheduled_checklists', True, False, False, False),  # view upcoming checklists
        ]
        
        created_count = 0
        updated_count = 0
        
        for view_name, can_view, can_add, can_edit, can_delete in views_permissions:
            perm, created = PositionPermission.objects.get_or_create(
                position=safety_officer_pos,
                view_name=view_name,
                defaults={
                    'can_view': can_view,
                    'can_add': can_add,
                    'can_edit': can_edit,
                    'can_delete': can_delete,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created permission: {view_name}')
                )
            else:
                # Update if it already exists
                perm.can_view = can_view
                perm.can_add = can_add
                perm.can_edit = can_edit
                perm.can_delete = can_delete
                perm.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Updated permission: {view_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal created: {created_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total updated: {updated_count}')
        )
