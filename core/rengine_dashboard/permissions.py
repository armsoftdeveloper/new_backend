# iam/permissions.py
from typing import Optional
from django.http import HttpRequest
from .models import Firm, Panel, Membership, FirmPanel, UserPanelPermission

CURRENT_FIRM_SESSION_KEY = "current_firm_id"

def get_current_firm(request: HttpRequest) -> Optional[Firm]:
    fid = request.session.get(CURRENT_FIRM_SESSION_KEY)
    if not fid:
        return None
    try:
        return Firm.objects.get(pk=fid)
    except Firm.DoesNotExist:
        return None

def set_current_firm(request: HttpRequest, firm: Firm) -> None:
    request.session[CURRENT_FIRM_SESSION_KEY] = firm.pk

def is_platform_admin(user) -> bool:
    return bool(user.is_authenticated and user.is_superuser)

def get_membership(user, firm) -> Optional[Membership]:
    if not user.is_authenticated or not firm:
        return None
    return Membership.objects.filter(user=user, firm=firm).first()

def panel_enabled_for_firm(firm: Firm, panel: Panel) -> bool:
    return FirmPanel.objects.filter(firm=firm, panel=panel).exists()

def user_can_access_panel(user, firm: Firm, panel: Panel, need_edit: bool = False) -> bool:
    if is_platform_admin(user):
        return True
    ms = get_membership(user, firm)
    if not ms:
        return False
    if ms.role == Membership.Role.ADMIN:
        # админ фирмы видит все включённые панели
        return panel_enabled_for_firm(firm, panel)
    # иначе — точечные права
    upp = UserPanelPermission.objects.filter(membership=ms, panel=panel).first()
    if not upp or not upp.can_view:
        return False
    if need_edit and not upp.can_edit:
        return False
    # и панель вообще должна быть включена фирме
    return panel_enabled_for_firm(firm, panel)
