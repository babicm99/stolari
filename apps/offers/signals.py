"""
Django signals for automatic dimension calculations.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import OfferCoefficientSelection, Element, ElementSubTypeElements


@receiver(post_save, sender=OfferCoefficientSelection)
def recalculate_on_coefficient_change(sender, instance, created, **kwargs):
    """
    When a coefficient selection is saved/changed, recalculate dimensions
    for all ElementSubTypeElements related to that offer.
    
    Note: This signal will fire, but we also explicitly call recalculation
    in the view to ensure it happens immediately.
    """
    try:
        result = instance.offer.recalculate_all_element_dimensions()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Recalculated dimensions for offer {instance.offer.id}: {result}")
    except Exception as e:
        # Log error but don't break the save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error recalculating dimensions for offer {instance.offer.id}: {e}")


@receiver(pre_save, sender=Element)
def store_element_dimensions_before_save(sender, instance, **kwargs):
    """
    Store the old dimension values before save to detect changes.
    """
    if instance.pk:
        try:
            old_instance = Element.objects.get(pk=instance.pk)
            # Store old values in instance for comparison in post_save
            instance._old_dx = old_instance.Dx
            instance._old_dy = old_instance.Dy
            instance._old_dz = old_instance.Dz
        except Element.DoesNotExist:
            instance._old_dx = None
            instance._old_dy = None
            instance._old_dz = None
    else:
        # New instance
        instance._old_dx = None
        instance._old_dy = None
        instance._old_dz = None


@receiver(post_save, sender=Element)
def recalculate_on_element_change(sender, instance, created, **kwargs):
    """
    When an Element is added or its dimensions (Dx, Dy, Dz) are changed,
    recalculate dimensions for all ElementSubTypeElements of that sub_type.
    """
    try:
        # Check if dimensions changed (for existing elements) or if it's a new element
        dimensions_changed = False
        if created:
            dimensions_changed = True
        else:
            # Check if any dimension changed
            old_dx = getattr(instance, '_old_dx', None)
            old_dy = getattr(instance, '_old_dy', None)
            old_dz = getattr(instance, '_old_dz', None)
            
            dimensions_changed = (
                old_dx != instance.Dx or
                old_dy != instance.Dy or
                old_dz != instance.Dz
            )
        
        if dimensions_changed:
            # Recalculate all ElementSubTypeElements for this sub_type
            sub_type_elements = ElementSubTypeElements.objects.filter(
                element_sub_type=instance.sub_type
            )
            for sub_type_element in sub_type_elements:
                sub_type_element.calculate_dimensions(instance, instance.offer)
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Recalculated dimensions for {sub_type_elements.count()} "
                f"ElementSubTypeElements after Element {instance.id} change"
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error recalculating dimensions on element change: {e}")

