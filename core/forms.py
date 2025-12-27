from django import forms
from .models import Theme, Settings


class ThemeSelectionForm(forms.ModelForm):
    """Form for selecting site-wide theme."""
    
    class Meta:
        model = Settings
        fields = ['theme']
        widgets = {
            'theme': forms.RadioSelect(attrs={'class': 'theme-radio'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active themes
        self.fields['theme'].queryset = Theme.objects.filter(is_active=True).order_by('-is_default', 'name')
        self.fields['theme'].required = False
        self.fields['theme'].empty_label = "Use Default Theme"


class ThemeForm(forms.ModelForm):
    """Form for creating/editing themes."""
    
    class Meta:
        model = Theme
        fields = [
            'name', 'slug', 'is_default', 'is_active',
            'primary_color', 'primary_color_dark', 'primary_color_light',
            'secondary_color', 'secondary_color_dark', 'secondary_color_light',
            'primary_tailwind', 'secondary_tailwind', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Emerald, Blue, Purple'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'auto-generated from name'
            }),
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'primary_color_dark': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'primary_color_light': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'secondary_color_dark': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'secondary_color_light': forms.TextInput(attrs={
                'type': 'color',
                'class': 'w-20 h-10 border border-slate-300 rounded cursor-pointer'
            }),
            'primary_tailwind': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., emerald, blue, purple'
            }),
            'secondary_tailwind': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., teal, cyan, indigo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Optional description of this theme'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make slug optional and auto-populate if empty
        self.fields['slug'].required = False
        if not self.instance.pk:  # New theme
            self.fields['is_default'].help_text = "Setting this as default will unset other default themes"
    
    def clean_slug(self):
        """Auto-generate slug from name if not provided."""
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        if not slug and name:
            # Auto-generate slug from name
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        
        return slug

