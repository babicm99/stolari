from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from .models import Offer, Element, ElementSubType
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


