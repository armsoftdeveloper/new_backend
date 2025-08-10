import shlex
import subprocess
import requests
from time import time
from django.http import HttpResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import ScanResult
from .serializers import ScanResultSerializer
from users.models import Subscription
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

def is_command_safe(args):
    forbidden = {'sudo', 'shutdown', 'reboot', 'mkfs', 'mount'}
    shell_tokens = {'&', '&&', ';', '|'}
    for arg in args:
        if arg in forbidden:
            return False
        if any(token in arg for token in shell_tokens):
            return False
    return True

def get_public_ip():
    try:
        res = requests.get("https://api.ipify.org?format=json", timeout=5)
        res.raise_for_status()
        return res.json().get("ip")
    except requests.RequestException:
        return None

def get_ip_geoinfo(ip):
    try:
        res = requests.get(f"https://ipwho.is/{ip}", timeout=5)
        res.raise_for_status()
        return res.json() if res.json().get("success") else {}
    except Exception:
        return {}

def make_scan_view(command_name, default_args=None, timeout=180, use_bash_c=False):
    class GenericScanView(APIView):
        permission_classes = [AllowAny]

        def post(self, request):
            command_line = request.data.get("command")
            target = request.data.get("target")

            if not command_line and not target:
                return Response({"error": "Provide either 'command' or 'target'."}, status=400)
            if command_line and target:
                return Response({"error": "Provide only one of 'command' or 'target', not both."}, status=400)

            try:
                if command_line:
                    args = shlex.split(command_line)
                else:
                    args = [target]

                if use_bash_c:
                    args = [' '.join((default_args or []) + args)]
                else:
                    args = (default_args or []) + args

                if not is_command_safe(args):
                    return Response({"error": "Unsafe command detected"}, status=400)

                user = request.user if request.user.is_authenticated else None

                if user:
                    subscription = Subscription.objects.filter(user=user).first()
                    if not subscription:
                        return Response({"error": "No subscription found"}, status=403)

                    subscription.expire_if_needed()

                    if not subscription.is_active():
                        return Response({"error": "Subscription expired."}, status=403)

                    if subscription.attempts_left <= 0:
                        return Response({"error": "No attempts left. Please upgrade your plan."}, status=403)

                    subscription.use_attempt()
                else:
                    attempts_left = request.session.get("guest_attempts", 3)
                    if attempts_left <= 0:
                        return Response({"error": "Guest scan limit exceeded. Please register."}, status=403)
                    request.session["guest_attempts"] = attempts_left - 1
                    request.session.modified = True

                start_time = time()
                cmd = ['wsl', command_name] + args
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                duration = round(time() - start_time, 2)

                ip_address = get_public_ip() or "8.8.8.8"
                geo = get_ip_geoinfo(ip_address)

                ScanResult.objects.create(
                    user=user,
                    scanner=command_name,
                    command=' '.join(args),
                    output=result.stdout,
                    ip_address=ip_address,
                    country=geo.get("country"),
                    country_code=geo.get("country_code"),
                    city=geo.get("city"),
                    region=geo.get("region"),
                    region_code=geo.get("region_code"),
                    continent_code=geo.get("continent_code"),
                    timezone=geo.get("timezone", {}).get("id"),
                    utc_offset=geo.get("utc_offset"),
                    latitude=geo.get("latitude"),
                    longitude=geo.get("longitude"),
                    org=geo.get("org"),
                    asn=geo.get("asn"),
                )

                return Response({
                    "output": result.stdout,
                    "error_output": result.stderr,
                    "duration_sec": duration
                })

            except subprocess.TimeoutExpired:
                return Response({"error": f"{command_name} scan timed out"}, status=408)
            except Exception as e:
                return Response({"error": str(e)}, status=500)

    return GenericScanView

NmapScanView = make_scan_view("nmap", timeout=120)
ZmapScanView = make_scan_view("zmap", timeout=120)
PingView = make_scan_view("ping", default_args=["-c", "4"], timeout=30)
NiktoScanView = make_scan_view("nikto", timeout=180)
TracerouteView = make_scan_view("traceroute", timeout=60)
WhatwebScanView = make_scan_view("whatweb", timeout=120)
WPScanView = make_scan_view("wpscan", timeout=180)
DNSReconScanView = make_scan_view("dnsrecon", timeout=120)
XSStrikeScanView = make_scan_view("/home/armen/tools/XSStrike/venv/bin/python", default_args=["/home/armen/tools/XSStrike/xsstrike.py"], timeout=180)
DNScanView = make_scan_view("python3", default_args=["/home/armen/tools/dnscan/dnscan.py"], timeout=120)
SQLMapScanView = make_scan_view("sqlmap", timeout=180)
CommixScanView = make_scan_view("/snap/bin/commix", timeout=180)
JoomlaVSSCanView = make_scan_view("ruby", default_args=["/home/armen/tools/joomlavs/joomlavs.rb", "-u"], timeout=180)
GitDumperScanView = make_scan_view("/home/armen/tools/XSStrike/venv/bin/python", default_args=["/home/armen/tools/git-dumper/git_dumper.py"], timeout=180)
SchemathesisScanView = make_scan_view("/bin/bash", default_args=["-c", "/root/.local/bin/schemathesis"], timeout=180, use_bash_c=True)
LynxScanView = make_scan_view("lynx", timeout=60)
NucleiScanView = make_scan_view("nuclei", default_args=["-severity", "medium,high,critical"], timeout=180)
TestSSLView = make_scan_view("wsl", default_args=["/home/armen/testssl.sh/testssl.sh"], timeout=180)

