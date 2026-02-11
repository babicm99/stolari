# Dimension Calculation System

This system automatically calculates `Dx`, `Dy`, `Dz` dimensions for `ElementSubTypeElements` based on:
- **Element dimensions (Dx, Dy, Dz)** - user input from the form
- **Selected coefficients** for the `Offer`
- **Per-ElementSubTypeElements formulas** (optional, identified by `formula_code`)

## Architecture

### 1. Calculation Service (`calculations.py`)
- **`DimensionCalculator`**: Main service class that handles formula execution
- **`calculate_element_dimensions()`**: Convenience function for easy usage
- **Formula Registry**: 
  - Default formulas per element type and coefficient group
  - Per-ElementSubTypeElements formulas (identified by `formula_code`)

### 2. Model Methods
- **`ElementSubTypeElements.calculate_dimensions(element, offer)`**: Calculate and save dimensions for a single element
- **`Offer.recalculate_all_element_dimensions()`**: Recalculate all elements for an offer

### 3. Django Signals (`signals.py`)
- **Auto-recalculation**: Automatically recalculates when:
  - Coefficient selections change
  - Element dimensions (Dx, Dy, Dz) change
  - New elements are added to an offer

### 4. API Endpoint
- **`/offers/ajax/recalculate-dimensions/<offer_id>/`**: Manually trigger recalculation via AJAX

## Usage

### Automatic Calculation
Dimensions are automatically calculated when:
1. A coefficient is selected/changed for an offer
2. Element dimensions (Dx, Dy, Dz) are changed in the form
3. An element is added to an offer

### Manual Calculation

```python
from apps.offers.models import Offer, Element, ElementSubTypeElements
from apps.offers.calculations import calculate_element_dimensions

# Calculate for a single ElementSubTypeElements
element = Element.objects.get(id=1)  # Element with user-input Dx, Dy, Dz
offer = Offer.objects.get(id=1)
sub_type_element = ElementSubTypeElements.objects.get(id=1)

# Method 1: Use the model method
sub_type_element.calculate_dimensions(element, offer)

# Method 2: Use the calculation function directly
dimensions = calculate_element_dimensions(element, offer, sub_type_element)
sub_type_element.Dx = dimensions['Dx']
sub_type_element.Dy = dimensions['Dy']
sub_type_element.Dz = dimensions['Dz']
sub_type_element.save()

# Recalculate all elements for an offer
offer = Offer.objects.get(id=1)
offer.recalculate_all_element_dimensions()
```

### Via API
```javascript
fetch('/offers/ajax/recalculate-dimensions/123/', {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken
    }
})
```

## Defining Custom Formulas

### Method 1: Per-ElementSubTypeElements Formulas (Recommended)

Each `ElementSubTypeElements` can have its own formula by setting the `formula_code` field.

```python
from apps.offers.calculations import calculator
from decimal import Decimal
from typing import Dict

def custom_formula_for_specific_element(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],  # All coefficients
    element: 'Element',
    element_sub_type_element: 'ElementSubTypeElements'
) -> Dict[str, Decimal]:
    """
    Custom formula for a specific ElementSubTypeElements.
    This formula receives ALL coefficient selections, allowing complex logic.
    """
    # Access all coefficients
    ceiling_coeff = coefficient_selections.get('ceiling')
    floor_coeff = coefficient_selections.get('floor')
    
    # Access element properties
    element_dx = element.Dx or Decimal('0')
    
    # Your custom calculation
    result_dx = base_dx * Decimal('1.2')
    result_dy = base_dy * Decimal('1.1')
    result_dz = base_dz * Decimal('1.0')
    
    if ceiling_coeff:
        result_dx *= Decimal(ceiling_coeff.value) / Decimal('100')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }

# Register the formula with a unique code
calculator.register_element_formula('CUSTOM_FORMULA_1', custom_formula_for_specific_element)

# Then set formula_code on the ElementSubTypeElements
element = ElementSubTypeElements.objects.get(id=1)
element.formula_code = 'CUSTOM_FORMULA_1'
element.save()
```

### Method 2: Default Formulas (Per Element Type and Coefficient Group)

Edit the default formula functions in `calculations.py`:

```python
def _formula_ceiling(
    self,
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient: 'Coefficient',
    current_result: Dict[str, Decimal],
    element: 'Element',
    element_sub_type_element: Optional['ElementSubTypeElements']
) -> Dict[str, Decimal]:
    """
    Formula for ceiling coefficient.
    """
    if coefficient.code == "KOEF.UKLOP.PLAFON":
        multiplier = Decimal('1.2')
    elif coefficient.code == "KOEF.NAKL.PLAFON":
        multiplier = Decimal('0.8')
    else:
        multiplier = Decimal(coefficient.value) / Decimal('100')
    
    return {
        'Dx': current_result['Dx'] * multiplier,
        'Dy': current_result['Dy'] * multiplier,
        'Dz': current_result['Dz'] * multiplier,
    }
```

