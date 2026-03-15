"""
Calculation service for ElementSubTypeElements dimensions (Dx, Dy, Dz)
based on Element dimensions (user input) and Offer coefficient selections.

Each ElementSubTypeElements can have its own formula identified by formula_code.
"""
from decimal import Decimal
from typing import Dict, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Coefficient

from .models import Element, ElementSubType, ElementSubTypeElements, Offer, OfferCoefficientSelection


class DimensionCalculator:
    """
    Service class for calculating dimensions based on formulas.
    Formulas can be customized per:
    - ElementSubTypeElements (using formula_code)
    - Element type and coefficient group (default formulas)
    """
    
    def __init__(self):
        # Per-ElementSubTypeElements formula registry
        # Format: {formula_code: formula_function}
        # These take precedence over default formulas
        self.element_formulas = {}
        
        # Default formula registry by element type and coefficient group
        # Format: {element_type: {coefficient_group_code: formula_function}}
        self.default_formulas = {
            # Example structure - you'll define your actual formulas
            'donji_elementi': {
                'ceiling': self._formula_ceiling,
                'floor': self._formula_floor,
                'back': self._formula_back,
                'tier': self._formula_tier,
            },
            'gornji_elementi': {
                'ceiling': self._formula_ceiling,
                'floor': self._formula_floor,
                'back': self._formula_back,
                'tier': self._formula_tier,
            },
            # Add more element types as needed
        }
    
    def calculate_dimensions(
        self,
        element: Element,
        offer: Offer,
        element_sub_type_element: Optional[ElementSubTypeElements] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate Dx, Dy, Dz for an ElementSubTypeElements based on:
        - Element dimensions (Dx, Dy, Dz) - user input from form
        - Offer's selected coefficients
        - ElementSubTypeElements formula_code (if specified)
        
        Args:
            element: The Element instance with user-input Dx, Dy, Dz values
            offer: The Offer with coefficient selections
            element_sub_type_element: Optional ElementSubTypeElements instance (for per-element formulas)
            
        Returns:
            Dictionary with 'Dx', 'Dy', 'Dz' as Decimal values
        """
        # Get base dimensions from Element (user input)
        base_dx = element.Dx or Decimal('0')
        base_dy = element.Dy or Decimal('0')
        base_dz = element.Dz or Decimal('0')
        
        # Get offer's coefficient selections
        coefficient_selections = self._get_offer_coefficients(offer)
        
        # Check if this ElementSubTypeElements has a custom formula
        formula_code = None
        if element_sub_type_element and element_sub_type_element.formula_code:
            formula_code = element_sub_type_element.formula_code
        
        # If custom formula exists, use it
        if formula_code and formula_code in self.element_formulas:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Using custom formula '{formula_code}' for ElementSubTypeElements {element_sub_type_element.id}"
            )
            formula_func = self.element_formulas[formula_code]
            result = formula_func(
                base_dx, base_dy, base_dz,
                coefficient_selections,
                element,
                element_sub_type_element
            )
            logger.debug(
                f"Formula '{formula_code}' result: Dx={result['Dx']}, Dy={result['Dy']}, Dz={result['Dz']}"
            )
            return result
        elif formula_code:
            # Formula code specified but not found
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Formula code '{formula_code}' specified for ElementSubTypeElements {element_sub_type_element.id if element_sub_type_element else 'unknown'}, "
                f"but not found in registered formulas. Available formulas: {list(self.element_formulas.keys())}"
            )
        
        # Otherwise, use default formulas based on element type and coefficient groups
        element_type = element.element_type
        formulas = self.default_formulas.get(element_type, {})
        
        # Initialize result with base dimensions
        result = {
            'Dx': base_dx,
            'Dy': base_dy,
            'Dz': base_dz,
        }
        
        # Apply formulas based on coefficient groups
        for group_code, formula_func in formulas.items():
            if group_code in coefficient_selections:
                coefficient = coefficient_selections[group_code]
                # Apply formula
                result = formula_func(
                    base_dx, base_dy, base_dz,
                    coefficient,
                    result,
                    element,
                    element_sub_type_element
                )
        
        return result
    
    def _get_offer_coefficients(self, offer: Offer) -> Dict[str, 'Coefficient']:
        """
        Get all coefficient selections for an offer, keyed by group code.
        
        Returns:
            Dictionary mapping group_code -> Coefficient instance
        """
        selections = OfferCoefficientSelection.objects.filter(
            offer=offer
        ).select_related('coefficient', 'group')
        
        return {
            sel.group.code: sel.coefficient
            for sel in selections
        }
    
    def _get_selected_coefficient_codes(self, offer: Offer) -> set:
        """
        Get all selected coefficient codes for an offer.
        
        Returns:
            Set of coefficient codes (strings)
        """
        selections = OfferCoefficientSelection.objects.filter(
            offer=offer
        ).select_related('coefficient')
        
        return {
            sel.coefficient.code
            for sel in selections
        }
    
    # Default formula implementations - you'll replace these with your actual formulas
    
    def _formula_ceiling(
        self,
        base_dx: Decimal,
        base_dy: Decimal,
        base_dz: Decimal,
        coefficient: 'Coefficient',
        current_result: Dict[str, Decimal],
        element: Element,
        element_sub_type_element: Optional[ElementSubTypeElements]
    ) -> Dict[str, Decimal]:
        """
        Formula for ceiling coefficient.
        Modify this based on your requirements.
        """
        # Example: if coefficient code is "KOEF.UKLOP.PLAFON", multiply by coefficient.value
        # You'll define your actual formula here
        multiplier = Decimal(coefficient.value) / Decimal('100')  # Example: convert to percentage
        
        return {
            'Dx': current_result['Dx'] * multiplier,
            'Dy': current_result['Dy'] * multiplier,
            'Dz': current_result['Dz'] * multiplier,
        }
    
    def _formula_floor(
        self,
        base_dx: Decimal,
        base_dy: Decimal,
        base_dz: Decimal,
        coefficient: 'Coefficient',
        current_result: Dict[str, Decimal],
        element: Element,
        element_sub_type_element: Optional[ElementSubTypeElements]
    ) -> Dict[str, Decimal]:
        """
        Formula for floor coefficient.
        Modify this based on your requirements.
        """
        # Example implementation
        multiplier = Decimal(coefficient.value) / Decimal('100')
        
        return {
            'Dx': current_result['Dx'] * multiplier,
            'Dy': current_result['Dy'] * multiplier,
            'Dz': current_result['Dz'] * multiplier,
        }
    
    def _formula_back(
        self,
        base_dx: Decimal,
        base_dy: Decimal,
        base_dz: Decimal,
        coefficient: 'Coefficient',
        current_result: Dict[str, Decimal],
        element: Element,
        element_sub_type_element: Optional[ElementSubTypeElements]
    ) -> Dict[str, Decimal]:
        """
        Formula for back coefficient.
        Modify this based on your requirements.
        """
        # Example implementation
        multiplier = Decimal(coefficient.value) / Decimal('100')
        
        return {
            'Dx': current_result['Dx'] * multiplier,
            'Dy': current_result['Dy'] * multiplier,
            'Dz': current_result['Dz'] * multiplier,
        }
    
    def _formula_tier(
        self,
        base_dx: Decimal,
        base_dy: Decimal,
        base_dz: Decimal,
        coefficient: 'Coefficient',
        current_result: Dict[str, Decimal],
        element: Element,
        element_sub_type_element: Optional[ElementSubTypeElements]
    ) -> Dict[str, Decimal]:
        """
        Formula for tier coefficient.
        Modify this based on your requirements.
        """
        # Example implementation
        multiplier = Decimal(coefficient.value) / Decimal('100')
        
        return {
            'Dx': current_result['Dx'] * multiplier,
            'Dy': current_result['Dy'] * multiplier,
            'Dz': current_result['Dz'] * multiplier,
        }
    
    def register_default_formula(
        self,
        element_type: str,
        coefficient_group_code: str,
        formula_func: Callable
    ):
        """
        Register a default formula for a specific element type and coefficient group.
        
        Args:
            element_type: Element type (e.g., 'donji_elementi')
            coefficient_group_code: Coefficient group code (e.g., 'ceiling')
            formula_func: Function that takes (base_dx, base_dy, base_dz, coefficient, current_result, element, element_sub_type_element)
                         and returns a dict with 'Dx', 'Dy', 'Dz'
        """
        if element_type not in self.default_formulas:
            self.default_formulas[element_type] = {}
        self.default_formulas[element_type][coefficient_group_code] = formula_func
    
    def register_element_formula(
        self,
        formula_code: str,
        formula_func: Callable
    ):
        """
        Register a custom formula for a specific ElementSubTypeElements (identified by formula_code).
        This formula will take precedence over default formulas.
        
        Args:
            formula_code: Unique identifier for this formula (should match ElementSubTypeElements.formula_code)
            formula_func: Function that takes (base_dx, base_dy, base_dz, coefficient_selections, element, element_sub_type_element)
                         and returns a dict with 'Dx', 'Dy', 'Dz'
                         
        Note: The formula_func signature is different from default formulas:
        - It receives all coefficient_selections (dict) instead of a single coefficient
        - It can access all coefficients and implement complex logic
        """
        self.element_formulas[formula_code] = formula_func


# Global calculator instance
calculator = DimensionCalculator()


# Custom formula functions - Add your formulas here
def formula_stranica_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]
) -> Dict[str, Decimal]:
    """
    Custom formula for stranica dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = base_dy - deb_korp * KOEF.NAKL.POD - deb_korp * KOEF.NAKL.PLAFON
    - Dy = base_dz - deb_fronte - 2 - deb_leđa * KOEF.NAKL.LEĐA
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KOEF.NAKL.POD')
    # koef_nakl_plafon = get_coefficient_value_by_code('KOEF.NAKL.PLAFON')
    # koef_nakl_leda = get_coefficient_value_by_code('KOEF.NAKL.LEĐA')
    
    koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    koef_nakl_leda = get_coefficient_value_by_code('KNL')

    # Calculate dimensions
    # Dx = VISINA (base_dy) - DEB.KORP * KOEF.NAKL.POD - DEB.KORP * KOEF.NAKL.PLAFON
    result_dx = base_dy - (deb_korp * koef_nakl_pod) - (deb_korp * koef_nakl_plafon)
    
    # Dy = DUBINA (base_dz) - DEB.FRONTE - 2 - DEB.LEĐA * KOEF.NAKL.LEĐA
    result_dy = base_dz - deb_fronte - Decimal('2') - (deb_ledja * koef_nakl_leda)
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }


