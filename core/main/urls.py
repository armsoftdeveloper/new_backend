from django.urls import path
from .views import *

urlpatterns = [
    path('navigation/', CategoryListView.as_view(), name='navigation'),
    path('tool/<slug:slug>/', ToolPageDetailView.as_view(), name='tool-detail'),
    path('landing/', LandingContentView.as_view(), name='landing-content'),
    path('banner/', BannerAPIView.as_view(), name='banner-content'),
    path('features/', FeatureListAPIView.as_view(), name='feature-list'),
    path('team-services/', TeamServiceListAPIView.as_view(), name='team-services-list'),
    path('benefits/', BenefitListAPIView.as_view(), name='benefit-list'),
    path('statistics/', StatisticListAPIView.as_view(), name='statistics'),
    path('site-settings/', SiteSettingsAPIView.as_view()),
    path('research/', ResearchList.as_view(), name='research-list'),
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('terms/', TermsAndConditionsView.as_view(), name='terms-conditions'),
    path('security/', SecurityPolicyView.as_view(), name='security-policy'),
    path('about/', AboutView.as_view(), name='about-page'),
    path('contact/', ContactFormAPIView.as_view(), name='contact-api'),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
    path('landing-slider/', LandingSliderListAPIView.as_view(), name='landing-slider'),
]
