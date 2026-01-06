# Backward Compatibility Guide for Category-Based Folder Organization

## Overview

This guide documents how the system handles backward compatibility with existing documents that don't have category-based folder organization.

## Folder Structure Evolution

### Old Structure (Before Category Organization)
```
claims/{claimId}/document.pdf
claims/pending/{userId}/document.pdf
```

### New Structure (With Category Organization)
```
claims/{claimId}/{category}/document.pdf
claims/pending/{userId}/{category}/document.pdf
```

**Example:**
```
claims/123/death-certificate/document.pdf
claims/pending/456/claim-form/document.pdf
```

## Backward Compatibility Implementation

### 1. Folder Path Derivation

The `derive_folder_path()` function automatically handles backward compatibility:

**With Category:**
- `derive_folder_path(userId=123, documentType="claim_document", claimId=456, category="death-certificate")`
- Returns: `"claims/456/death-certificate"`

**Without Category (Backward Compatible):**
- `derive_folder_path(userId=123, documentType="claim_document", claimId=456, category=None)`
- Returns: `"claims/456"` (old structure)

### 2. Document Upload

The upload endpoint accepts `category` as an **optional** parameter:

```python
@router.post("/upload")
async def upload_document(
    ...
    category: Optional[str] = Form(None),  # Optional - backward compatible
    ...
):
```

**Behavior:**
- If `category` is provided → Uses new structure: `claims/{claimId}/{category}/`
- If `category` is not provided → Uses old structure: `claims/{claimId}/`

### 3. Document Retrieval

Documents are retrieved by URL, which contains the full path. Both old and new structures work:

**Old Structure URLs:**
```
https://account.blob.core.windows.net/container/claims/123/document.pdf
```

**New Structure URLs:**
```
https://account.blob.core.windows.net/container/claims/123/death-certificate/document.pdf
```

Both URLs are accessible and work correctly.

## Handling Existing Documents

### MongoDB Documents

Existing MongoDB documents may not have the `category` field. The system handles this:

1. **Document Retrieval:**
   - If `category` exists → Use it
   - If `category` doesn't exist → Use `undefined` (fallback)

2. **ClaimsTrack Page:**
   - Documents without category still display correctly
   - Category badge only shows if category exists

### Azure Blob Storage

Existing documents in Azure Blob Storage remain accessible:

1. **Old Structure Documents:**
   - Still accessible via their URLs
   - No migration needed
   - Continue to work as before

2. **New Structure Documents:**
   - Organized by category
   - Better organization
   - Still accessible via URLs

## Migration Strategy (Optional)

If you want to migrate existing documents to category-based folders:

### Option 1: No Migration (Recommended)
- Keep existing documents in old structure
- New documents use category-based structure
- Both structures coexist

### Option 2: Gradual Migration
- Migrate documents when they're accessed
- Update MongoDB with category field
- Move files in Azure Blob Storage

### Option 3: Full Migration
- Script to migrate all existing documents
- Extract category from MongoDB if available
- Move files to category-based folders

## Testing Backward Compatibility

### Test Cases

1. **Upload without category:**
   - Upload document without `category` parameter
   - Verify it uses old structure: `claims/{claimId}/`
   - Verify document is accessible

2. **Upload with category:**
   - Upload document with `category` parameter
   - Verify it uses new structure: `claims/{claimId}/{category}/`
   - Verify document is accessible

3. **Retrieve old documents:**
   - Retrieve claim with old structure documents
   - Verify documents display correctly
   - Verify URLs work

4. **Retrieve new documents:**
   - Retrieve claim with new structure documents
   - Verify documents display correctly
   - Verify category badge shows

5. **Mixed documents:**
   - Claim with both old and new structure documents
   - Verify all documents display correctly
   - Verify all URLs work

## Code Examples

### Backend: Check if Document Has Category

```python
def has_category_folder(url: str) -> bool:
    """Check if document URL indicates category-based folder structure"""
    if 'blob.core.windows.net' not in url:
        return False
    
    # Extract folder path
    parts = url.split('blob.core.windows.net/')
    if len(parts) > 1:
        path_parts = parts[1].split('/')
        # New structure: container/claims/{claimId}/{category}/file
        # Old structure: container/claims/{claimId}/file
        if len(path_parts) >= 4 and path_parts[1] == 'claims':
            # Check if there's a category folder (4th part after container)
            return len(path_parts) >= 5
    
    return False
```

### Frontend: Handle Documents Without Category

```typescript
// Documents without category still work
const documents = claim.documents.map(doc => ({
  ...doc,
  category: doc.category || undefined,  // Optional category
  // Document still accessible even without category
}));
```

## Best Practices

1. **Always provide category for new uploads:**
   - Better organization
   - Easier to find documents
   - Consistent structure

2. **Don't break existing documents:**
   - Old structure still works
   - No need to migrate immediately
   - Gradual adoption is fine

3. **Handle missing category gracefully:**
   - Don't fail if category is missing
   - Use fallback to old structure
   - Log warnings for debugging

4. **Document category in MongoDB:**
   - Save category with document metadata
   - Helps with future queries
   - Enables better organization

## Summary

✅ **Backward Compatibility Maintained:**
- Old folder structure still works
- Documents without category still accessible
- No breaking changes
- Gradual adoption possible

✅ **New Features Available:**
- Category-based folder organization
- Better document management
- Improved organization in Azure

✅ **Migration Not Required:**
- Existing documents continue to work
- New documents use category structure
- Both structures coexist

