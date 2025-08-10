# iam/middleware.py
from .permissions import get_current_firm

class CurrentFirmMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.current_firm = get_current_firm(request)
        return self.get_response(request)
