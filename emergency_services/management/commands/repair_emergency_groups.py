from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, User


EMERGENCY_GROUPS = [
    ("EmergencyManager", "مدیر اورژانس"),
    ("EmergencyDoctor", "پزشک اورژانس"),
    ("EmergencyNurse", "پرستار اورژانس"),
]


class Command(BaseCommand):
    help = "Repairs emergency portal groups (recreate if missing) and optionally assigns users to roles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--assign",
            metavar=("username", "role"),
            nargs=2,
            action="append",
            help=(
                "Optionally assign a user to a role. Can be repeated. "
                "Roles: EmergencyManager | EmergencyDoctor | EmergencyNurse"
            ),
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Repairing Emergency Portal groups..."))

        # Ensure groups exist
        created_count = 0
        for name, display in EMERGENCY_GROUPS:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created group: {display} ({name})"))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"• Group exists: {display} ({name})"))

        self.stdout.write(self.style.SUCCESS(f"Groups ready. Newly created: {created_count}"))

        # Optional assignments
        assigns = options.get("assign") or []
        for username, role in assigns:
            valid_roles = {g[0] for g in EMERGENCY_GROUPS}
            if role not in valid_roles:
                raise CommandError(
                    f"Invalid role '{role}'. Use one of: {', '.join(sorted(valid_roles))}"
                )

            user = User.objects.filter(username=username).first()
            if not user:
                raise CommandError(f"User '{username}' not found")

            # Remove user from emergency groups, then add to the target role
            emergency_groups = Group.objects.filter(name__in=list(valid_roles))
            user.groups.remove(*emergency_groups)
            target_group = Group.objects.get(name=role)
            user.groups.add(target_group)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Assigned user '{username}' to role '{role}'"
                )
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Repair completed."))
        self.stdout.write(
            "Tip: Use --assign <username> <role> to (re)assign users to roles."
        )