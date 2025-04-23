from django.apps import AppConfig

class MeetingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meetings'
    verbose_name = 'مدیریت جلسات'

    def ready(self):
        import meetings.signals
        
        # Import models here to avoid circular imports
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        from .models import Meeting

        @receiver(post_migrate)
        def create_meeting_permissions(sender, **kwargs):
            if sender.name == 'meetings':
                content_type = ContentType.objects.get_for_model(Meeting)
                permissions = [
                    ('add_meeting', 'افزودن جلسه'),
                    ('change_meeting', 'تغییر جلسه'),
                    ('delete_meeting', 'حذف جلسه'),
                    ('view_meeting', 'مشاهده جلسه'),
                ]
                
                for codename, name in permissions:
                    Permission.objects.get_or_create(
                        codename=codename,
                        content_type=content_type,
                        defaults={'name': name}
                    )
