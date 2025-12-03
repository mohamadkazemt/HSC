from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from permissions.models import PartPermission, SectionPermission, PositionPermission, UnitGroupPermission, UserPermission
from accounts.models import UserProfile
from permissions.utils import check_permission

User = get_user_model()

class Command(BaseCommand):
    help = "Debug permission resolution for a username and view_name"

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username to check')
        parser.add_argument('--view', required=True, help='View name to check')

    def handle(self, *args, **options):
        username = options['username']
        view_name = options['view']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")

        profile = getattr(user, 'userprofile', None)
        self.stdout.write(self.style.NOTICE(f"User: {user.username} | superuser={user.is_superuser} | authenticated={user.is_authenticated}"))
        if profile:
            self.stdout.write(self.style.NOTICE(f"Profile: section={profile.section} part={profile.part} unit_group={profile.unit_group} position={profile.position}"))
        else:
            self.stdout.write(self.style.WARNING("No UserProfile attached to this user"))

        # Gather each layer explicitly
        layers = []
        if profile and profile.part:
            p = PartPermission.objects.filter(part=profile.part, view_name=view_name).first()
            layers.append(('PartPermission', p))
        if profile and profile.section:
            s = SectionPermission.objects.filter(section=profile.section, view_name=view_name).first()
            layers.append(('SectionPermission', s))
        if profile and profile.unit_group:
            ug = UnitGroupPermission.objects.filter(unit_group=profile.unit_group, view_name=view_name).first()
            layers.append(('UnitGroupPermission', ug))
        if profile and profile.position:
            pos = PositionPermission.objects.filter(position=profile.position, view_name=view_name).first()
            layers.append(('PositionPermission', pos))
        up = UserPermission.objects.filter(user_id=user.id, view_name=view_name).first()
        layers.append(('UserPermission', up))

        self.stdout.write(self.style.NOTICE(f"\nLayers for view '{view_name}':"))
        for name, obj in layers:
            if obj:
                self.stdout.write(f"- {name}: can_view={obj.can_view} can_add={obj.can_add} can_edit={obj.can_edit} can_delete={obj.can_delete}")
            else:
                self.stdout.write(f"- {name}: NONE")

        final = check_permission(user, view_name)
        self.stdout.write(self.style.SUCCESS(f"\nFinal merged permissions: {final}"))
        self.stdout.write(self.style.SUCCESS(f"Has any permission: {any(final.values())}"))
