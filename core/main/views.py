from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from .models import  *
from .serializers import *
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from django.conf import settings

# === Landing Content ===
class LandingContentView(APIView):
    def get(self, request):
        content = LandingContent.objects.filter(is_published=True).order_by('-updated_at').first()
        if not content:
            return Response({'error': 'No published landing content'}, status=404)
        serializer = LandingContentSerializer(content, context={'request': request})
        return Response(serializer.data)

# === Banner ===
class BannerAPIView(APIView):
    def get(self, request):
        qs = Banner.objects.filter(is_published=True).order_by('-created_at')
        serializer = BannerSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
    
# === Features ===
class FeatureListAPIView(APIView):
    def get(self, request):
        qs = Feature.objects.filter(is_published=True).order_by('created_at')
        serializer = FeatureSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

# === Benefits ===
class BenefitListAPIView(APIView):
    def get(self, request):
        qs = Benefit.objects.filter(is_published=True).order_by('-created_at')
        serializer = BenefitSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

# === Statistics ===
class StatisticListAPIView(APIView):
    def get(self, request):
        queryset = Statistic.objects.filter(is_published=True).order_by('-created_at')
        serializer = StatisticSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
# === Categories with Subcategories and Tools ===
class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.prefetch_related('subcategories__tools').all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class ToolPageDetailView(APIView):
    def get(self, request, slug):
        tool = get_object_or_404(ToolPage.objects.prefetch_related('blocks'), slug=slug)
        serializer = FullToolPageSerializer(tool, context={'request': request})
        return Response(serializer.data)

# === Site Settings ===
class SiteSettingsAPIView(APIView):
    def get(self, request):
        settings = SiteSettings.objects.first()
        if not settings:
            return Response({'error': 'Site settings not configured'}, status=404)
        serializer = SiteSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)

class ResearchList(APIView):
    def get(self, request):
        queryset = Research.objects.all() 
        serializer = ResearchSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
class PrivacyPolicyView(RetrieveAPIView):
    queryset = PrivacyPolicy.objects.all()
    serializer_class = PrivacyPolicySerializer

    def get_object(self):
        return PrivacyPolicy.objects.latest('updated_at')

class TermsAndConditionsView(RetrieveAPIView):
    queryset = TermsAndConditions.objects.all()
    serializer_class = TermsAndConditionsSerializer

    def get_object(self):
        return TermsAndConditions.objects.latest('updated_at')

class SecurityPolicyView(RetrieveAPIView):
    queryset = SecurityPolicy.objects.all()
    serializer_class = SecurityPolicySerializer

    def get_object(self):
        return SecurityPolicy.objects.latest('updated_at')
    

class AboutView(APIView):
    def get(self, request):
        try:
            about = About.objects.latest('updated_at')
            serializer = AboutSerializer(about)
            return Response(serializer.data)
        except About.DoesNotExist:
            return Response({"detail": "About content not found."}, status=404)

class ContactFormAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            name = serializer.validated_data["name"]
            email = serializer.validated_data["email"]
            message = serializer.validated_data["message"]

            subject = f"New Contact Message from {name}"
            full_message = f"From: {name} <{email}>\n\nMessage:\n{message}"

            send_mail(
                subject,
                full_message,
                settings.EMAIL_HOST_USER,
                [settings.DEFAULT_TO_EMAIL],
                fail_silently=False,
            )

            return Response({"detail": "Message received successfully."}, status=201)
        return Response(serializer.errors, status=400)
    
class TeamServiceListAPIView(APIView):
    def get(self, request):
        teams = TeamService.objects.all()
        serializer = TeamSerializer(teams, many=True, context={'request': request})
        return Response(serializer.data)
    
class SubscribeView(APIView):
    def post(self, request):
        serializer = SubscriberSerializer(data=request.data)
        if serializer.is_valid():
            subscriber = serializer.save()

            send_mail(
                subject="New subscriber",
                message=f"New email subscribed: {subscriber.email}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
            return Response({"message": "Subscribed successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LandingSliderListAPIView(APIView):
    def get(self, request):
        sliders = LandingSlider.objects.filter(is_published=True).order_by('-time_create')
        serializer = LandingSliderSerializer(sliders, many=True, context={'request': request})
        return Response(serializer.data)
    