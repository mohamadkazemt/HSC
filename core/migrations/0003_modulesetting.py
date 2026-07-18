from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


MODULE_KEYS = [
    "anomalis", "meetings", "analytics", "shift_manager", "BaseInfo",
    "OperationsShiftReports", "dailyreport_hse", "leave_reports",
    "contractor_management", "hse_incidents", "machine_checklist",
    "fire_reports", "checklist_app", "emergency_services",
    "fire_extinguisher_management", "rubika_bot", "risk_assessment",
    "hse_docs", "corrective_actions", "mining_operations",
]


def create_module_settings(apps, schema_editor):
    ModuleSetting = apps.get_model("core", "ModuleSetting")
    ModuleSetting.objects.bulk_create(
        [ModuleSetting(module_key=key, is_active=True) for key in MODULE_KEYS],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0002_aisettings"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModuleSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_key", models.CharField(max_length=100, unique=True, verbose_name="ماژول")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال است")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
                ("modified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="modified_modules", to=settings.AUTH_USER_MODEL, verbose_name="آخرین تغییر توسط")),
            ],
            options={
                "verbose_name": "ماژول سایت",
                "verbose_name_plural": "فعال/غیرفعال‌سازی ماژول‌ها",
            },
        ),
        migrations.RunPython(create_module_settings, migrations.RunPython.noop),
    ]
