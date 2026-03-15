from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class Offer(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'), blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price'), null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Discount %'), null=True, blank=True)
    start_date = models.DateField(verbose_name=_('Start Date'), null=True, blank=True)
    end_date = models.DateField(verbose_name=_('End Date'), null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers', verbose_name=_('Created By'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Offer')
        verbose_name_plural = _('Offers')
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def recalculate_all_element_dimensions(self):
        """
        Calculate Dx and Dy for all ElementSubTypeElements related to this offer's elements.
        Uses Element.Dx, Dy, Dz (user input) as base dimensions.
        This should be called when user clicks "Save Offer" button.
        
        For each Element in the offer:
        1. Get all ElementSubTypeElements templates for that Element's sub_type
        2. For each template that has a formula_code, calculate Dx and Dy
        3. Save results to CalculatedElementSubTypeElement table
        
        Works even if no coefficients are selected (uses default values of 0).
        
        Returns:
            dict: Statistics about the recalculation (count of updated elements, errors, etc.)
        """
        from .calculations import calculate_element_dimensions
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        updated_count = 0
        error_count = 0
        
        # Get all Elements for this offer
        elements = self.elements.all()
        
        # If no elements exist yet (new offer), return empty stats
        if not elements.exists():
            return {
                'updated': 0,
                'errors': 0,
                'total': 0,
                'message': 'No elements found. Calculations will run after elements are added and saved.'
            }
        
        # For each Element, calculate all related ElementSubTypeElements
        for element in elements:
            # Get all ElementSubTypeElements templates for this Element's sub_type
            # Only those that have formula_code set (need calculation)
            sub_type_elements = ElementSubTypeElements.objects.filter(
                element_sub_type=element.sub_type
            ).exclude(
                models.Q(formula_code__isnull=True) | models.Q(formula_code='')
            )
            
            for sub_type_element in sub_type_elements:
                try:
                    logger.debug(
                        f"Calculating for Element {element.id}, "
                        f"ElementSubTypeElements {sub_type_element.id} "
                        f"(formula_code={sub_type_element.formula_code})"
                    )
                    
                    # Calculate dimensions using the formula
                    dimensions = calculate_element_dimensions(
                        element,
                        self,
                        sub_type_element
                    )
                    
                    # Create or update CalculatedElementSubTypeElement
                    calculated, created = CalculatedElementSubTypeElement.objects.update_or_create(
                        element=element,
                        sub_type_element=sub_type_element,
                        defaults={
                            'offer': self,
                            'Dx': dimensions['Dx'],
                            'Dy': dimensions['Dy'],
                            'element_name': sub_type_element.element_name,
                            'element_quantity': sub_type_element.element_quantity,
                            'element_price': sub_type_element.element_price,
                            'element_discount': sub_type_element.element_discount,
                            'element_total_price': sub_type_element.element_total_price,
                        }
                    )
                    
                    logger.info(
                        f"{'Created' if created else 'Updated'} CalculatedElementSubTypeElement "
                        f"{calculated.id} for Element {element.id}: Dx={calculated.Dx}, Dy={calculated.Dy}"
                    )
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(
                        f"Error calculating ElementSubTypeElements {sub_type_element.id} "
                        f"for Element {element.id}: {e}",
                        exc_info=True
                    )
                    error_count += 1
        
        return {
            'updated': updated_count,
            'errors': error_count,
            'total': updated_count + error_count
        }

class ElementType(models.TextChoices):
    DONJI = 'donji_elementi', 'Donji elementi'
    GORNI = 'gornji_elementi', 'Gornji elementi'
    VISOKI = 'visoki_elementi', 'Visoki elementi'
    LADICE = 'ladice', 'Ladice'


class ElementSubType(models.Model):
    type = models.CharField(max_length=50, choices=ElementType.choices)
    code = models.CharField(max_length=50, verbose_name='Code')  # npr DE1V, GE1V...
    name = models.CharField(max_length=100, verbose_name='Name', blank=True)

    Dx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    Dy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    Dz = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    image = models.ImageField(upload_to='elements/', null=True, blank=True)

    # Optional: list of extra input definitions for this sub-type (e.g. for Ladice).
    # Format: [{"name": "field_name", "label": "Label", "type": "number"|"text"|"select", "required": true/false, "options": [...]}]
    extra_fields_schema = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Extra fields schema'),
        help_text=_('JSON list of extra input definitions shown when this sub-type is selected (e.g. for Ladice).')
    )

    class Meta:
        unique_together = ('type', 'code')
        verbose_name = 'Element SubType'
        verbose_name_plural = 'Element SubTypes'

    def __str__(self):
        return self.name.strip() if self.name and self.name.strip() else f"{self.type} - {self.code}"
        

