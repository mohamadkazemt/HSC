from django.db import models
from accounts.models import Part, Section, Position, UnitGroup
from django.contrib.auth.models import User

class PartPermission(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name="قسمت")
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
        return f"{self.part.name} - {self.view_name}"


class SectionPermission(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="بخش")
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
        return f"{self.section.name} - {self.view_name}"

class UnitGroupPermission(models.Model):
    unit_group = models.ForeignKey(UnitGroup, on_delete=models.CASCADE, verbose_name="گروه")
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
        return f"{self.unit_group.name} - {self.view_name}"


class PositionPermission(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name="سمت")
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
class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
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
        return f"{self.user.username} - {self.view_name}"