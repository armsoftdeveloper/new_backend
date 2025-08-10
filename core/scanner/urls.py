from django.urls import path
from .views import *
from scanner.views import *

urlpatterns = [
    path('nmap/', NmapScanView.as_view(), name='nmap-scan'),
    path('zmap/', ZmapScanView.as_view(), name='zmap-scan'),
    path('ping/', PingView.as_view(), name='ping-scan'),
    path('nikto/', NiktoScanView.as_view(), name='nikto-scan'),
    path('traceroute/', TracerouteView.as_view(), name='traceroute-scan'),
    path('whatweb/', WhatwebScanView.as_view(), name='whatweb-scan'),
    path('wpscan/', WPScanView.as_view(), name='wpscan-scan'),
    path('dnsrecon/', DNSReconScanView.as_view(), name='dnsrecon-scan'),
    path('xsstrike/', XSStrikeScanView.as_view(), name='xsstrike-scan'),
    path('dnsscan/', DNScanView.as_view(), name='dnscan-scan'),
    path('sql-map/', SQLMapScanView.as_view(), name='sqlmap-scan'),
    path('commix/', CommixScanView.as_view(), name='commix-scan'),
    path('joomlavs/', JoomlaVSSCanView.as_view(), name='joomlavs-scan'),
    path('gitdumper/', GitDumperScanView.as_view(), name='gitdumper-scan'),
    path('schemathesis/', SchemathesisScanView.as_view(), name='schemathesis-scan'),
    path('lynx/', LynxScanView.as_view(), name='lynx-scan'),
    path('nuclei/', NucleiScanView.as_view(), name='nuclei-scan'),
    path('testssl/', TestSSLView.as_view(), name='testssl-scan'),
    path('download-cef/<int:scan_id>/', download_cef_output, name='download_cef_output'),
    path('api/custom-scan/', MultiScanView.as_view(), name='custom-scan'),
]
