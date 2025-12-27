from django import template

register = template.Library()


@register.simple_tag
def theme_color(color_type, shade="500"):
    """
    Template tag to get theme color classes.
    
    Usage:
        {% theme_color 'primary' %} -> returns 'emerald-500'
        {% theme_color 'primary' '600' %} -> returns 'emerald-600'
        {% theme_color 'secondary' %} -> returns 'teal-500'
    """
    # This will be populated by the context processor
    # We'll use it in templates like: class="bg-{% theme_color 'primary' %}-500"
    return ""


@register.simple_tag(takes_context=True)
def theme_class(context, color_type, shade="500", prefix=""):
    """
    Template tag to generate Tailwind classes with theme colors.
    
    Usage:
        {% theme_class 'primary' '500' 'bg' %} -> returns 'bg-emerald-500'
        {% theme_class 'secondary' '600' 'text' %} -> returns 'text-teal-600'
        {% theme_class 'primary' %} -> returns 'emerald-500'
    """
    theme_primary = context.get('theme_primary', 'emerald')
    theme_secondary = context.get('theme_secondary', 'teal')
    
    if color_type == 'primary':
        color = theme_primary
    elif color_type == 'secondary':
        color = theme_secondary
    else:
        color = 'slate'  # fallback
    
    class_name = f"{color}-{shade}"
    
    if prefix:
        return f"{prefix}-{class_name}"
    
    return class_name


@register.simple_tag(takes_context=True)
def theme_gradient(context, color_type="primary"):
    """
    Template tag to generate gradient classes with theme colors.
    
    Usage:
        {% theme_gradient 'primary' %} -> returns 'from-emerald-500 to-teal-600'
        {% theme_gradient 'secondary' %} -> returns 'from-teal-500 to-cyan-600'
    """
    theme_primary = context.get('theme_primary', 'emerald')
    theme_secondary = context.get('theme_secondary', 'teal')
    
    if color_type == 'primary':
        return f"from-{theme_primary}-500 to-{theme_secondary}-600"
    elif color_type == 'secondary':
        return f"from-{theme_secondary}-500 to-{theme_secondary}-600"
    else:
        return f"from-{theme_primary}-500 to-{theme_secondary}-600"

