from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class MyAdminSite(AdminSite):
    site_header = _("My Admin")
    site_title = _("Admin Portal")
    index_title = _("Welcome to Admin")

    def get_app_list(self, request):
        """
        
        """
        app_list = super().get_app_list(request)

        # Плоский список всех моделей
        all_models = []
        for app in app_list:
            for model in app["models"]:
                all_models.append((app["name"], model))

        # Задай порядок здесь по verbose_name модели
        desired_order = [
            "Site settings",
            "Contact messages",
            "Subscribers",
            "Landing contents",
            "Banners",
            "Features",
            "Benefits",
            "Statistics",
            "Tools",
            "Researches",
            "Privacy policies",
            "Terms and conditions",
            "Security policies",
            "Abouts",
        ]

        def model_sort_key(item):
            _, model = item
            try:
                return desired_order.index(model["name"])
            except ValueError:
                return len(desired_order)  # всё остальное внизу

        sorted_models = sorted(all_models, key=model_sort_key)

        # Группируем обратно по приложениям
        new_app_dict = {}
        for app_name, model in sorted_models:
            new_app_dict.setdefault(app_name, []).append(model)

        new_app_list = []
        for app in app_list:
            if app["name"] in new_app_dict:
                app["models"] = new_app_dict[app["name"]]
                new_app_list.append(app)

        return new_app_list
