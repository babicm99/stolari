from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .models import Offer, Element, ElementSubType, ElementSubTypeElements, CoefficientGroup, Coefficient, OfferCoefficientSelection
from .forms import OfferForm, ElementFormSet


def _set_default_coefficients_for_offer(offer: Offer):
    """
    Set default coefficients for a new offer.
    Selects the coefficient marked as is_default=True for each group.
    """
    # Get all coefficient groups
    groups = CoefficientGroup.objects.prefetch_related('coefficients').all()
    
    for group in groups:
        # Find the default coefficient for this group
        default_coefficient = group.coefficients.filter(is_default=True).first()
        
        if default_coefficient:
            # Create selection for this default coefficient
            OfferCoefficientSelection.objects.get_or_create(
                offer=offer,
                group=group,
                defaults={'coefficient': default_coefficient}
            )


def offers_list(request):
    """Display list of all offers"""
    offers = Offer.objects.all().order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(offers, 10)  # 10 offers per page
    
    try:
        offers_page = paginator.page(page)
    except PageNotAnInteger:
        offers_page = paginator.page(1)
    except EmptyPage:
        offers_page = paginator.page(paginator.num_pages)
    
    context = {
        'segment': 'offers',
        'parent': 'apps',
        'offers': offers_page,
        'total_offers': offers.count(),
    }
    
    return render(request, 'pages/apps/offers.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def offer_create(request):
    """Create a new offer with elements"""
    if request.method == 'POST':
        form = OfferForm(request.POST)
        formset = ElementFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            offer = form.save(commit=False)
            offer.created_by = request.user
            offer.save()
            formset.instance = offer
            formset.save()
            
            # Auto-select default coefficients for new offer
            _set_default_coefficients_for_offer(offer)
            
            messages.success(request, 'Offer created successfully!')
            return redirect('offers:detail', pk=offer.pk)
    else:
        form = OfferForm()
        formset = ElementFormSet()
    
    context = {
        'segment': 'offers',
        'parent': 'apps',
        'form': form,
        'formset': formset,
        'action': 'Create',
        'current_offer_id': None,  # No offer ID for new offers initially
        'offer': None,  # No offer object for new offers
    }
    
    return render(request, 'pages/apps/offer_form.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def offer_edit(request, pk):
    """Edit an existing offer with elements"""
    offer = get_object_or_404(Offer, pk=pk)
    
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        formset = ElementFormSet(request.POST, instance=offer)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, 'Offer updated successfully!')
            return redirect('offers:detail', pk=offer.pk)
    else:
        form = OfferForm(instance=offer)
        formset = ElementFormSet(instance=offer)
    
    context = {
        'segment': 'offers',
        'parent': 'apps',
        'form': form,
        'formset': formset,
        'offer': offer,
        'action': 'Edit',
        'current_offer_id': pk,  # Pass directly to template
    }
    
    return render(request, 'pages/apps/offer_form.html', context)


def offer_detail(request, pk):
    """Display offer details with all elements"""
    offer = get_object_or_404(Offer, pk=pk)
    elements = offer.elements.all().order_by('element_type', 'sub_type')
    
    context = {
        'segment': 'offers',
        'parent': 'apps',
        'offer': offer,
        'elements': elements,
        'current_offer_id': pk,  # Pass directly to template
    }
    
    return render(request, 'pages/apps/offer_detail.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def offer_delete(request, pk):
    """Delete an offer"""
    offer = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Offer deleted successfully!')
        return redirect('offers:list')
    
    context = {
        'segment': 'offers',
        'parent': 'apps',
        'offer': offer,
    }
    
    return render(request, 'pages/apps/offer_confirm_delete.html', context)


def get_subtypes(request):
    """AJAX endpoint to get subtypes based on element type"""
    element_type = request.GET.get('element_type')
    if element_type:
        subtypes = ElementSubType.objects.filter(type=element_type).values('id', 'code', 'name', 'Dx', 'Dy', 'Dz')
        return JsonResponse(list(subtypes), safe=False)
    return JsonResponse([], safe=False)


def get_subtype_elements(request):
    """AJAX endpoint to get ElementSubTypeElements based on ElementSubType ID"""
    sub_type_id = request.GET.get('sub_type_id')
    if sub_type_id:
        try:
            elements = ElementSubTypeElements.objects.filter(element_sub_type_id=sub_type_id).values(
                'id', 'element_name', 'element_quantity', 'Dx', 'Dy', 'Dz'
            )
            return JsonResponse(list(elements), safe=False)
        except (ValueError, TypeError):
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)


@login_required(login_url='/accounts/login/basic-login/')
def update_coefficient(request):
    """Update coefficient selection via AJAX - only one coefficient per group can be selected per offer"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            offer_id = request.POST.get('offer_id')
            coefficient_id = request.POST.get('coefficient_id')
            group_id = request.POST.get('group_id')
            
            if not offer_id or not coefficient_id or not group_id:
                return JsonResponse({'success': False, 'error': 'Missing offer_id, coefficient_id or group_id'}, status=400)
            
            # Get the offer, coefficient and group
            offer = get_object_or_404(Offer, id=offer_id)
            coefficient = get_object_or_404(Coefficient, id=coefficient_id)
            group = get_object_or_404(CoefficientGroup, id=group_id)
            
            # Verify coefficient belongs to the group
            if coefficient.group != group:
                return JsonResponse({'success': False, 'error': 'Coefficient does not belong to the specified group'}, status=400)
            
            with transaction.atomic():
                # Remove any existing selection for this group and offer
                OfferCoefficientSelection.objects.filter(offer=offer, group=group).delete()
                
                # Create new selection
                selection, created = OfferCoefficientSelection.objects.get_or_create(
                    offer=offer,
                    group=group,
                    defaults={'coefficient': coefficient}
                )
                
                if not created:
                    selection.coefficient = coefficient
                    selection.save()
                
                # Explicitly trigger recalculation after coefficient change
                # This ensures ElementSubTypeElements are updated immediately
                recalculation_result = offer.recalculate_all_element_dimensions()
                
                # Get updated ElementSubTypeElements for all elements in this offer
                # This will be used to update the UI
                # Group by element_id so each Element gets its own calculated values
                updated_elements_data = {}
                for element in offer.elements.all():
                    sub_type_elements = ElementSubTypeElements.objects.filter(
                        element_sub_type=element.sub_type
                    )
                    
                    # Calculate dimensions for each ElementSubTypeElements using this specific Element
                    element_subtype_data = []
                    for sub_elem in sub_type_elements:
                        # Recalculate using this Element's dimensions
                        from .calculations import calculate_element_dimensions
                        dimensions = calculate_element_dimensions(element, offer, sub_elem)
                        
                        elem_data = {
                            'id': sub_elem.id,
                            'element_name': sub_elem.element_name,
                            'element_sub_type_id': sub_elem.element_sub_type_id,
                            'Dx': float(dimensions['Dx']) if dimensions['Dx'] is not None else None,
                            'Dy': float(dimensions['Dy']) if dimensions['Dy'] is not None else None,
                            'Dz': float(dimensions['Dz']) if dimensions['Dz'] is not None else None,
                        }
                        element_subtype_data.append(elem_data)
                    
                    # Store by element_id so frontend can update the correct table
                    updated_elements_data[element.id] = element_subtype_data
                
                # Log the recalculation
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Coefficient updated for offer {offer.id}: "
                    f"Updated {recalculation_result['updated']} elements, "
                    f"{recalculation_result['errors']} errors"
                )
            
            return JsonResponse({
                'success': True,
                'coefficient_id': coefficient.id,
                'coefficient_name': coefficient.name,
                'group_id': group.id,
                'offer_id': offer.id,
                'message': 'Coefficient updated and dimensions recalculated',
                'recalculation': {
                    'updated_elements': recalculation_result['updated'],
                    'errors': recalculation_result['errors'],
                    'total': recalculation_result['total']
                },
                'updated_subtype_elements_by_element': updated_elements_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def auto_save_offer(request):
    """
    Auto-save offer when creating new offer. This enables coefficient selection.
    Called when first element is added to a new offer.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', 'New Offer')
            
            # Create a new offer
            offer = Offer.objects.create(
                title=title,
                created_by=request.user,
                is_active=True
            )
            
            # Auto-select default coefficients
            _set_default_coefficients_for_offer(offer)
            
            return JsonResponse({
                'success': True,
                'offer_id': offer.id,
                'message': 'Offer auto-saved successfully'
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error auto-saving offer: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def update_element_dimensions(request):
    """
    Update Element dimensions (Dx, Dy, Dz) via AJAX and trigger recalculation.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            element_id = request.POST.get('element_id')
            dx = request.POST.get('Dx')
            dy = request.POST.get('Dy')
            dz = request.POST.get('Dz')
            
            if not element_id:
                return JsonResponse({'success': False, 'error': 'Missing element_id'}, status=400)
            
            # Get the element
            element = get_object_or_404(Element, id=element_id)
            
            # Update dimensions (convert empty strings to None)
            if dx == '':
                element.Dx = None
            elif dx is not None:
                try:
                    element.Dx = Decimal(dx)
                except (ValueError, InvalidOperation):
                    return JsonResponse({'success': False, 'error': f'Invalid Dx value: {dx}'}, status=400)
            
            if dy == '':
                element.Dy = None
            elif dy is not None:
                try:
                    element.Dy = Decimal(dy)
                except (ValueError, InvalidOperation):
                    return JsonResponse({'success': False, 'error': f'Invalid Dy value: {dy}'}, status=400)
            
            if dz == '':
                element.Dz = None
            elif dz is not None:
                try:
                    element.Dz = Decimal(dz)
                except (ValueError, InvalidOperation):
                    return JsonResponse({'success': False, 'error': f'Invalid Dz value: {dz}'}, status=400)
            
            # Save the element (this will trigger the signal which recalculates ElementSubTypeElements)
            element.save(update_fields=['Dx', 'Dy', 'Dz'])
            
            # Get updated ElementSubTypeElements for this element's sub_type
            updated_elements_data = []
            sub_type_elements = ElementSubTypeElements.objects.filter(
                element_sub_type=element.sub_type
            ).values('id', 'element_name', 'Dx', 'Dy', 'Dz', 'element_sub_type_id')
            
            for sub_elem in sub_type_elements:
                # Convert Decimal to float for JSON serialization
                elem_data = dict(sub_elem)
                elem_data['Dx'] = float(sub_elem['Dx']) if sub_elem['Dx'] is not None else None
                elem_data['Dy'] = float(sub_elem['Dy']) if sub_elem['Dy'] is not None else None
                elem_data['Dz'] = float(sub_elem['Dz']) if sub_elem['Dz'] is not None else None
                updated_elements_data.append(elem_data)
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Element {element.id} dimensions updated: Dx={element.Dx}, Dy={element.Dy}, Dz={element.Dz}"
            )
            
            return JsonResponse({
                'success': True,
                'element_id': element.id,
                'Dx': float(element.Dx) if element.Dx else None,
                'Dy': float(element.Dy) if element.Dy else None,
                'Dz': float(element.Dz) if element.Dz else None,
                'updated_subtype_elements': updated_elements_data,
                'message': 'Element dimensions updated and recalculated'
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating element dimensions: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def recalculate_dimensions(request, pk):
    """
    Manually trigger recalculation of dimensions for all ElementSubTypeElements
    in an offer. Useful when formulas change or for bulk updates.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            offer = get_object_or_404(Offer, pk=pk)
            result = offer.recalculate_all_element_dimensions()
            
            return JsonResponse({
                'success': True,
                'message': 'Dimensions recalculated successfully',
                'stats': result
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error recalculating dimensions: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


