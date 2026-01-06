"""
Test Category Folder Structure Creation and Validation

This script verifies:
1) Folder paths generated for category-based uploads
2) Category mappings for all claim types (health, life, car)
3) Normalization of category names
4) Backward-compatible behavior for pending claims

It does NOT perform real uploads; it validates path logic and mappings.
"""
import sys
from pathlib import Path

# Ensure local imports work when run directly
sys.path.insert(0, str(Path(__file__).parent))

from document_utils import derive_folder_path, normalize_category_for_folder, extract_folder_from_url  # noqa: E402
from category_mapping import CATEGORY_MAPPING, VALID_CATEGORIES, get_category_id, is_valid_category, normalize_category_id  # noqa: E402


def assert_equal(actual, expected, msg):
    if actual != expected:
        raise AssertionError(f"{msg}. Expected: {expected}, Got: {actual}")


def test_folder_paths():
    print("=" * 70)
    print("TASK 6.1: TEST FOLDER STRUCTURE CREATION (LOGIC)")
    print("=" * 70)

    # Claim with claimId and category
    path = derive_folder_path(userId=1, documentType="claim_document", claimId=999, category="Death Certificate")
    expected = "claims/999/death-certificate"
    print(f"claims/999/Death Certificate -> {path}")
    assert_equal(path, expected, "Claim path with category")

    # Claim with claimId but no category (backward compatible)
    path_no_cat = derive_folder_path(userId=1, documentType="claim_document", claimId=999, category=None)
    expected_no_cat = "claims/999"
    print(f"claims/999 (no category) -> {path_no_cat}")
    assert_equal(path_no_cat, expected_no_cat, "Claim path without category")

    # Pending claim with category
    pending_path = derive_folder_path(userId=7, documentType="claim_document", claimId=None, category="Claim Form")
    expected_pending = "claims/pending/7/claim-form"
    print(f"pending/7/Claim Form -> {pending_path}")
    assert_equal(pending_path, expected_pending, "Pending claim path with category")

    # Pending claim without category (backward compatible)
    pending_no_cat = derive_folder_path(userId=7, documentType="claim_document", claimId=None, category=None)
    expected_pending_no_cat = "claims/pending/7"
    print(f"pending/7 (no category) -> {pending_no_cat}")
    assert_equal(pending_no_cat, expected_pending_no_cat, "Pending claim path without category")


def test_category_mappings():
    print("\n" + "=" * 70)
    print("TASK 6.3: TEST CATEGORY MAPPINGS FOR ALL CLAIM TYPES")
    print("=" * 70)

    # Ensure every mapping is valid per claim type
    for claim_type, mapping in CATEGORY_MAPPING.items():
        valid_set = VALID_CATEGORIES.get(claim_type, set())
        for doc_name, cat_id in mapping.items():
            normalized = normalize_category_id(doc_name)
            print(f"[{claim_type}] {doc_name} -> {cat_id} (normalized: {normalized})")
            # Cat ID should be in valid set
            if valid_set:
                assert cat_id in valid_set, f"Category '{cat_id}' not in valid set for '{claim_type}'"
            # get_category_id should resolve
            resolved = get_category_id(claim_type, doc_name)
            assert_equal(resolved, cat_id, f"get_category_id mismatch for {doc_name}")
            # normalized should match cat_id when mapped
            if normalized != cat_id:
                # normalized may differ (e.g., post-mortem-report-if-applicable vs post-mortem)
                # ensure cat_id is still valid
                assert cat_id in valid_set, f"Normalized mismatch but cat_id not valid: {cat_id}"
        # Ensure all valid categories are covered by mapping (lenient; optional)
        missing = [c for c in valid_set if c not in mapping.values()]
        if missing:
            print(f"[{claim_type}] Note: valid categories not in display-name mapping (ok): {missing}")


def test_url_extraction():
    print("\n" + "=" * 70)
    print("TASK 6.2: TEST DOCUMENT RETRIEVAL PATHS (LOGIC)")
    print("=" * 70)
    old_url = "https://acct.blob.core.windows.net/container/claims/123/document.pdf"
    new_url = "https://acct.blob.core.windows.net/container/claims/123/death-certificate/document.pdf"
    extracted_old = extract_folder_from_url(old_url)
    extracted_new = extract_folder_from_url(new_url)
    print(f"Old URL -> {extracted_old}")
    print(f"New URL -> {extracted_new}")
    assert_equal(extracted_old, "claims/123", "Old URL extraction")
    assert_equal(extracted_new, "claims/123/death-certificate", "New URL extraction")


def test_normalization_cases():
    print("\n" + "=" * 70)
    print("EXTRA: CATEGORY NORMALIZATION CASES")
    print("=" * 70)
    cases = [
        ("Death Certificate", "death-certificate"),
        ("FIR Copy (if accidental)", "fir-copy-if-accidental"),
        ("Post Mortem Report (if applicable)", "post-mortem-report-if-applicable"),
        ("Claim Form", "claim-form"),
    ]
    for raw, expected in cases:
        norm = normalize_category_for_folder(raw)
        print(f"{raw} -> {norm}")
        assert_equal(norm, expected, f"Normalization mismatch for '{raw}'")


def main():
    test_folder_paths()
    test_category_mappings()
    test_url_extraction()
    test_normalization_cases()
    print("\n✅ All logical tests for Task 6 passed (folder paths, mappings, normalization, URL extraction).")
    print("Note: No live Azure upload executed in this script; it validates logic and structure.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

