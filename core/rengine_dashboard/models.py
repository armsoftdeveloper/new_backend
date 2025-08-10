# iam/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Firm(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Panel(models.Model):
    """
    Логические "панели/модули/дашборды", доступ к которым надо ограничивать.
    Пример: 'assets', 'scans', 'reports'
    """
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Membership(models.Model):
    """
    Пользователь состоит в фирме и имеет роль.
    """
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin (firm)"
        MANAGER = "manager", "Manager"
        MEMBER = "member", "Member"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        unique_together = ("user", "firm")

    def __str__(self):
        return f"{self.user} @ {self.firm} ({self.get_role_display()})"


class FirmPanel(models.Model):
    """
    Какие панели включены у конкретной фирмы (глобальный доступ внутри фирмы).
    """
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="enabled_panels")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("firm", "panel")

    def __str__(self):
        return f"{self.firm} -> {self.panel}"


class UserPanelPermission(models.Model):
    """
    Точная настройка: доступ конкретного пользователя (в контексте его Membership) к панели.
    Админ фирмы видит всё по умолчанию, для остальных — проверяем тут.
    """
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="panel_perms")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)

    class Meta:
        unique_together = ("membership", "panel")

    def __str__(self):
        return f"{self.membership} -> {self.panel} (view={self.can_view}, edit={self.can_edit})"
