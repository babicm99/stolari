from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.db import transaction
from .models import Offer, Element, ElementSubType, ElementSubTypeElements, CoefficientGroup, Coefficient, OfferCoefficientSelection
from .forms import OfferForm, ElementFormSet


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
        subtypes = ElementSubType.objects.filter(type=element_type).values('id', 'code', 'name')
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
            
            return JsonResponse({
                'success': True,
                'coefficient_id': coefficient.id,
                'coefficient_name': coefficient.name,
                'group_id': group.id,
                'offer_id': offer.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


