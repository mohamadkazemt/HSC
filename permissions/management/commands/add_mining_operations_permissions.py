from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from accounts.models import UnitGroup
from permissions.models import UnitGroupPermission, UserPermission


class Command(BaseCommand):
    help = 'Grant mining operations permissions to a unit group or a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--unit-group',
            dest='unit_group',
            help='UnitGroup id or exact name to grant permissions',
        )
        parser.add_argument(
            '--username',
            dest='username',
            help='Username to grant permissions',
        )

    def handle(self, *args, **options):
        unit_group_value = options.get('unit_group')
        username = options.get('username')

        if not unit_group_value and not username:
            raise CommandError('Provide either --unit-group or --username')

        views_permissions = [
            ('machine_activity_create', True, True, False, False),
            ('loading_hauling_create', True, True, False, False),
            ('loading_hauling_list', True, False, False, False),
            ('loading_hauling_update', True, False, True, False),
            ('count_sheet_create', True, True, False, False),
            ('machine_activity_export_excel', True, False, False, False),
            ('loading_hauling_export_excel', True, False, False, False),
        ]

        created_count = 0
        updated_count = 0

        if unit_group_value:
            unit_group = self._get_unit_group(unit_group_value)
            for view_name, can_view, can_add, can_edit, can_delete in views_permissions:
                perm, created = UnitGroupPermission.objects.get_or_create(
                    unit_group=unit_group,
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
                    self.stdout.write(self.style.SUCCESS(f'✓ ایجاد شد: {view_name}'))
                else:
                    perm.can_view = can_view
                    perm.can_add = can_add
                    perm.can_edit = can_edit
                    perm.can_delete = can_delete
                    perm.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'↻ به‌روزرسانی شد: {view_name}'))

            self.stdout.write(self.style.SUCCESS(
                f'\nگروه "{unit_group.name}" اکنون دسترسی عملیات معدنی دارد.'
            ))

        if username:
            user = self._get_user(username)
            for view_name, can_view, can_add, can_edit, can_delete in views_permissions:
                perm, created = UserPermission.objects.get_or_create(
                    user=user,
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
                    self.stdout.write(self.style.SUCCESS(f'✓ ایجاد شد: {view_name}'))
                else:
                    perm.can_view = can_view
                    perm.can_add = can_add
                    perm.can_edit = can_edit
                    perm.can_delete = can_delete
                    perm.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'↻ به‌روزرسانی شد: {view_name}'))

            self.stdout.write(self.style.SUCCESS(
                f'\nکاربر "{user.username}" اکنون دسترسی عملیات معدنی دارد.'
            ))

        self.stdout.write(self.style.SUCCESS(f'\nجمع ایجاد شده: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'جمع به‌روزرسانی شده: {updated_count}'))

    def _get_unit_group(self, value):
        try:
            if value.isdigit():
                return UnitGroup.objects.get(id=int(value))
            return UnitGroup.objects.get(name=value)
        except UnitGroup.DoesNotExist as exc:
            raise CommandError(f'UnitGroup not found: {value}') from exc

    def _get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f'User not found: {username}') from exc
