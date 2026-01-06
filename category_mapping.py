"""
Category Mapping and Validation Functions

Maps document names to category IDs and validates categories for claim types.
"""

from typing import Dict, List, Optional, Set

# Category mapping for each claim type
# Maps document display names to category IDs (folder-safe names)
CATEGORY_MAPPING: Dict[str, Dict[str, str]] = {
    "life": {
        "Death Certificate": "death-certificate",
        "Death Claim Form": "claim-form",
        "Original Policy Document": "policy-document",
        "Claimant ID Proof": "claimant-id",
        "Address Proof": "claimant-address",
        "Medical Records (if illness)": "medical-records",
        "FIR Copy (if accidental)": "fir-copy",
        "Post Mortem Report (if applicable)": "post-mortem",
        "Nominee Relationship Proof": "nominee-proof",
        "Cancelled Cheque/Bank Statement": "bank-details"
    },
    "health": {
        # Cashless category
        "Pre-Authorization Form": "pre-auth",
        "Hospital ID Card": "hospital-id",
        "Policy Copy": "policy-copy",
        "Photo ID Proof": "id-proof",
        "Medical Reports/Prescription": "medical-reports",
        # Reimbursement category
        "Duly Filled Claim Form": "claim-form",
        "Hospital Bills & Receipts": "hospital-bills",
        "Discharge Summary": "discharge-summary",
        "Investigation Reports": "medical-reports",
        "Doctor's Prescription": "prescription",
        "Payment Receipts": "payment-receipts",
        "Cancelled Cheque": "cancelled-cheque"
    },
    "car": {
        "Duly Filled Claim Form": "claim-form",
        "Policy Copy": "policy-copy",
        "RC Book Copy": "rc-copy",
        "Driving License": "driving-license",
        "FIR Copy": "fir-copy",
        "Vehicle Damage Photos": "damage-photos",
        "Repair Estimate/Invoice": "repair-estimate",
        "Survey Report": "survey-report",
        "Third Party Documents": "third-party-docs"
    }
}

# Valid category IDs for each claim type (for validation)
VALID_CATEGORIES: Dict[str, Set[str]] = {
    "life": {
        "death-certificate", "claim-form", "policy-document", "claimant-id",
        "claimant-address", "medical-records", "fir-copy", "post-mortem",
        "nominee-proof", "bank-details"
    },
    "health": {
        "pre-auth", "hospital-id", "policy-copy", "id-proof", "medical-reports",
        "claim-form", "hospital-bills", "discharge-summary", "prescription",
        "payment-receipts", "cancelled-cheque"
    },
    "car": {
        "claim-form", "policy-copy", "rc-copy", "driving-license", "fir-copy",
        "damage-photos", "repair-estimate", "survey-report", "third-party-docs"
    }
}


def get_category_id(claim_type: str, document_name: str) -> Optional[str]:
    """
    Get category ID from document name for a given claim type.
    
    Args:
        claim_type: Type of claim ('life', 'health', 'car')
        document_name: Display name of the document (e.g., "Death Certificate")
    
    Returns:
        Category ID (e.g., "death-certificate") or None if not found
    
    Examples:
        >>> get_category_id("life", "Death Certificate")
        "death-certificate"
        >>> get_category_id("health", "Pre-Authorization Form")
        "pre-auth"
        >>> get_category_id("car", "Duly Filled Claim Form")
        "claim-form"
    """
    if claim_type not in CATEGORY_MAPPING:
        return None
    
    return CATEGORY_MAPPING[claim_type].get(document_name)


def get_document_name(claim_type: str, category_id: str) -> Optional[str]:
    """
    Get document display name from category ID for a given claim type.
    
    Args:
        claim_type: Type of claim ('life', 'health', 'car')
        category_id: Category ID (e.g., "death-certificate")
    
    Returns:
        Document display name (e.g., "Death Certificate") or None if not found
    
    Examples:
        >>> get_document_name("life", "death-certificate")
        "Death Certificate"
        >>> get_document_name("health", "pre-auth")
        "Pre-Authorization Form"
    """
    if claim_type not in CATEGORY_MAPPING:
        return None
    
    # Reverse lookup
    for doc_name, cat_id in CATEGORY_MAPPING[claim_type].items():
        if cat_id == category_id:
            return doc_name
    
    return None


def is_valid_category(claim_type: str, category_id: str) -> bool:
    """
    Validate if a category ID is valid for a given claim type.
    
    Args:
        claim_type: Type of claim ('life', 'health', 'car')
        category_id: Category ID to validate
    
    Returns:
        True if category is valid, False otherwise
    
    Examples:
        >>> is_valid_category("life", "death-certificate")
        True
        >>> is_valid_category("life", "invalid-category")
        False
        >>> is_valid_category("health", "pre-auth")
        True
    """
    if claim_type not in VALID_CATEGORIES:
        return False
    
    return category_id in VALID_CATEGORIES[claim_type]


def get_all_categories_for_claim_type(claim_type: str) -> List[str]:
    """
    Get all valid category IDs for a claim type.
    
    Args:
        claim_type: Type of claim ('life', 'health', 'car')
    
    Returns:
        List of valid category IDs
    
    Examples:
        >>> get_all_categories_for_claim_type("life")
        ['death-certificate', 'claim-form', 'policy-document', ...]
    """
    if claim_type not in VALID_CATEGORIES:
        return []
    
    return sorted(list(VALID_CATEGORIES[claim_type]))


def normalize_category_id(category: str) -> str:
    """
    Normalize a category string to a valid category ID format.
    
    This handles cases where category might be a display name or already a category ID.
    
    Args:
        category: Category string (could be display name or category ID)
    
    Returns:
        Normalized category ID
    
    Examples:
        >>> normalize_category_id("Death Certificate")
        "death-certificate"
        >>> normalize_category_id("death-certificate")
        "death-certificate"
    """
    import re
    # Convert to lowercase
    normalized = category.lower()
    # Replace spaces and underscores with hyphens
    normalized = normalized.replace(' ', '-').replace('_', '-')
    # Remove any special characters except hyphens and alphanumeric
    normalized = re.sub(r'[^a-z0-9\-]', '', normalized)
    # Remove multiple consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized

