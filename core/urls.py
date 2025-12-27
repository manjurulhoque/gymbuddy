from django.urls import path
from .views import (
    HomeView, DashboardView, PrivacyPolicyView, TermsConditionsView,
    ThemeSettingsView, ThemeListView
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-conditions/", TermsConditionsView.as_view(), name="terms_conditions"),
    path("settings/theme/", ThemeSettingsView.as_view(), name="theme_settings"),
    path("themes/", ThemeListView.as_view(), name="theme_list"),
]
