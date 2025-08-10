from django.db import models
from django.contrib.auth.models import User


class ScanResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    scanner = models.CharField(max_length=50)
    command = models.TextField()
    output = models.TextField()
    ip_address = models.CharField(max_length=100, null=True, blank=True)
    mac_address = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # GeoIP fields
    country = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    region_code = models.CharField(max_length=10, blank=True, null=True)
    continent_code = models.CharField(max_length=10, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    utc_offset = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    org = models.CharField(max_length=200, blank=True, null=True)
    asn = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user or 'Guest'} — {self.scanner} — {self.created_at.strftime('%Y-%m-%d %H:%M')}"
