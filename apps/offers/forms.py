from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db.models import Q
from .models import Offer, Element, ElementSubType, ElementType


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['title', 'description', 'price', 'discount_percentage', 'start_date', 'end_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter offer title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter offer description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount percentage', 'step': '0.01', 'min': '0', 'max': '100'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(OfferForm, self).__init__(*args, **kwargs)
        
        # Set default values
        if not self.instance.pk:  # New offer
            self.fields['is_active'].initial = True
            if 'start_date' not in self.data:
                self.fields['start_date'].initial = timezone.now().date()


class ElementForm(forms.ModelForm):
    class Meta:
        model = Element
        fields = ['element_type', 'sub_type', 'quantity', 'Dx', 'Dy', 'Dz']
        widgets = {
            'element_type': forms.Select(attrs={'class': 'form-control element-type-select'}),
            'sub_type': forms.Select(attrs={'class': 'form-control element-subtype-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'Dx': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Dx'}),
            'Dy': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Dy'}),
            'Dz': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Dz'}),
        }

    def __init__(self, *args, **kwargs):
        super(ElementForm, self).__init__(*args, **kwargs)
        self.fields['element_type'].choices = [('', '---------')] + list(ElementType.choices)
        
        # Filter sub_type based on element_type
        element_type = None
        selected_sub_type_id = None
        
        # Check if we have instance data (editing existing element)
        if self.instance and self.instance.pk:
            element_type = self.instance.element_type
            self.fields['sub_type'].queryset = ElementSubType.objects.filter(type=element_type)
        # Check if we have POST data (form submission)
        elif self.data:
            # Get the prefix for this form (formset uses prefixes like 'elements-0', 'elements-1', etc.)
            prefix = kwargs.get('prefix', '')
            
            # Construct the field name with prefix
            if prefix:
                element_type_key = f'{prefix}-element_type'
                sub_type_key = f'{prefix}-sub_type'
            else:
                element_type_key = 'element_type'
                sub_type_key = 'sub_type'
            
            element_type = self.data.get(element_type_key)
            selected_sub_type_id = self.data.get(sub_type_key)
            
            # Build queryset: filter by element_type, but always include selected sub_type
            if element_type:
                # Start with subtypes matching the element_type
                queryset = ElementSubType.objects.filter(type=element_type)
                
                # Always include the selected sub_type if provided (to avoid validation errors)
                if selected_sub_type_id:
                    try:
                        selected_id = int(selected_sub_type_id)
                        # Use Q objects to include both the filtered types and the selected one
                        queryset = ElementSubType.objects.filter(
                            Q(type=element_type) | Q(pk=selected_id)
                        )
                    except (ValueError, TypeError):
                        pass
                
                self.fields['sub_type'].queryset = queryset
            else:
                # No element_type selected yet, but include selected sub_type if any
                if selected_sub_type_id:
                    try:
                        selected_id = int(selected_sub_type_id)
                        self.fields['sub_type'].queryset = ElementSubType.objects.filter(pk=selected_id)
                    except (ValueError, TypeError, ElementSubType.DoesNotExist):
                        # Fallback to all if we can't find the specific one
                        self.fields['sub_type'].queryset = ElementSubType.objects.all()
                else:
                    # No data yet, show all (will be filtered by JS)
                    self.fields['sub_type'].queryset = ElementSubType.objects.all()
        else:
            # Initial form load - no data yet
            self.fields['sub_type'].queryset = ElementSubType.objects.none()


# Create formset factory
ElementFormSet = inlineformset_factory(
    Offer,
    Element,
    form=ElementForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)