### Method 3: Register Default Formulas Programmatically

```python
from apps.offers.calculations import calculator

def my_custom_default_formula(
    base_dx, base_dy, base_dz, 
    coefficient, 
    current_result, 
    element, 
    element_sub_type_element
):
    # Your formula logic
    return {
        'Dx': current_result['Dx'] * Decimal('1.5'),
        'Dy': current_result['Dy'] * Decimal('1.5'),
        'Dz': current_result['Dz'] * Decimal('1.5'),
    }

# Register for specific element type and coefficient group
calculator.register_default_formula('donji_elementi', 'ceiling', my_custom_default_formula)
```

## Formula Function Signatures

### Per-ElementSubTypeElements Formula Signature

```python
def element_formula(
    base_dx: Decimal,                    # Dx from Element (user input)
    base_dy: Decimal,                    # Dy from Element (user input)
    base_dz: Decimal,                    # Dz from Element (user input)
    coefficient_selections: Dict[str, 'Coefficient'],  # ALL coefficient selections
    element: Element,                   # The Element instance with user input
    element_sub_type_element: ElementSubTypeElements  # The ElementSubTypeElements instance
) -> Dict[str, Decimal]:
    """
    Returns a dictionary with 'Dx', 'Dy', 'Dz' as Decimal values.
    """
    return {
        'Dx': Decimal('...'),
        'Dy': Decimal('...'),
        'Dz': Decimal('...'),
    }
```

### Default Formula Signature (Per Coefficient Group)

```python
def default_formula(
    base_dx: Decimal,                    # Dx from Element (user input)
    base_dy: Decimal,                    # Dy from Element (user input)
    base_dz: Decimal,                    # Dz from Element (user input)
    coefficient: 'Coefficient',          # Selected coefficient for this group
    current_result: Dict[str, Decimal],  # Current calculated values (may have been modified by previous formulas)
    element: Element,                   # The Element instance
    element_sub_type_element: Optional[ElementSubTypeElements]  # The ElementSubTypeElements instance (if available)
) -> Dict[str, Decimal]:
    """
    Returns a dictionary with 'Dx', 'Dy', 'Dz' as Decimal values.
    """
    return {
        'Dx': Decimal('...'),
        'Dy': Decimal('...'),
        'Dz': Decimal('...'),
    }
```

## Formula Execution Order

1. **Per-ElementSubTypeElements formulas** (if `formula_code` is set) take precedence
2. If no custom formula, **default formulas** are applied sequentially based on coefficient groups
3. Each default formula receives the result from the previous formula, allowing for chained calculations

## Example: Complex Per-Element Formula

```python
def complex_element_formula(
    base_dx, base_dy, base_dz,
    coefficient_selections,
    element,
    element_sub_type_element
):
    """
    Example: Complex calculation using multiple coefficients and element properties
    """
    # Access all coefficients
    ceiling = coefficient_selections.get('ceiling')
    floor = coefficient_selections.get('floor')
    
    # Access element properties
    element_quantity = element.quantity
    element_dx = element.Dx or Decimal('0')
    
    # Complex calculation
    result_dx = base_dx
    result_dy = base_dy
    result_dz = base_dz
    
    if ceiling:
        result_dx += Decimal(ceiling.value) * Decimal('0.1')
    
    if floor:
        result_dy *= Decimal(floor.value) / Decimal('100')
    
    # Adjust based on quantity
    if element_quantity > 1:
        result_dz *= Decimal(str(element_quantity)) * Decimal('0.9')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }

# Register
calculator.register_element_formula('COMPLEX_1', complex_element_formula)
```

## Testing Formulas

You can test formulas in Django shell:

```python
from apps.offers.models import Offer, Element, ElementSubTypeElements
from apps.offers.calculations import calculate_element_dimensions

# Get test data
offer = Offer.objects.get(id=1)
element = Element.objects.get(id=1)  # Element with user-input Dx, Dy, Dz
sub_type_element = ElementSubTypeElements.objects.get(id=1)

# Calculate
dimensions = calculate_element_dimensions(element, offer, sub_type_element)
print(f"Dx: {dimensions['Dx']}, Dy: {dimensions['Dy']}, Dz: {dimensions['Dz']}")

# Apply to element
sub_type_element.calculate_dimensions(element, offer)
print(f"Updated: Dx={sub_type_element.Dx}, Dy={sub_type_element.Dy}, Dz={sub_type_element.Dz}")
```

## Notes

- **Base dimensions come from `Element.Dx`, `Element.Dy`, `Element.Dz`** (user input from form), NOT from ElementSubType
- Calculations use `Decimal` for precision
- All formulas should return Decimal values, not floats
- Per-ElementSubTypeElements formulas take precedence over default formulas
- Default formulas are applied sequentially, so order matters
- Each default formula receives the result from the previous formula
- When Element dimensions change, all related ElementSubTypeElements are automatically recalculated