def formula_pod_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]
) -> Dict[str, Decimal]:
    """
    Custom formula for pod dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = ŠIRINA-2*DEB.KORP*KOEF.UKL.POD
    - Dy = DUBINA-DEB.FRONTE-2-DEB.LEĐA*KOEF.NAKL.LEĐA-(DEB.LEĐA+20)*KOEF.NUT.LEĐA-DEB.LEĐA*KOEF.FALC.LEĐA
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    # koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    koef_nakl_leda = get_coefficient_value_by_code('KNL')
    koef_ukl_pod = get_coefficient_value_by_code('KUPO')
    koef_nut_leda = get_coefficient_value_by_code('KNUL')
    koef_falc_leda = get_coefficient_value_by_code('KFL')

    # Calculate dimensions
    # Dx = ŠIRINA-2*DEB.KORP*KOEF.UKL.POD
    result_dx = base_dx - 2 * deb_korp * koef_ukl_pod
    
    # Dy = DUBINA-DEB.FRONTE-2-DEB.LEĐA*KOEF.NAKL.LEĐA-(DEB.LEĐA+20)*KOEF.NUT.LEĐA-DEB.LEĐA*KOEF.FALC.LEĐA
    # TODO: PRovjeriti ovu formulu da li je uvijek +20
    result_dy = base_dz - deb_fronte - Decimal('2') - (deb_ledja * koef_nakl_leda) - (deb_ledja + Decimal('20')) * koef_nut_leda - deb_ledja * koef_falc_leda
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }


def formula_polica_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]
) -> Dict[str, Decimal]:
    """
    Custom formula for pod dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = ŠIRINA-2*DEB.KORP-1
    - Dy = DUBINA-DEB.FRONTE-2-DEB.LEĐA*KOEF.NAKL.LEĐA-(DEB.LEĐA+20)*KOEF.NUT.LEĐA-DEB.LEĐA*KOEF.FALC.LEĐA
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    # koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    koef_nakl_leda = get_coefficient_value_by_code('KNL')
    koef_ukl_pod = get_coefficient_value_by_code('KUPO')
    koef_nut_leda = get_coefficient_value_by_code('KNUL')
    koef_falc_leda = get_coefficient_value_by_code('KFL')

    # Calculate dimensions
    # Dx = ŠIRINA-2*DEB.KORP-1
    # TODO: PRovjeriti ovu formulu da li je uvijek -1 nema koeficijenta
    result_dx = base_dx - 2 * deb_korp - Decimal('1')
    
    # Dy = DUBINA-DEB.FRONTE-2-DEB.LEĐA*KOEF.NAKL.LEĐA-(DEB.LEĐA+20)*KOEF.NUT.LEĐA-DEB.LEĐA*KOEF.FALC.LEĐA-20
    # TODO: PRovjeriti ovu formulu da li je uvijek +20
    result_dy = base_dz - deb_fronte - Decimal('2') - (deb_ledja * koef_nakl_leda) - (deb_ledja + Decimal('20')) * koef_nut_leda - deb_ledja * koef_falc_leda - Decimal('20')
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }



