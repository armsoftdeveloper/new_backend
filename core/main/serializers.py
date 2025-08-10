
# serializers.py
from rest_framework import serializers
from .models import *

class LandingContentSerializer(serializers.ModelSerializer):
    background_video_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingContent
        fields = "__all__"

    def get_background_video_url(self, obj):
        request = self.context.get('request')
        if obj.background_video and request:
            return request.build_absolute_uri(obj.background_video.url)
        return None
    
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']

class FeatureSerializer(serializers.ModelSerializer):
    desc = serializers.CharField(source='description')

    class Meta:
        model = Feature
        fields = ['title', 'desc']

class TeamSerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = TeamService
        fields = ['id', 'team', 'title' , 'description', 'icon_url', 'updated_at']

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon and request:
            return request.build_absolute_uri(obj.icon.url)
        return None

class BenefitSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Benefit
        fields = ['id', 'icon_key', 'title', 'description', 'image', 'is_published', 'created_at', 'updated_at']

class StatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistic
        fields = [
            'id',
            'title',
            'value',
            'is_published',
            'suffix',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

class ToolBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolBlock
        fields = ['title', 'content']


class ToolPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolPage
        fields = '__all__'

class FullToolPageSerializer(serializers.ModelSerializer):
    blocks = ToolBlockSerializer(many=True, read_only=True)

    class Meta:
        model = ToolPage
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    tools = ToolPageSerializer(many=True, read_only=True)

    class Meta:
        model = SubCategory
        fields = ['name', 'slug', 'tools']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['name', 'slug', 'description','subcategories']

class SiteSettingsSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = [
            'logo_url',
            'email',
            'twitter_url',
            'github_url',
            'linkedin_url',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

class ResearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Research
        fields = ['id', 'title', 'description', 'image', 'created_at', 'updated_at']
        
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'title', 'content',]


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditions
        fields = ['id', 'title', 'content',]


class SecurityPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityPolicy
        fields = ['id', 'title', 'content',]

class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = '__all__'

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['email']

class LandingSliderSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingSlider
        fields = ['id', 'image_url', 'is_published', 'time_create', 'time_update']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
    