class Element(models.Model):
    offer = models.ForeignKey(
        'Offer', 
        on_delete=models.CASCADE, 
        related_name='elements'
    )
    element_type = models.CharField(max_length=50, choices=ElementType.choices)
    sub_type = models.ForeignKey(
        ElementSubType,
        on_delete=models.PROTECT,
        verbose_name='Sub Type',
        limit_choices_to=models.Q(type=models.F('type'))
    )

    quantity = models.PositiveIntegerField(default=1)
    Dx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='Dx')
    Dy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='Dy')
    Dz = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='Dz')
    # Ladice sub-type fields (saved only when present for the selected sub-type)
    dubina_ladice = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('DUBINA LADICE'))
    visina_fronte_1 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('VISINA 1. FRONTE'))
    visina_fronte_2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('VISINA 2. FRONTE'))
    visina_fronte_3 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('VISINA 3. FRONTE'))
    visina_fronte_4 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('VISINA 4. FRONTE'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['element_type', 'sub_type']

    def __str__(self):
        return f"{self.element_type} - {self.sub_type.code} ({self.offer.title})"
    

# ElementSubTypeElements is a configuration table that defines which elements exist for each ElementSubType
# This is a pure configuration table - no calculated data is stored here
class ElementSubTypeElements(models.Model):
    element_name = models.CharField(max_length=255, verbose_name=_('Element Name'))
    element_sub_type = models.ForeignKey(ElementSubType, on_delete=models.CASCADE, verbose_name=_('Element Sub Type'), related_name='sub_type_elements')
    element_quantity = models.IntegerField(verbose_name=_('Element Quantity'), default=1)
    element_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Price'), default=0)
    element_discount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Discount'), default=0)
    element_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Total'), default=0)
    
    # Formula code to identify which formula to use for this element
    # If set, Dx and Dy will be calculated when saving the offer using this formula
    # The formula should calculate and return both Dx and Dy values
    formula_code = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Formula Code'), 
                                    help_text=_('If set, Dx and Dy will be calculated using this formula when saving the offer. The formula calculates both dimensions together.'))

    class Meta:
        verbose_name = _('ElementSubTypeElements')
        verbose_name_plural = _('ElementSubTypeElements')
        unique_together = ('element_sub_type', 'element_name')

    def __str__(self):
        return f"{self.element_sub_type.code} - {self.element_name}"


# CalculatedElementSubTypeElement stores the calculated results for each Element in an Offer
class CalculatedElementSubTypeElement(models.Model):
    offer = models.ForeignKey(
        'Offer',
        on_delete=models.CASCADE,
        related_name='calculated_sub_type_elements',
        verbose_name=_('Offer')
    )
    element = models.ForeignKey(
        'Element',
        on_delete=models.CASCADE,
        related_name='calculated_sub_type_elements',
        verbose_name=_('Element')
    )
    sub_type_element = models.ForeignKey(
        ElementSubTypeElements,
        on_delete=models.CASCADE,
        related_name='calculated_instances',
        verbose_name=_('Sub Type Element Template')
    )
    
    # Calculated dimensions
    Dx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name=_('Dx'))
    Dy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name=_('Dy'))
    
    # Copy of configuration values (for display purposes)
    element_name = models.CharField(max_length=255, verbose_name=_('Element Name'))
    element_quantity = models.IntegerField(verbose_name=_('Element Quantity'))
    element_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Price'))
    element_discount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Discount'))
    element_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Total'))
    
    calculated_at = models.DateTimeField(auto_now=True, verbose_name=_('Calculated At'))
    
    class Meta:
        verbose_name = _('Calculated ElementSubTypeElement')
        verbose_name_plural = _('Calculated ElementSubTypeElements')
        unique_together = ('element', 'sub_type_element')
        ordering = ['element', 'sub_type_element__element_name']
    
    def __str__(self):
        return f"{self.element} - {self.element_name} (Dx={self.Dx}, Dy={self.Dy})"


class CoefficientGroup(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Coefficient Group"
        verbose_name_plural = "Coefficient Groups"

    def __str__(self):
        return self.name


class Coefficient(models.Model):
    group = models.ForeignKey(
        CoefficientGroup,
        on_delete=models.CASCADE,
        related_name="coefficients"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    value = models.PositiveSmallIntegerField(default=1)  # active = 1
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Default'),
        help_text=_('If checked, this coefficient will be automatically selected for new offers')
    )

    class Meta:
        unique_together = ("group", "code")
        verbose_name = "Coefficient"
        verbose_name_plural = "Coefficients"

    def __str__(self):
        return f"{self.group.name} – {self.name}"


class OfferCoefficientSelection(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="coefficient_selections"
    )
    group = models.ForeignKey(
        CoefficientGroup,
        on_delete=models.CASCADE
    )
    coefficient = models.ForeignKey(
        Coefficient,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("offer", "group")
        verbose_name = "Offer Coefficient Selection"
        verbose_name_plural = "Offer Coefficient Selections"

    def __str__(self):
        return f"{self.offer} → {self.coefficient}"
    