from django.contrib import admin
from django.utils.html import format_html
from .models import Theme, Settings


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_default', 'is_active', 'primary_tailwind', 'secondary_tailwind', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_default', 'is_active')
        }),
        ('Primary Colors', {
            'fields': ('primary_tailwind', 'primary_color', 'primary_color_dark', 'primary_color_light')
        }),
        ('Secondary Colors', {
            'fields': ('secondary_tailwind', 'secondary_color', 'secondary_color_dark', 'secondary_color_light')
        }),
    )


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'theme', 'updated_at']
    list_filter = ['theme', 'updated_at']
    readonly_fields = ['singleton_key', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one settings instance."""
        return Settings.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings."""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Make singleton_key readonly."""
        if obj:
            return self.readonly_fields
        return self.readonly_fields
