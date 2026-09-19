import re

from apps.offers.models import (
    CoefficientGroup,
    OfferCoefficientSelection,
    Offer,
    UserCoefficientPreference,
    Distributor,
    UserMaterialPreference,
)


def _user_pref_coefficient_ids(user):
    if not user.is_authenticated:
        return {}
    return {
        p.group_id: p.coefficient_id
        for p in UserCoefficientPreference.objects.filter(user=user).only(
            "group_id", "coefficient_id"
        )
    }


def _selected_coefficient_id_for_group(group, user_pref_by_group):
    cid = user_pref_by_group.get(group.id)
    if cid is not None:
        return cid
    default_c = group.coefficients.filter(is_default=True).first()
    return default_c.id if default_c else None


def _build_group_dicts(groups, selected_id_by_group):
    return [
        {
            "id": group.id,
            "name": group.name,
            "code": group.code,
            "coefficients": [
                {
                    "id": coeff.id,
                    "name": coeff.name,
                    "code": coeff.code,
                    "value": coeff.value,
                    "selected": selected_id_by_group.get(group.id) == coeff.id,
                    "is_default": coeff.is_default,
                }
                for coeff in group.coefficients.all()
            ],
        }
        for group in groups
    ]


def coefficient_groups(request):
    """
    - user_coefficient_groups: profile defaults for the configurator sidebar (always user prefs, then global default).
    - coefficient_groups: selections for the offer form — offer-specific on edit/detail URL, else same as profile defaults.
    """
    context = {
        "coefficient_groups": [],
        "user_coefficient_groups": [],
        "current_offer_id": None,
    }

    path = request.path
    offer_id = None
    if "/offers/detail/" in path or "/offers/edit/" in path:
        match = re.search(r"/offers/(?:detail|edit)/(\d+)", path)
        if match:
            try:
                offer_id = int(match.group(1))
            except (ValueError, TypeError):
                pass

    context["current_offer_id"] = offer_id

    groups = list(
        CoefficientGroup.objects.prefetch_related("coefficients").all()
    )
    user_pref_by_group = _user_pref_coefficient_ids(request.user)

    selected_for_user = {
        g.id: _selected_coefficient_id_for_group(g, user_pref_by_group) for g in groups
    }
    context["user_coefficient_groups"] = _build_group_dicts(groups, selected_for_user)

    if offer_id:
        try:
            offer = Offer.objects.get(id=offer_id)
            offer_selections = {
                sel.group_id: sel.coefficient_id
                for sel in OfferCoefficientSelection.objects.filter(
                    offer=offer
                ).select_related("coefficient")
            }
            context["coefficient_groups"] = _build_group_dicts(
                groups, offer_selections
            )
        except (Offer.DoesNotExist, ValueError, TypeError):
            context["coefficient_groups"] = _build_group_dicts(
                groups, selected_for_user
            )
    else:
        context["coefficient_groups"] = _build_group_dicts(
            groups, selected_for_user
        )

    return context


def material_preference(request):
    """
    Provides material filter options + the user's saved preference to every page.
    Used by the configurator sidebar.
    """
    ctx = {
        'material_countries': [],
        'user_material_preference': {'country': '', 'cities': [], 'distributor_ids': []},
    }
    if not request.user.is_authenticated:
        return ctx

    # All distinct countries from distributors that have materials
    ctx['material_countries'] = sorted(
        Distributor.objects.filter(materials__isnull=False).exclude(country='')
        .values_list('country', flat=True).distinct()
    )

    try:
        pref = request.user.material_preference
        ctx['user_material_preference'] = {
            'country': pref.country,
            'cities': pref.cities,
            'distributor_ids': list(pref.distributors.values_list('id', flat=True)),
        }
    except UserMaterialPreference.DoesNotExist:
        pass

    return ctx
