from django.db import models
from accounts.models import Unit, Department, Position

class UnitPermission(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name="واحد")
    view_name = models.CharField(max_length=100, verbose_name="نام ویو")
    can_view = models.BooleanField(default=False, verbose_name="مشاهده")
    can_add = models.BooleanField(default=False, verbose_name="افزودن")
    can_edit = models.BooleanField(default=False, verbose_name="ویرایش")
    can_delete = models.BooleanField(default=False, verbose_name="حذف")

    def get_permissions(self):
        return {
            "can_view": self.can_view,
            "can_add": self.can_add,
            "can_edit": self.can_edit,
            "can_delete": self.can_delete,
        }

    def __str__(self):
        return f"{self.unit.name} - {self.view_name}"

class DepartmentPermission(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="بخش")
    view_name = models.CharField(max_length=100, verbose_name="نام ویو")
    can_view = models.BooleanField(default=False, verbose_name="مشاهده")
    can_add = models.BooleanField(default=False, verbose_name="افزودن")
    can_edit = models.BooleanField(default=False, verbose_name="ویرایش")
    can_delete = models.BooleanField(default=False, verbose_name="حذف")

    def get_permissions(self):
        return {
            "can_view": self.can_view,
            "can_add": self.can_add,
            "can_edit": self.can_edit,
            "can_delete": self.can_delete,
        }

    def __str__(self):
        return f"{self.department.name} - {self.view_name}"

class PositionPermission(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name="پست")
    view_name = models.CharField(max_length=100, verbose_name="نام ویو")
    can_view = models.BooleanField(default=False, verbose_name="مشاهده")
    can_add = models.BooleanField(default=False, verbose_name="افزودن")
    can_edit = models.BooleanField(default=False, verbose_name="ویرایش")
    can_delete = models.BooleanField(default=False, verbose_name="حذف")

    def get_permissions(self):
        return {
            "can_view": self.can_view,
            "can_add": self.can_add,
            "can_edit": self.can_edit,
            "can_delete": self.can_delete,
        }

    def __str__(self):
        return f"{self.position.name} - {self.view_name}"
