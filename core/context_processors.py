from .models import Theme, Settings


def theme_context(request):
    """
    Context processor to inject theme data into all templates.
    Uses site-wide settings to determine the active theme.
    """
    context = {}
    
    # Get site settings (singleton)
    site_settings = Settings.get_settings()
    active_theme = site_settings.get_active_theme()
    
    # If no theme found, create a default one
    if not active_theme:
        active_theme = Theme.objects.filter(is_active=True).first()
        if not active_theme:
            # Create a default emerald theme if none exists
            active_theme = Theme.objects.create(
                name="Emerald",
                slug="emerald",
                is_default=True,
                is_active=True,
                primary_tailwind="emerald",
                secondary_tailwind="teal"
            )
    
    # Add theme data to context
    context['active_theme'] = active_theme
    context['site_settings'] = site_settings
    context['theme_primary'] = active_theme.primary_tailwind
    context['theme_secondary'] = active_theme.secondary_tailwind
    context['theme_primary_color'] = active_theme.primary_color
    context['theme_secondary_color'] = active_theme.secondary_color
    context['theme_primary_dark'] = active_theme.primary_color_dark
    context['theme_secondary_dark'] = active_theme.secondary_color_dark
    context['theme_primary_light'] = active_theme.primary_color_light
    context['theme_secondary_light'] = active_theme.secondary_color_light
    
    return context

