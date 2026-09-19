from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from decimal import Decimal, InvalidOperation
import json
from .models import (
    Offer,
    Element,
    OfferElement,
    ElementSubType,
    CalculatedElementSubTypeElement,
    CoefficientGroup,
    Coefficient,
    OfferCoefficientSelection,
    UserCoefficientPreference,
    Material,
)
from .forms import OfferForm, ElementFormSet, ElementForm
from .ladice_extra_fields import get_ladice_extra_fields_for_sub_type, LADICE_FIELD_NAMES


def _material_qs_for_user(user):
    """Return a Material queryset filtered by the user's material preference.

    Priority:
      1. If distributors are selected → filter by those distributors only.
      2. Else if cities are selected  → filter by distributor city.
      3. Else if country is selected  → filter by distributor country.
      4. Otherwise                    → return all materials.
    """
    qs = Material.objects.select_related('distributor').order_by('code')
    try:
        pref = user.material_preference
        dist_ids = list(pref.distributors.values_list('id', flat=True))
        if dist_ids:
            qs = qs.filter(distributor_id__in=dist_ids)
        elif pref.cities:
            qs = qs.filter(distributor__city__in=pref.cities)
        elif pref.country:
            qs = qs.filter(distributor__country=pref.country)
    except Exception:
        pass
    return qs


def _materials_json_for_user(user):
    """Serialise the user-filtered material queryset to JSON for the template."""
    qs = _material_qs_for_user(user)
    return json.dumps(list(qs.values('id', 'code', 'name', 'distributor__name')))


def _save_elements_ladice_fields(formset, request):
    """Save Ladice explicit fields from POST to Element. If value exists save it, if not leave as-is (don't overwrite)."""
    total = int(request.POST.get('elements-TOTAL_FORMS', 0))
    for i in range(total):
        if i >= len(formset.forms) or formset.forms[i].cleaned_data.get('DELETE'):
            continue
        element = formset.forms[i].instance
        update_fields = []
        for field_name in LADICE_FIELD_NAMES:
            key = f'elements-{i}-extra_{field_name}'
            val = request.POST.get(key)
            if val is not None:  # key was in POST
                if val == '':
                    setattr(element, field_name, None)
                else:
                    try:
                        setattr(element, field_name, Decimal(val))
                    except (ValueError, InvalidOperation):
                        setattr(element, field_name, None)
                update_fields.append(field_name)
        if update_fields:
            element.save(update_fields=update_fields)


def _coefficient_for_new_offer_group(user, group, posted_coefficient_id=None):
    """Resolve coefficient: POST override, then user profile preference, then global default."""
    if posted_coefficient_id:
        try:
            return Coefficient.objects.get(id=posted_coefficient_id, group=group)
        except Coefficient.DoesNotExist:
            pass
    if user and user.is_authenticated:
        pref = (
            UserCoefficientPreference.objects.filter(user=user, group=group)
            .select_related("coefficient")
            .first()
        )
        if pref:
            return pref.coefficient
    return group.coefficients.filter(is_default=True).first()


