# users/views.py
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.contrib.auth.models import User
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.dateparse import parse_datetime
from .models import Subscription, Plan, ScanFolder
from django.utils import timezone
import traceback
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import update_session_auth_hash
import requests

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.microsoft.views import MicrosoftGraphOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from scanner.models import ScanResult


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = get_current_site(request).domain
            activation_link = f"http://{domain}/api/users/activate/{uid}/{token}/"

            subject = 'Confirm your email address'
            from_email = 'noreply@yourdomain.com'
            to_email = user.email

            html_content = render_to_string('emails/activation_email.html', {
                'activation_link': activation_link,
                'username': user.username,
            })
            text_content = f'Click to activate your account: {activation_link}'

            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()

            return Response({"message": "Registration successful. Check your email."}, status=201)

        return Response(serializer.errors, status=400)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subscription = Subscription.objects.filter(user=user, status='active').first()
        return Response({
            "username": user.username,
            "email": user.email,
            "last_login": user.last_login,
            "attempts_left": subscription.attempts_left if subscription else 0,
            "subscription": subscription.plan.slug if subscription else "none"
        })

    def put(self, request):
        user = request.user
        user.username = request.data.get('username', user.username)
        user.email = request.data.get('email', user.email)
        user.save()
        return Response({
            "username": user.username,
            "email": user.email
        })


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        slug = request.data.get("plan")
        if not slug:
            return Response({"error": "Missing 'plan' slug"}, status=400)

        try:
            plan = Plan.objects.get(slug=slug)
        except Plan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=404)

        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={
                "plan": plan,
                "start_date": timezone.now(),
                "end_date": timezone.now() + timezone.timedelta(days=30),
                "status": "active",
                # ❗️ИСПРАВЛЕНО: attempts_limit -> monthly_attempts_limit
                "attempts_left": plan.monthly_attempts_limit,
            }
        )

        if not created:
            subscription.plan = plan
            subscription.start_date = timezone.now()
            subscription.end_date = timezone.now() + timezone.timedelta(days=30)
            subscription.status = "active"
            subscription.attempts_left = plan.monthly_attempts_limit
            subscription.save()

        return Response({"message": "Plan changed successfully"}, status=200)


class PaypalWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        user_id = data.get('user_id')
        plan_slug = data.get('plan')
        start_date = parse_datetime(data.get('start_date'))
        end_date = parse_datetime(data.get('end_date'))

        if not user_id or not plan_slug or not start_date or not end_date:
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            plan = Plan.objects.get(slug=plan_slug)
        except Plan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            subscription = Subscription.objects.get(user=user, plan=plan)
            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.status = 'active'
            subscription.times_renewed += 1
            subscription.reset_attempts()
            subscription.save()
            created = False
        except Subscription.DoesNotExist:
            duration_days = (end_date - start_date).days if (start_date and end_date) else 30
            attempts = plan.yearly_attempts_limit if duration_days >= 365 else plan.monthly_attempts_limit

            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                status='active',
                times_renewed=0,
                attempts_left=attempts
            )
            created = True

        return Response({"message": "Subscription updated", "created": created}, status=status.HTTP_200_OK)


def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        return response.json().get("ip")
    except requests.RequestException as e:
        print(f"❌ Error fetching public IP: {e}")
        return None


def get_ip_geoinfo(ip):
    try:
        print(f"🌐 Fetching geo info for IP: {ip}")
        res = requests.get(f"https://ipwho.is/{ip}", timeout=5)
        res.raise_for_status()
        data = res.json()
        if data.get("success"):
            return data
        else:
            print(f"⚠️ ipwho.is failed: {data.get('message')}")
            return {}
    except Exception as e:
        print("🌐 GeoIP fetch error:", e)
        return {}


