# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView,
    UserDetailView,
    UserSubscriptionView,
    PlanListView,
    UserScanResultsView,
    ChangePlanView,
    ScanFolderViewSet,
    ActivateUserView,
    PasswordResetRequestView,
    ResetPasswordConfirmView,
    ChangePasswordView,
    # соц-логин классы из views.py:
    GoogleLogin,
    GithubLogin,
    MicrosoftLogin,
)

router = DefaultRouter()
router.register(r'folders', ScanFolderViewSet, basename='scan-folder')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('me/', UserDetailView.as_view(), name='user_info'),
    path('subscription/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('plans/', PlanListView.as_view(), name='plans-list'),

    path('scans/', UserScanResultsView.as_view(), name='user-scans'),
    path('change-plan/', ChangePlanView.as_view(), name='change-plan'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    path('activate/<uidb64>/<token>/', ActivateUserView.as_view(), name='activate'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('reset-password-confirm/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='password-reset-confirm'),

    # соц-логин
    path('google/login/', GoogleLogin.as_view(), name='google_login'),
    path('github/login/', GithubLogin.as_view(), name='github_login'),
    path('microsoft/login/', MicrosoftLogin.as_view(), name='microsoft_login'),

    path('', include(router.urls)),
]