def formula_fronta_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]
) -> Dict[str, Decimal]:
    """
    Custom formula for fronta dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = VISINA-4
    - Dy = ŠIRINA-4
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    # koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    # koef_nakl_leda = get_coefficient_value_by_code('KNL')
    # koef_ukl_pod = get_coefficient_value_by_code('KUPO')
    # koef_nut_leda = get_coefficient_value_by_code('KNUL')
    # koef_falc_leda = get_coefficient_value_by_code('KFL')

    # Calculate dimensions
    # Dx = VISINA-4
    result_dx = base_dy - Decimal(4)
    
    # Dy = ŠIRINA-4
    result_dy = base_dx - Decimal(4)
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }


def formula_ledja_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]
) -> Dict[str, Decimal]:
    """
    Custom formula for ledja dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = VISINA-2
    - Dy = ŠIRINA-2*KOEF.NAKL.LEĐA-(2*DEB.KORP-20)*KOEF.FALC.LEĐA-(2*DEB.KORP-20)*KOEF.NUT.LEĐA
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    # koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    koef_nakl_leda = get_coefficient_value_by_code('KNL')
    # koef_ukl_pod = get_coefficient_value_by_code('KUPO')
    koef_nut_leda = get_coefficient_value_by_code('KNUL')
    koef_falc_leda = get_coefficient_value_by_code('KFL')

    # Calculate dimensions
    # Dx = VISINA-2
    result_dx = base_dy - Decimal(2)
    
    # Dy = ŠIRINA-2*KOEF.NAKL.LEĐA-(2*DEB.KORP-20)*KOEF.FALC.LEĐA-(2*DEB.KORP-20)*KOEF.NUT.LEĐA
    result_dy = base_dx - Decimal(2) * koef_nakl_leda - (Decimal(2) * deb_korp - Decimal('20')) * koef_falc_leda - (Decimal(2) * deb_korp - Decimal('20')) * koef_nut_leda
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }

