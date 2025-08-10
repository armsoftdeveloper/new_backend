from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import (
    Plan, Subscription, ScanFolder, PlanToolAccess, ToolPage
)
import requests

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        if self.is_temp_email(value):
            raise serializers.ValidationError("Temporary email addresses are not allowed.")

        return value

    def is_temp_email(self, email):
        try:
            res = requests.get(f"https://open.kickbox.com/v1/disposable/{email}", timeout=5)
            res.raise_for_status()
            result = res.json()
            return result.get("disposable", False)
        except Exception as e:
            print("⚠️ Failed to verify email:", e)
            raise serializers.ValidationError("Could not validate email address. Try again later.")

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_name', 'start_date',
            'end_date', 'status', 'times_renewed', 'attempts_left'
        ]


class ToolMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolPage
        fields = ['id', 'title', 'slug']


class PlanSerializer(serializers.ModelSerializer):
    tools = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id', 'slug', 'name', 'description',
            'monthly_price', 'yearly_price',
            'monthly_attempts_limit', 'yearly_attempts_limit',
            'monthly_features', 'yearly_features',
            'tools'
        ]

    def get_tools(self, obj):
        accesses = obj.tool_accesses.select_related('tool')
        return ToolMiniSerializer([a.tool for a in accesses], many=True).data


class ScanFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanFolder
        fields = ['id', 'name', 'created_at']
