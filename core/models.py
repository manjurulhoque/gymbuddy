from django.db import models
from django.conf import settings


class Theme(models.Model):
    """
    Model to define different color themes for the application.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the theme (e.g., 'Emerald', 'Blue', 'Purple')"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier for the theme"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default theme"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this theme is available for selection"
    )
    
    # Primary colors (main brand color)
    primary_color = models.CharField(
        max_length=7,
        default="#10b981",  # emerald-500
        help_text="Primary color in hex format (e.g., #10b981)"
    )
    primary_color_dark = models.CharField(
        max_length=7,
        default="#059669",  # emerald-600
        help_text="Darker shade of primary color"
    )
    primary_color_light = models.CharField(
        max_length=7,
        default="#34d399",  # emerald-400
        help_text="Lighter shade of primary color"
    )
    
    # Secondary colors (accent color)
    secondary_color = models.CharField(
        max_length=7,
        default="#14b8a6",  # teal-500
        help_text="Secondary color in hex format"
    )
    secondary_color_dark = models.CharField(
        max_length=7,
        default="#0d9488",  # teal-600
        help_text="Darker shade of secondary color"
    )
    secondary_color_light = models.CharField(
        max_length=7,
        default="#5eead4",  # teal-400
        help_text="Lighter shade of secondary color"
    )
    
    # Tailwind color classes (for easy template usage)
    primary_tailwind = models.CharField(
        max_length=50,
        default="emerald",
        help_text="Tailwind color name for primary (e.g., 'emerald', 'blue', 'purple')"
    )
    secondary_tailwind = models.CharField(
        max_length=50,
        default="teal",
        help_text="Tailwind color name for secondary"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the theme"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Theme"
        verbose_name_plural = "Themes"
        ordering = ["-is_default", "name"]

    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.name}{default_marker}"

    def save(self, *args, **kwargs):
        # Ensure only one default theme
        if self.is_default:
            Theme.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Settings(models.Model):
    """
    Site-wide settings model (singleton pattern).
    This model stores global application settings that can be updated later.
    """
    # Singleton identifier - only one instance should exist
    singleton_key = models.CharField(
        max_length=50,
        default="site_settings",
        unique=True,
        editable=False,
        help_text="Singleton identifier to ensure only one settings instance exists"
    )
    
    theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_settings",
        help_text="Site-wide theme preference (null means use default theme)"
    )
    
    # Additional settings can be added here later
    # site_name = models.CharField(max_length=200, default="GymBuddy")
    # site_description = models.TextField(blank=True)
    # maintenance_mode = models.BooleanField(default=False)
    # etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
        ordering = ["-updated_at"]

    def __str__(self):
        theme_name = self.theme.name if self.theme else "Default"
        return f"Site Settings (Theme: {theme_name})"

    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists."""
        self.singleton_key = "site_settings"
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        settings, created = cls.objects.get_or_create(
            singleton_key="site_settings",
            defaults={}
        )
        return settings

    def get_active_theme(self):
        """Get the active theme (site preference or default)."""
        if self.theme and self.theme.is_active:
            return self.theme
        return Theme.objects.filter(is_default=True, is_active=True).first()