class ScannerProxyView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def run_nmap_scan(self, request):
        import shlex, subprocess

        def is_command_safe(args):
            forbidden = {'sudo', 'rm', 'shutdown', 'reboot', '&', '&&', ';', '|', 'mkfs', 'mount'}
            return all(not any(f in arg for f in forbidden) for arg in args)

        command_line = request.data.get('command')
        target = request.data.get('target')

        if not command_line and not target:
            return {"error": "Either command or target is required"}, 400

        try:
            args = shlex.split(command_line) if command_line else [target]
            if not is_command_safe(args):
                return {"error": "Unsafe command detected"}, 400
            cmd = ['wsl', 'nmap'] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {
                "output": result.stdout,
                "error_output": result.stderr
            }, 200
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out"}, 408
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self, request, slug):
        user = request.user if request.user.is_authenticated else None

        if user:
            try:
                subscription = Subscription.objects.get(user=user, status='active', end_date__gt=timezone.now())
                if subscription.attempts_left <= 0:
                    return Response({"error": "No attempts left. Please upgrade your plan."}, status=403)
                subscription.use_attempt()
                attempts_left = subscription.attempts_left
            except Subscription.DoesNotExist:
                return Response({"error": "No active subscription found."}, status=403)
        else:
            attempts_left = request.session.get("guest_attempts", 3)
            if attempts_left <= 0:
                return Response({"error": "Guest limit exceeded. Please login or register."}, status=403)
            request.session["guest_attempts"] = attempts_left - 1
            request.session.modified = True

        if slug == "nmap":
            data, status_code = self.run_nmap_scan(request)
            output = data.get("output", "[no output]")
        else:
            return Response({"error": f"Scanner '{slug}' not supported"}, status=400)

        ip_address = get_public_ip()
        if not ip_address:
            ip_address = '8.8.8.8'
        print(f"🌐 Real public IP: {ip_address}")

        geo_info = get_ip_geoinfo(ip_address)

        try:
            scan = ScanResult.objects.create(
                user=user,
                scanner=slug,
                command=request.data.get('command', '') or '',
                output=output or '[no output]',
                ip_address=ip_address,
                mac_address=None,

                country=geo_info.get("country"),
                country_name=geo_info.get("country_name"),
                country_code=geo_info.get("country_code"),
                country_code_iso3=geo_info.get("country_code_iso3"),
                country_capital=geo_info.get("country_capital"),
                country_tld=geo_info.get("country_tld"),
                country_calling_code=geo_info.get("country_calling_code"),
                country_area=geo_info.get("country_area"),
                country_population=geo_info.get("country_population"),

                city=geo_info.get("city"),
                region=geo_info.get("region"),
                region_code=geo_info.get("region_code"),
                continent_code=geo_info.get("continent_code"),

                timezone=geo_info.get("timezone", {}).get("id"),
                utc_offset=geo_info.get("utc_offset") or geo_info.get("timezone", {}).get("utc"),

                currency=geo_info.get("currency"),
                currency_name=geo_info.get("currency_name"),
                languages=geo_info.get("languages"),

                latitude=geo_info.get("latitude"),
                longitude=geo_info.get("longitude"),

                org=geo_info.get("org") or geo_info.get("connection", {}).get("org"),
                asn=geo_info.get("asn") or geo_info.get("connection", {}).get("asn"),
            )

            print(f"✅ ScanResult saved: {scan.id}")
        except Exception as e:
            print(f"❌ Failed to save ScanResult: {e}")

        data['attempts_left'] = attempts_left
        return Response(data, status=status_code)
    

class UserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = Subscription.objects.filter(user=request.user, status='active').first()
        if not subscription:
            return Response({"detail": "No active subscription"}, status=404)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class PlanListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)


class UserScanResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scans = ScanResult.objects.filter(user=request.user).order_by('-created_at')
        data = [
            {
                "id": s.id,
                "scanner": s.scanner,
                "output": s.output,
                "created_at": s.created_at,
            } for s in scans
        ]
        return Response(data)

class ScanFolderViewSet(viewsets.ModelViewSet):
    serializer_class = ScanFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScanFolder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ActivateUserView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return HttpResponse("Invalid activation link", status=400)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect("http://localhost:3000/account-activated")
        else:
            return HttpResponse("Invalid or expired token.", status=400)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"

            html_content = render_to_string("emails/password_reset_email.html", {
                "reset_link": reset_link,
                "username": user.username,
            })

            email_message = EmailMultiAlternatives(
                subject="Password Reset",
                body="Use HTML version",
                from_email="armsoftdeveloper@gmail.com",
                to=[user.email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return Response({"message": "Email sent."})
        except User.DoesNotExist:
            return Response({"detail": "No user with that email."}, status=400)


class ResetPasswordConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception as e:
            traceback.print_exc()
            return Response({"error": "Invalid link"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required"}, status=400)

        try:
            user.set_password(password)
            user.save()
            return Response({"message": "Password has been reset."}, status=200)
        except Exception as e:
            traceback.print_exc()
            return Response({"error": "Internal server error"}, status=500)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_password = request.data.get("password")
        if not new_password:
            return Response({"error": "Password is required"}, status=400)

        user = request.user
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return Response({"message": "Password updated successfully."})

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth/callback?provider=google"
    
class GithubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth/github/callbac"

class MicrosoftLogin(SocialLoginView):
    adapter_class = MicrosoftGraphOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth/callback?provider=microsoft"
