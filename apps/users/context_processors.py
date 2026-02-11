from apps.offers.models import CoefficientGroup, OfferCoefficientSelection, Offer


def coefficient_groups(request):
    """Context processor to make coefficient groups available in all templates - based on current offer"""
    context = {
        'coefficient_groups': [],
        'current_offer_id': None
    }
    
    # Try to get offer_id from URL if we're on an offer page
    offer_id = None
    
    # Check if we're on an offer detail, edit, or create page by looking at the path
    path = request.path
    if '/offers/detail/' in path or '/offers/edit/' in path:
        try:
            # Extract offer ID from URL (e.g., /offers/detail/123/ or /offers/edit/123/)
            import re
            match = re.search(r'/offers/(?:detail|edit)/(\d+)', path)
            if match:
                offer_id = int(match.group(1))
        except (ValueError, AttributeError):
            pass
    # Note: /offers/create/ doesn't have an offer_id, so it will show default coefficients
    
    context['current_offer_id'] = offer_id
    
    # Get all groups with their coefficients (always, even for new offers)
    groups = CoefficientGroup.objects.prefetch_related('coefficients').all()
    
    if offer_id:
        try:
            offer = Offer.objects.get(id=offer_id)
            # Get offer's current selections
            offer_selections = {
                sel.group_id: sel.coefficient_id 
                for sel in OfferCoefficientSelection.objects.filter(offer=offer).select_related('coefficient')
            }
            
            # Build context with groups, coefficients, and offer selections
            context['coefficient_groups'] = [
                {
                    'id': group.id,
                    'name': group.name,
                    'code': group.code,
                    'coefficients': [
                        {
                            'id': coeff.id,
                            'name': coeff.name,
                            'code': coeff.code,
                            'value': coeff.value,
                            'selected': offer_selections.get(group.id) == coeff.id,
                            'is_default': coeff.is_default
                        }
                        for coeff in group.coefficients.all()
                    ]
                }
                for group in groups
            ]
        except (Offer.DoesNotExist, ValueError, TypeError):
            # If offer doesn't exist, show default coefficients as selected
            context['coefficient_groups'] = [
                {
                    'id': group.id,
                    'name': group.name,
                    'code': group.code,
                    'coefficients': [
                        {
                            'id': coeff.id,
                            'name': coeff.name,
                            'code': coeff.code,
                            'value': coeff.value,
                            'selected': coeff.is_default,  # Show default as selected for new offers
                            'is_default': coeff.is_default
                        }
                        for coeff in group.coefficients.all()
                    ]
                }
                for group in groups
            ]
    else:
        # For new offers (no offer_id), show default coefficients as selected
        context['coefficient_groups'] = [
            {
                'id': group.id,
                'name': group.name,
                'code': group.code,
                'coefficients': [
                    {
                        'id': coeff.id,
                        'name': coeff.name,
                        'code': coeff.code,
                        'value': coeff.value,
                        'selected': coeff.is_default,  # Show default as selected for new offers
                        'is_default': coeff.is_default
                    }
                    for coeff in group.coefficients.all()
                ]
            }
            for group in groups
        ]
    
    return context

