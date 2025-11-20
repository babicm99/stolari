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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['element_type', 'sub_type']

    def __str__(self):
        return f"{self.element_type} - {self.sub_type.code} ({self.offer.title})"