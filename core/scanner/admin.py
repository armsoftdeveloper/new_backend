from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *

@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'scanner', 'command', 'ip_address', 'city', 'region', 'address', 'created_at' , 'download_cef_link')
    
    readonly_fields = (
        'user', 'scanner', 'command', 'output', 'ip_address', 'mac_address',
        'country', 'region_code', 'continent_code', 'timezone', 'utc_offset',
        'latitude', 'longitude', 'org', 'asn', 'created_at', 'location_map', 'address' , 'download_cef_link'
    )

    def location_map(self, obj):
        if obj.latitude and obj.longitude:
            return mark_safe(f"""
                <div id="map_{obj.id}" style="height: 400px;"></div>
                <script>
                  var map = L.map('map_{obj.id}').setView([{obj.latitude}, {obj.longitude}], 16);
                  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
                  }}).addTo(map);
                  L.marker([{obj.latitude}, {obj.longitude}]).addTo(map)
                    .bindPopup('{obj.city or "Unknown"}').openPopup();
                </script>
            """)
        return "Нет координат"

    location_map.short_description = "Местоположение на карте"

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet/dist/leaflet.css',),
        }
        js = (
            'https://unpkg.com/leaflet/dist/leaflet.js',
        )

    def download_cef_link(self, obj):
        return mark_safe(
            f'<a href="/download-cef/{obj.id}/" target="_blank">📄 Скачать в CEF</a>'
        )
    download_cef_link.short_description = "CEF"