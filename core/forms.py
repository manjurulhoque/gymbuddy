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


class ThemeAdminForm(forms.ModelForm):
    """Form for admin to create/edit themes."""
    
    class Meta:
        model = Theme
        fields = [
            'name', 'slug', 'is_default', 'is_active',
            'primary_color', 'primary_color_dark', 'primary_color_light',
            'secondary_color', 'secondary_color_dark', 'secondary_color_light',
            'primary_tailwind', 'secondary_tailwind', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'primary_color_dark': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'primary_color_light': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color_dark': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color_light': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'primary_tailwind': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_tailwind': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

