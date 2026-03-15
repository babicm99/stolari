"""
Django signals for automatic dimension calculations.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import OfferCoefficientSelection, Element, ElementSubTypeElements


# Disabled: Calculation is now only triggered on Save Offer button
# @receiver(post_save, sender=OfferCoefficientSelection)
# def recalculate_on_coefficient_change(sender, instance, created, **kwargs):
#     """
#     When a coefficient selection is saved/changed, recalculate dimensions
#     for all ElementSubTypeElements related to that offer.
#     
#     Note: This signal will fire, but we also explicitly call recalculation
#     in the view to ensure it happens immediately.
#     """
#     try:
#         result = instance.offer.recalculate_all_element_dimensions()
#         import logging
#         logger = logging.getLogger(__name__)
#         logger.info(f"Recalculated dimensions for offer {instance.offer.id}: {result}")
#     except Exception as e:
#         # Log error but don't break the save
#         import logging
#         logger = logging.getLogger(__name__)
#         logger.error(f"Error recalculating dimensions for offer {instance.offer.id}: {e}")


@receiver(pre_save, sender=Element)
def store_element_dimensions_before_save(sender, instance, **kwargs):
    """
    Store the old dimension values and sub_type before save to detect changes.
    """
    if instance.pk:
        try:
            old_instance = Element.objects.get(pk=instance.pk)
            # Store old values in instance for comparison in post_save
            instance._old_dx = old_instance.Dx
            instance._old_dy = old_instance.Dy
            instance._old_dz = old_instance.Dz
            instance._old_sub_type_id = old_instance.sub_type_id
        except Element.DoesNotExist:
            instance._old_dx = None
            instance._old_dy = None
            instance._old_dz = None
            instance._old_sub_type_id = None
    else:
        # New instance
        instance._old_dx = None
        instance._old_dy = None
        instance._old_dz = None
        instance._old_sub_type_id = None


# Note: Calculations are now only triggered when user clicks "Save Offer" button
# No automatic recalculation on element changes