def formula_plafonvezac_dimensions_calculation(
    base_dx: Decimal,
    base_dy: Decimal,
    base_dz: Decimal,
    coefficient_selections: Dict[str, 'Coefficient'],
    element: Element,
    element_sub_type_element: Optional[ElementSubTypeElements]  
) -> Dict[str, Decimal]:
    """
    Custom formula for plafonvezac dimensions calculation.
    Calculates both Dx and Dy together.
    - Dx = ŠIRINA-2*DEB.KORP*KOEF.UKLOP.PLAFON
    - Dy = SIRINA VEZACA*KOEF.VEZAČI+D9*KOEF.PUN.PLAFON
    
    Args:
        base_dx, base_dy, base_dz: Base dimensions from Element
        coefficient_selections: Dict of {group_code: Coefficient} for selected coefficients
        element: The Element instance
        element_sub_type_element: The ElementSubTypeElements instance
    
    Returns:
        Dict with calculated Dx, Dy (Dz is not used but included for compatibility)
    """
    deb_korp = Decimal('18')  # TODO: It will depend of selected material and read it from material informations
    deb_fronte = Decimal('18')
    deb_ledja = Decimal('18')
    sirina_vezaca = Decimal('100')

    # Helper function to get coefficient value by its code
    # coefficient_selections is keyed by group_code, so we need to search through all coefficients
    def get_coefficient_value_by_code(target_code: str) -> Decimal:
        """Find coefficient by code and return its value, or 0 if not found."""
        for coeff in coefficient_selections.values():
            if coeff.code == target_code:
                return Decimal(coeff.value)
        return Decimal('0')
    
    # Get coefficient values (returns 0 if coefficient not selected)
    # koef_nakl_pod = get_coefficient_value_by_code('KNPO')
    # koef_nakl_plafon = get_coefficient_value_by_code('KNPL')
    # koef_nakl_leda = get_coefficient_value_by_code('KNL')
    # koef_ukl_pod = get_coefficient_value_by_code('KUPO')
    # koef_nut_leda = get_coefficient_value_by_code('KNUL')
    # koef_falc_leda = get_coefficient_value_by_code('KFL')
    koef_uklop_plafon = get_coefficient_value_by_code('KUPL')
    koef_vezaci = get_coefficient_value_by_code('KV')
    koef_pun_plafon = get_coefficient_value_by_code('PP')
    # TODO: PRovjeriti ovu formulu da li je uvijek D9 za pod_dx
    pod_dimensions = formula_pod_dimensions_calculation(base_dx, base_dy, base_dz, coefficient_selections, element, element_sub_type_element)
    pod_dx = pod_dimensions['Dx']
    pod_dy = pod_dimensions['Dy']

    # Calculate dimensions
    # Dx = ŠIRINA-2*DEB.KORP*KOEF.UKLOP.PLAFON
    result_dx = base_dx - Decimal(2) * deb_korp * koef_uklop_plafon
    
    # Dy = SIRINA VEZACA*KOEF.VEZAČI+D9*KOEF.PUN.PLAFON
    result_dy = sirina_vezaca * koef_vezaci + pod_dx * koef_pun_plafon
    
    # Dz is not calculated, return 0 for compatibility
    result_dz = Decimal('0')
    
    return {
        'Dx': result_dx,
        'Dy': result_dy,
        'Dz': result_dz,
    }