def download_cef_output(request, scan_id):
    try:
        scan = ScanResult.objects.get(pk=scan_id)
    except ScanResult.DoesNotExist:
        raise Http404("Scan not found")

    safe_msg = scan.output[:1000].replace('\n', ' ')[:1000]
    cef = (
        f"CEF:0|WebScanner|{scan.scanner}|1.0|100|Scan Event|Low|"
        f"src={scan.ip_address or 'unknown'} "
        f"suser={(scan.user.username if scan.user else 'guest')} "
        f"request={scan.command} "
        f"msg={safe_msg}"
    )

    filename = f"scan_{scan.id}_{scan.scanner}.cef"
    response = HttpResponse(cef, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

logger = logging.getLogger(__name__)

class MultiScanView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Получаем данные из запроса
        command = request.data.get('command')
        scanners = request.data.get('scanners', [])
        scan_type = request.data.get('scan_type', 'custom')

        if not command or not scanners:
            return Response({"error": "Command and scanners are required"}, status=400)

        if isinstance(scanners, str):
            scanners = [scanners]  # если передан только один сканер, преобразуем его в список

        # Проверка подписки или попыток
        user = request.user if request.user.is_authenticated else None
        if user:
            subscription = Subscription.objects.filter(user=user).first()
            if not subscription or not subscription.is_active():
                return Response({"error": "No active subscription found."}, status=403)

        results = []
        try:
            # Используем потоковый подход для параллельной обработки сканов
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_scanner = {
                    executor.submit(self.run_scan, scanner, command): scanner for scanner in scanners
                }
                for future in concurrent.futures.as_completed(future_to_scanner):
                    scanner = future_to_scanner[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        logger.error(f"Error with scanner {scanner}: {exc}")
                        results.append({"scanner": scanner, "error": str(exc)})

            return Response({"results": results})

        except Exception as e:
            logger.error(f"Error during scanning: {str(e)}")
            return Response({"error": str(e)}, status=500)

    def run_scan(self, scanner, command):
        """
        Запускает команду для каждого сканера и возвращает результат.
        """
        try:
            cmd = self.get_command_for_scanner(scanner, command)
            if not cmd:
                return {"scanner": scanner, "error": "Unsupported scanner"}

            # Выполняем команду с ограничением по времени
            process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=120)

            # Сохранение результата в базе данных
            ScanResult.objects.create(
                scanner=scanner,
                command=command,
                output=stdout.decode(),
            )

            return {"scanner": scanner, "output": stdout.decode(), "error_output": stderr.decode()}

        except subprocess.TimeoutExpired:
            return {"scanner": scanner, "error": f"{scanner} scan timed out"}
        except Exception as e:
            return {"scanner": scanner, "error": f"Error running {scanner}: {str(e)}"}

    def get_command_for_scanner(self, scanner, command):
        """
        Method to get the command for each scanner.
        """
        commands = {
            "nmap": f"wsl /usr/bin/nmap {command}",
            "zmap": f"wsl /usr/bin/zmap {command}",
            "ping": f"wsl ping -c 4 {command}",
            "nikto": f"wsl /usr/bin/nikto {command}",
            "traceroute": f"wsl /usr/bin/traceroute {command}",
            "whatweb": f"wsl /usr/bin/whatweb {command}",
            "wpscan": f"wsl /usr/bin/wpscan {command}",
            "joomlavss": f"wsl ruby /home/armen/tools/joomlavs/joomlavs.rb -u {command}",
            "dnsrecon": f"wsl /usr/bin/dnsrecon {command}",
            "dnsscan": f"wsl python3 /home/armen/tools/dnscan/dnscan.py {command}",
            "xssstrike": f"wsl python3 /home/armen/tools/XSStrike/xsstrike.py {command}",
            "nuclei": f"wsl /usr/bin/nuclei {command}",
            "testssl": f"wsl /home/armen/testssl.sh/testssl.sh {command}",
            "gitdumper": f"wsl python3 /home/armen/tools/git-dumper/git_dumper.py {command}",
            "schemathesis": f"wsl /bin/bash -c /root/.local/bin/schemathesis {command}",
            "lynx": f"wsl lynx {command}",
        }
        return commands.get(scanner)

