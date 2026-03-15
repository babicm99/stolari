# Testing Dimension Calculations

## How to Verify Calculations Are Working

### 1. Check Database After Coefficient Change

When you change a coefficient for an offer, the `ElementSubTypeElements` table should be automatically updated.

**Steps to test:**
1. Open an offer detail page
2. Note the current Dx, Dy, Dz values for some ElementSubTypeElements
3. Change a coefficient in the configurator
4. Check the database - the values should be updated

**SQL Query to check:**
```sql
SELECT 
    ese.id,
    ese.element_name,
    ese.Dx,
    ese.Dy,
    ese.Dz,
    est.code as sub_type_code,
    o.title as offer_title
FROM offers_elementsubtypeelements ese
JOIN offers_elementsubtype est ON ese.element_sub_type_id = est.id
JOIN offers_element e ON e.sub_type_id = est.id
JOIN offers_offer o ON e.offer_id = o.id
WHERE o.id = <your_offer_id>
ORDER BY ese.id;
```

### 2. Test via Django Shell

```python
from apps.offers.models import Offer, ElementSubTypeElements, OfferCoefficientSelection

# Get an offer
offer = Offer.objects.get(id=1)

# Check current dimensions
elements = ElementSubTypeElements.objects.filter(
    element_sub_type__in=offer.elements.values_list('sub_type', flat=True)
)
print("Before coefficient change:")
for e in elements[:5]:
    print(f"{e.element_name}: Dx={e.Dx}, Dy={e.Dy}, Dz={e.Dz}")

# Change a coefficient
selection = OfferCoefficientSelection.objects.filter(offer=offer).first()
if selection:
    # Get a different coefficient from the same group
    new_coeff = selection.group.coefficients.exclude(id=selection.coefficient.id).first()
    if new_coeff:
        selection.coefficient = new_coeff
        selection.save()
        
        # Trigger recalculation
        offer.recalculate_all_element_dimensions()
        
        # Refresh from database
        elements = ElementSubTypeElements.objects.filter(
            element_sub_type__in=offer.elements.values_list('sub_type', flat=True)
        )
        print("\nAfter coefficient change:")
        for e in elements[:5]:
            print(f"{e.element_name}: Dx={e.Dx}, Dy={e.Dy}, Dz={e.Dz}")
```

### 3. Test via API

```javascript
// Change a coefficient
fetch('/offers/ajax/update-coefficient/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken
    },
    body: 'offer_id=1&coefficient_id=2&group_id=1'
})
.then(response => response.json())
.then(data => {
    console.log('Coefficient updated:', data);
    console.log('Recalculation stats:', data.recalculation);
});
```

### 4. Manual Recalculation

```javascript
// Manually trigger recalculation
fetch('/offers/ajax/recalculate-dimensions/1/', {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken
    }
})
.then(response => response.json())
.then(data => {
    console.log('Recalculation result:', data);
});
```

### 5. Check Logs

The system logs recalculation activities. Check your Django logs for messages like:
```
INFO: Recalculated dimensions for offer 1: {'updated': 5, 'errors': 0, 'total': 5}
```

### 6. Verify Signal is Working

The signal should fire automatically. To verify:

```python
from apps.offers.models import OfferCoefficientSelection, Offer, Coefficient

# Get an offer and coefficient
offer = Offer.objects.get(id=1)
coeff = Coefficient.objects.first()

# Create/update selection - this should trigger the signal
selection, created = OfferCoefficientSelection.objects.get_or_create(
    offer=offer,
    group=coeff.group,
    defaults={'coefficient': coeff}
)

# The signal should have automatically recalculated dimensions
# Check the database to verify
```

## Troubleshooting

### If dimensions are not updating:

1. **Check if formulas are defined:**
   ```python
   from apps.offers.calculations import calculator
   print(calculator.formulas)
   ```

2. **Check if coefficients are selected:**
   ```python
   offer = Offer.objects.get(id=1)
   selections = OfferCoefficientSelection.objects.filter(offer=offer)
   for sel in selections:
       print(f"{sel.group.code}: {sel.coefficient.code}")
   ```

3. **Check if elements exist:**
   ```python
   offer = Offer.objects.get(id=1)
   elements = offer.elements.all()
   print(f"Offer has {elements.count()} elements")
   ```

4. **Check if ElementSubTypeElements exist:**
   ```python
   from apps.offers.models import ElementSubTypeElements
   sub_types = offer.elements.values_list('sub_type', flat=True).distinct()
   elements = ElementSubTypeElements.objects.filter(element_sub_type__in=sub_types)
   print(f"Found {elements.count()} ElementSubTypeElements")
   ```

5. **Test calculation directly:**
   ```python
   from apps.offers.calculations import calculate_element_dimensions
   from apps.offers.models import ElementSubType, ElementSubTypeElements
   
   sub_type = ElementSubType.objects.first()
   element = ElementSubTypeElements.objects.filter(element_sub_type=sub_type).first()
   offer = Offer.objects.get(id=1)
   
   dimensions = calculate_element_dimensions(sub_type, offer, element)
   print(f"Calculated dimensions: {dimensions}")
   ```

## Expected Behavior

1. **When coefficient changes:**
   - `OfferCoefficientSelection` is updated
   - Signal fires → `recalculate_on_coefficient_change`
   - View explicitly calls `recalculate_all_element_dimensions()`
   - All `ElementSubTypeElements` for that offer are recalculated
   - Database is updated with new Dx, Dy, Dz values

2. **When element is added:**
   - `Element` is saved
   - Signal fires → `recalculate_on_element_add`
   - `ElementSubTypeElements` for that sub_type are recalculated
   - Database is updated

3. **Manual recalculation:**
   - Call `offer.recalculate_all_element_dimensions()`
   - All related `ElementSubTypeElements` are recalculated
   - Database is updated






