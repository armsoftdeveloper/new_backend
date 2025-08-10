# iam/decorators.py
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .permissions import get_current_firm, user_can_access_panel
from .models import Panel

def panel_required(panel_code: str, need_edit: bool = False):
    def _decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            firm = get_current_firm(request)
            if not firm:
                # нет выбранной фирмы — отправим на страницу выбора
                return redirect("admin:iam_firm_changelist")
            try:
                panel = Panel.objects.get(code=panel_code)
            except Panel.DoesNotExist:
                return HttpResponseForbidden("Panel not configured")
            if not user_can_access_panel(request.user, firm, panel, need_edit=need_edit):
                return HttpResponseForbidden("No access to this panel")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return _decorator