def _set_default_coefficients_for_offer(offer: Offer):
    """Apply user profile defaults, then global is_default, for each group."""
    user = offer.created_by
    groups = CoefficientGroup.objects.prefetch_related("coefficients").all()
    for group in groups:
        coeff = _coefficient_for_new_offer_group(user, group)
        if coeff:
            OfferCoefficientSelection.objects.get_or_create(
                offer=offer,
                group=group,
                defaults={"coefficient": coeff},
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


def elements_list(request):
    """Display list of all element sub types"""
    sub_types = (
        Element.objects.annotate(
            sub_type_elements_count=Count('sub_type_elements', distinct=True),
            used_in_offers_count=Count('offer_elements', distinct=True),
        )
        .order_by('type', 'code')
    )

    page = request.GET.get('page', 1)
    paginator = Paginator(sub_types, 10)

    try:
        sub_types_page = paginator.page(page)
    except PageNotAnInteger:
        sub_types_page = paginator.page(1)
    except EmptyPage:
        sub_types_page = paginator.page(paginator.num_pages)

    context = {
        'segment': 'elements',
        'parent': 'apps',
        'sub_types': sub_types_page,
        'total_sub_types': sub_types.count(),
    }

    return render(request, 'pages/apps/elements.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def element_subtype_create(request):
    """Create a new element sub type"""
    if request.method == 'POST':
        form = ElementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Element created successfully!')
            return redirect('offers:elements_list')
    else:
        form = ElementForm()

    context = {
        'segment': 'elements',
        'parent': 'apps',
        'form': form,
    }

    return render(request, 'pages/apps/element_form.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def element_subtype_delete(request, pk):
    """Delete an element sub type"""
    sub_type = get_object_or_404(Element, pk=pk)
    used_in_offers_count = sub_type.offer_elements.count()

    if request.method == 'POST':
        if used_in_offers_count:
            messages.error(
                request,
                'This element cannot be deleted because it is used in existing offers.',
            )
            return redirect('offers:element_delete', pk=pk)
        try:
            sub_type.delete()
        except ProtectedError:
            messages.error(
                request,
                'This element cannot be deleted because it is used in existing offers.',
            )
            return redirect('offers:elements_list')
        messages.success(request, 'Element deleted successfully!')
        return redirect('offers:elements_list')

    context = {
        'segment': 'elements',
        'parent': 'apps',
        'sub_type': sub_type,
        'used_in_offers_count': used_in_offers_count,
    }

    return render(request, 'pages/apps/element_confirm_delete.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def offer_create(request):
    """Create a new offer with elements"""
    material_qs = _material_qs_for_user(request.user)
    if request.method == 'POST':
        form = OfferForm(request.POST)
        formset = ElementFormSet(request.POST, form_kwargs={'material_qs': material_qs})

        if form.is_valid() and formset.is_valid():
            offer = form.save(commit=False)
            offer.created_by = request.user
            offer.save()
            formset.instance = offer
            formset.save()
            _save_elements_ladice_fields(formset, request)

            groups = CoefficientGroup.objects.prefetch_related("coefficients").all()
            for group in groups:
                posted = request.POST.get(f"coefficient_group_{group.id}")
                coefficient = _coefficient_for_new_offer_group(
                    request.user, group, posted_coefficient_id=posted or None
                )
                if coefficient:
                    OfferCoefficientSelection.objects.update_or_create(
                        offer=offer,
                        group=group,
                        defaults={"coefficient": coefficient},
                    )
            
            # Trigger calculation after saving offer and coefficients
            offer.recalculate_all_element_dimensions()
            
            messages.success(request, 'Offer created successfully!')
            return redirect('offers:detail', pk=offer.pk)
    else:
        form = OfferForm()
        formset = ElementFormSet(form_kwargs={'material_qs': material_qs})

    context = {
        'segment': 'offers',
        'parent': 'apps',
        'form': form,
        'formset': formset,
        'action': 'Create',
        'current_offer_id': None,
        'offer': None,
        'materials_json': _materials_json_for_user(request.user),
    }

    return render(request, 'pages/apps/offer_form.html', context)


@login_required(login_url='/accounts/login/basic-login/')
def offer_edit(request, pk):
    """Edit an existing offer with elements"""
    offer = get_object_or_404(Offer, pk=pk)
    material_qs = _material_qs_for_user(request.user)

    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        formset = ElementFormSet(request.POST, instance=offer, form_kwargs={'material_qs': material_qs})
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            _save_elements_ladice_fields(formset, request)

            # Handle coefficient selection from form
            groups = CoefficientGroup.objects.prefetch_related('coefficients').all()
            for group in groups:
                coefficient_id = request.POST.get(f'coefficient_group_{group.id}')
                if coefficient_id:
                    try:
                        coefficient = Coefficient.objects.get(id=coefficient_id, group=group)
                        OfferCoefficientSelection.objects.update_or_create(
                            offer=offer,
                            group=group,
                            defaults={'coefficient': coefficient}
                        )
                    except Coefficient.DoesNotExist:
                        pass
            
            # Trigger calculation after saving offer and coefficients
            offer.recalculate_all_element_dimensions()
            
            messages.success(request, 'Offer updated successfully!')
            return redirect('offers:detail', pk=offer.pk)
    else:
        form = OfferForm(instance=offer)
        formset = ElementFormSet(instance=offer, form_kwargs={'material_qs': material_qs})

    context = {
        'segment': 'offers',
        'parent': 'apps',
        'form': form,
        'formset': formset,
        'offer': offer,
        'action': 'Edit',
        'current_offer_id': pk,
        'materials_json': _materials_json_for_user(request.user),
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
        subtypes = Element.objects.filter(type=element_type).values('id', 'code', 'name', 'Dx', 'Dy', 'Dz')
        return JsonResponse(list(subtypes), safe=False)
    return JsonResponse([], safe=False)


def get_subtype_extra_fields(request):
    """AJAX endpoint to get extra fields schema for a sub-type (e.g. for Ladice)."""
    sub_type_id = request.GET.get('sub_type_id')
    if not sub_type_id:
        return JsonResponse({'extra_fields': []})
    try:
        sub_type = Element.objects.get(pk=sub_type_id)
        # For Ladice, use the defined mapping (LADICE 1–4); otherwise use DB schema
        if sub_type.type == 'ladice':
            schema = get_ladice_extra_fields_for_sub_type(sub_type)
        else:
            schema = sub_type.extra_fields_schema or []
        return JsonResponse({'extra_fields': schema})
    except (Element.DoesNotExist, ValueError):
        return JsonResponse({'extra_fields': []})


def get_subtype_elements(request):
    """
    AJAX endpoint to get ElementSubTypeElements based on ElementSubType ID.
    Returns configuration templates (ElementSubTypeElements).
    If Element ID is provided, also returns calculated results from CalculatedElementSubTypeElement.
    """
    sub_type_id = request.GET.get('sub_type_id')
    element_id = request.GET.get('element_id')
    
    if sub_type_id:
        try:
            from .models import CalculatedElementSubTypeElement
            
            # Get configuration templates
            templates = ElementSubType.objects.filter(element_sub_type_id=sub_type_id)
            
            elements_data = []
            for template in templates:
                element_data = {
                    'id': template.id,
                    'element_name': template.element_name,
                    'element_quantity': template.element_quantity,
                    'formula_code': template.formula_code,
                }
                
                # If element_id is provided, try to get calculated values
                if element_id:
                    try:
                        calculated = CalculatedElementSubTypeElement.objects.get(
                            element_id=element_id,
                            sub_type_element=template
                        )
                        element_data['Dx'] = float(calculated.Dx) if calculated.Dx else None
                        element_data['Dy'] = float(calculated.Dy) if calculated.Dy else None
                        element_data['Dz'] = None  # Dz is not calculated
                    except CalculatedElementSubTypeElement.DoesNotExist:
                        element_data['Dx'] = None
                        element_data['Dy'] = None
                        element_data['Dz'] = None
                else:
                    element_data['Dx'] = None
                    element_data['Dy'] = None
                    element_data['Dz'] = None
                
                elements_data.append(element_data)
            
            return JsonResponse(elements_data, safe=False)
        except (ValueError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_subtype_elements: {e}")
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
                
                # Note: Calculation is no longer triggered on coefficient change
                # It will be triggered when the form is saved
            
            return JsonResponse({
                'success': True,
                'coefficient_id': coefficient.id,
                'coefficient_name': coefficient.name,
                'group_id': group.id,
                'offer_id': offer.id,
                'message': 'Coefficient updated. Calculations will run when you save the offer.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def auto_save_offer(request):
    """Auto-save offer on first element add so coefficient selection works."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            title = request.POST.get('title', 'New Offer')
            offer = Offer.objects.create(title=title, created_by=request.user, is_active=True)
            _set_default_coefficients_for_offer(offer)
            return JsonResponse({'success': True, 'offer_id': offer.id})
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error auto-saving offer: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def update_element_dimensions(request):
    """Update Element dimensions (Dx, Dy, Dz) via AJAX."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            element_id = request.POST.get('element_id')
            dx = request.POST.get('Dx')
            dy = request.POST.get('Dy')
            dz = request.POST.get('Dz')

            if not element_id:
                return JsonResponse({'success': False, 'error': 'Missing element_id'}, status=400)

            element = get_object_or_404(OfferElement, id=element_id)

            for attr, val in (('Dx', dx), ('Dy', dy), ('Dz', dz)):
                if val == '':
                    setattr(element, attr, None)
                elif val is not None:
                    try:
                        setattr(element, attr, Decimal(val))
                    except (ValueError, InvalidOperation):
                        return JsonResponse({'success': False, 'error': f'Invalid {attr} value: {val}'}, status=400)

            element.save(update_fields=['Dx', 'Dy', 'Dz'])
            return JsonResponse({
                'success': True,
                'element_id': element.id,
                'Dx': float(element.Dx) if element.Dx else None,
                'Dy': float(element.Dy) if element.Dy else None,
                'Dz': float(element.Dz) if element.Dz else None,
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating element dimensions: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def recalculate_dimensions(request, pk):
    """Manually trigger dimension recalculation for an offer."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            offer = get_object_or_404(Offer, pk=pk)
            result = offer.recalculate_all_element_dimensions()
            return JsonResponse({'success': True, 'message': 'Dimensions recalculated successfully', 'stats': result})
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error recalculating dimensions: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
