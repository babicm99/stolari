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
        Recalculate Dx, Dy, Dz for all ElementSubTypeElements related to this offer's elements.
        Uses Element.Dx, Dy, Dz (user input) as base dimensions.
        This should be called when coefficients change or Element dimensions change.
        
        Important: Each ElementSubTypeElements is recalculated for each Element that uses its sub_type.
        This ensures that if multiple Elements share the same sub_type, each Element's table shows
        calculations based on that Element's dimensions.
        
        Works even if no coefficients are selected (uses default values of 0).
        
        Returns:
            dict: Statistics about the recalculation (count of updated elements, errors, etc.)
        """
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
        
        # Track which ElementSubTypeElements have been recalculated for which Elements
        # This prevents duplicate calculations when multiple Elements share the same sub_type
        # Format: {(element_id, sub_type_element_id): calculated}
        calculated_pairs = {}
        
        # For each Element, recalculate all related ElementSubTypeElements
        for element in elements:
            # Get all ElementSubTypeElements for this element's sub_type
            sub_type_elements = ElementSubTypeElements.objects.filter(
                element_sub_type=element.sub_type
            )
            
            for sub_type_element in sub_type_elements:
                # Calculate dimensions for this specific Element + ElementSubTypeElements pair
                # Each ElementSubTypeElements should be calculated using the Element's dimensions
                if sub_type_element.calculate_dimensions(element, self):
                    calculated_pairs[(element.id, sub_type_element.id)] = True
                    updated_count += 1
                else:
                    calculated_pairs[(element.id, sub_type_element.id)] = False
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

    class Meta:
        unique_together = ('type', 'code')
        verbose_name = 'Element SubType'
        verbose_name_plural = 'Element SubTypes'

    def __str__(self):
        return f"{self.type} - {self.code}"
        

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['element_type', 'sub_type']

    def __str__(self):
        return f"{self.element_type} - {self.sub_type.code} ({self.offer.title})"

# ElementSubTypeElements is a model that will be used to store the elements of the sub type
class ElementSubTypeElements(models.Model):
    element_name = models.CharField(max_length=255, verbose_name=_('Element Name'))
    element_sub_type = models.ForeignKey(ElementSubType, on_delete=models.CASCADE, verbose_name=_('Element Sub Type'))
    element_quantity = models.IntegerField(verbose_name=_('Element Quantity'))
    element_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Price'))
    element_discount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Discount'))
    element_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Element Total'))
    
    # Formula code to identify which formula to use for this element
    # Can be element_name, a custom code, or left blank to use default formulas
    formula_code = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Formula Code'), 
                                    help_text=_('Optional: Custom formula identifier for this element. If blank, uses default formulas.'))

    Dx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    Dy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    Dz = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _('ElementSubTypeElements')
        verbose_name_plural = _('ElementSubTypeElements')

    def __str__(self):
        return self.element_name
    
    def calculate_dimensions(self, element: 'Element', offer: 'Offer'):
        """
        Calculate and update Dx, Dy, Dz based on Element dimensions and Offer coefficients.
        Works even if no coefficients are selected (uses default values of 0).
        
        Args:
            element: The Element instance with user-input Dx, Dy, Dz values
            offer: The Offer instance to use for coefficient calculations (can be new offer with no coefficients)
        
        Returns:
            bool: True if calculation was successful, False otherwise
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            from .calculations import calculate_element_dimensions
            
            logger.debug(
                f"Calculating dimensions for ElementSubTypeElements {self.id} "
                f"(formula_code={self.formula_code}) with Element {element.id if element.id else 'new'} "
                f"(Dx={element.Dx}, Dy={element.Dy}, Dz={element.Dz})"
            )
            
            dimensions = calculate_element_dimensions(
                element,
                offer,
                self
            )
            
            logger.debug(
                f"Calculated dimensions: Dx={dimensions['Dx']}, "
                f"Dy={dimensions['Dy']}, Dz={dimensions['Dz']}"
            )
            
            # Update and save dimensions
            self.Dx = dimensions['Dx']
            self.Dy = dimensions['Dy']
            self.Dz = dimensions['Dz']
            self.save(update_fields=['Dx', 'Dy', 'Dz'])
            
            logger.info(
                f"Successfully updated ElementSubTypeElements {self.id} dimensions: "
                f"Dx={self.Dx}, Dy={self.Dy}, Dz={self.Dz}"
            )
            
            return True
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(
                f"Error calculating dimensions for ElementSubTypeElements {self.id}: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return False


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
    