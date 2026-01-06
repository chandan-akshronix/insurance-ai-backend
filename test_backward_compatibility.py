"""
Test Backward Compatibility for Category-Based Folder Organization

This script tests that:
1. Documents without category use old folder structure
2. Documents with category use new folder structure
3. Both structures work correctly
4. Existing documents remain accessible
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from document_utils import derive_folder_path, extract_folder_from_url

def test_backward_compatibility():
    """Test backward compatibility for folder structure"""
    print("=" * 70)
    print("TASK 5: TESTING BACKWARD COMPATIBILITY")
    print("=" * 70)
    
    print("\n📁 Testing Folder Path Derivation")
    print("-" * 70)
    
    # Test 1: Old structure (without category)
    print("\n1. Testing OLD structure (without category):")
    old_path = derive_folder_path(userId=123, documentType="claim_document", claimId=456, category=None)
    print(f"   Input: userId=123, claimId=456, category=None")
    print(f"   Output: {old_path}")
    assert old_path == "claims/456", f"Expected 'claims/456', got '{old_path}'"
    print("   ✅ Old structure works correctly")
    
    # Test 2: New structure (with category)
    print("\n2. Testing NEW structure (with category):")
    new_path = derive_folder_path(userId=123, documentType="claim_document", claimId=456, category="death-certificate")
    print(f"   Input: userId=123, claimId=456, category='death-certificate'")
    print(f"   Output: {new_path}")
    assert new_path == "claims/456/death-certificate", f"Expected 'claims/456/death-certificate', got '{new_path}'"
    print("   ✅ New structure works correctly")
    
    # Test 3: Pending claims without category
    print("\n3. Testing PENDING claims (without category):")
    pending_old = derive_folder_path(userId=123, documentType="claim_document", claimId=None, category=None)
    print(f"   Input: userId=123, claimId=None, category=None")
    print(f"   Output: {pending_old}")
    assert pending_old == "claims/pending/123", f"Expected 'claims/pending/123', got '{pending_old}'"
    print("   ✅ Pending old structure works correctly")
    
    # Test 4: Pending claims with category
    print("\n4. Testing PENDING claims (with category):")
    pending_new = derive_folder_path(userId=123, documentType="claim_document", claimId=None, category="claim-form")
    print(f"   Input: userId=123, claimId=None, category='claim-form'")
    print(f"   Output: {pending_new}")
    assert pending_new == "claims/pending/123/claim-form", f"Expected 'claims/pending/123/claim-form', got '{pending_new}'"
    print("   ✅ Pending new structure works correctly")
    
    # Test 5: URL extraction (old structure)
    print("\n5. Testing URL extraction (old structure):")
    old_url = "https://account.blob.core.windows.net/container/claims/456/document.pdf"
    old_folder = extract_folder_from_url(old_url)
    print(f"   URL: {old_url}")
    print(f"   Extracted folder: {old_folder}")
    assert old_folder == "claims/456", f"Expected 'claims/456', got '{old_folder}'"
    print("   ✅ Old URL extraction works correctly")
    
    # Test 6: URL extraction (new structure)
    print("\n6. Testing URL extraction (new structure):")
    new_url = "https://account.blob.core.windows.net/container/claims/456/death-certificate/document.pdf"
    new_folder = extract_folder_from_url(new_url)
    print(f"   URL: {new_url}")
    print(f"   Extracted folder: {new_folder}")
    assert new_folder == "claims/456/death-certificate", f"Expected 'claims/456/death-certificate', got '{new_folder}'"
    print("   ✅ New URL extraction works correctly")
    
    # Test 7: Category normalization
    print("\n7. Testing category normalization:")
    from document_utils import normalize_category_for_folder
    
    test_cases = [
        ("Death Certificate", "death-certificate"),
        ("FIR Copy (if accidental)", "fir-copy-if-accidental"),
        ("Claim Form", "claim-form"),
        ("Post Mortem Report (if applicable)", "post-mortem-report-if-applicable"),
    ]
    
    for input_cat, expected in test_cases:
        normalized = normalize_category_for_folder(input_cat)
        print(f"   '{input_cat}' -> '{normalized}'")
        assert normalized == expected, f"Expected '{expected}', got '{normalized}'"
    
    print("   ✅ Category normalization works correctly")
    
    print("\n" + "=" * 70)
    print("BACKWARD COMPATIBILITY TEST RESULTS")
    print("=" * 70)
    print("\n✅ All tests passed!")
    print("\nSummary:")
    print("  ✅ Old structure (without category) works correctly")
    print("  ✅ New structure (with category) works correctly")
    print("  ✅ Both structures coexist without issues")
    print("  ✅ URL extraction works for both structures")
    print("  ✅ Category normalization works correctly")
    print("\n✅ Backward compatibility is maintained!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        test_backward_compatibility()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