# Register custom formulas here
# This will be executed when the module is imported
calculator.register_element_formula('STRANICE_CALCULATION', formula_stranica_dimensions_calculation)
calculator.register_element_formula('POD_CALCULATION', formula_pod_dimensions_calculation)
calculator.register_element_formula('POLICA_CALCULATION', formula_polica_dimensions_calculation)
calculator.register_element_formula('FRONTA_CALCULATION', formula_fronta_dimensions_calculation)
calculator.register_element_formula('LEDJA_CALCULATION', formula_ledja_dimensions_calculation)
calculator.register_element_formula('PLAFONVEZAC_CALCULATION', formula_plafonvezac_dimensions_calculation)

def calculate_element_dimensions(
    element: Element,
    offer: Offer,
    element_sub_type_element: Optional[ElementSubTypeElements] = None
) -> Dict[str, Decimal]:
    """
    Convenience function to calculate dimensions for ElementSubTypeElements.
    Uses Element.Dx, Dy, Dz (user input) as base dimensions.
    
    Usage:
        from apps.offers.calculations import calculate_element_dimensions
        from apps.offers.models import Element, ElementSubTypeElements
        
        element = Element.objects.get(id=1)
        sub_type_element = ElementSubTypeElements.objects.get(id=1)
        dimensions = calculate_element_dimensions(element, offer, sub_type_element)
        sub_type_element.Dx = dimensions['Dx']
        sub_type_element.Dy = dimensions['Dy']
        sub_type_element.Dz = dimensions['Dz']
    """
    return calculator.calculate_dimensions(
        element,
        offer,
        element_sub_type_element
    )



