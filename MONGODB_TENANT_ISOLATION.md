# MongoDB Tenant Isolation for OCR Learning System

## Overview
The auto-learning OCR system uses MongoDB to store bank patterns and learning data. To ensure proper tenant isolation, all MongoDB collections must include tenant and merchant context.

## Required Schema Updates

### 1. bank_format_templates Collection

**Current Schema (Insecure):**
```javascript
{
  "_id": ObjectId("..."),
  "bank_code": "ABA",
  "template": {
    "patterns": [...],
    "confidence_base": 0.85
  },
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**New Schema (Tenant-Isolated):**
```javascript
{
  "_id": ObjectId("..."),
  "bank_code": "ABA",
  "tenant_id": "uuid-tenant-123",  // NEW: Tenant isolation
  "merchant_id": "uuid-merchant-456",  // NEW: Merchant-specific patterns
  "template": {
    "patterns": [...],
    "confidence_base": 0.85,
    "source": "tenant_learning"  // NEW: Track pattern source
  },
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

### 2. ocr_learning_queue Collection

**Current Schema (Insecure):**
```javascript
{
  "_id": ObjectId("..."),
  "bank_code": "ABA",
  "ocr_text": "Transfer to JOHN DOE...",
  "verified_data": {...},
  "extracted_patterns": {...},
  "verification_confidence": 0.95,
  "learned_at": ISODate("..."),
  "processed": false
}
```

**New Schema (Tenant-Isolated):**
```javascript
{
  "_id": ObjectId("..."),
  "bank_code": "ABA",
  "tenant_id": "uuid-tenant-123",  // NEW: Tenant isolation
  "merchant_id": "uuid-merchant-456",  // NEW: Merchant context
  "ocr_text": "Transfer to JOHN DOE...",
  "verified_data": {...},
  "extracted_patterns": {...},
  "verification_confidence": 0.95,
  "learned_at": ISODate("..."),
  "processed": false
}
```

## Migration Script

### Step 1: Backup Existing Data
```javascript
// In MongoDB shell
use customerDB

// Backup existing collections
db.bank_format_templates.aggregate([
  { $out: "bank_format_templates_backup" }
])

db.ocr_learning_queue.aggregate([
  { $out: "ocr_learning_queue_backup" }
])
```

### Step 2: Add Tenant Fields to Existing Data
```javascript
// Add tenant_id field to existing bank templates
// Mark existing patterns as "global" (no specific tenant)
db.bank_format_templates.updateMany(
  { tenant_id: { $exists: false } },
  {
    $set: {
      tenant_id: null,  // Global patterns available to all tenants
      merchant_id: null,
      "template.source": "global"
    }
  }
)

// Add tenant_id field to existing learning queue
// These old records should be marked for cleanup
db.ocr_learning_queue.updateMany(
  { tenant_id: { $exists: false } },
  {
    $set: {
      tenant_id: "unknown",
      merchant_id: "unknown",
      processed: true,  // Mark as processed to prevent cross-tenant learning
      migration_note: "Pre-tenant-isolation data - processed to prevent security issues"
    }
  }
)
```

### Step 3: Create Security Indexes
```javascript
// Compound indexes for efficient tenant-filtered queries
db.bank_format_templates.createIndex(
  { "tenant_id": 1, "bank_code": 1 },
  { name: "tenant_bank_patterns_idx" }
)

db.ocr_learning_queue.createIndex(
  { "tenant_id": 1, "processed": 1, "learned_at": -1 },
  { name: "tenant_learning_queue_idx" }
)

// Index for merchant-specific patterns
db.bank_format_templates.createIndex(
  { "tenant_id": 1, "merchant_id": 1, "bank_code": 1 },
  { name: "merchant_specific_patterns_idx" }
)
```

## Application Code Changes (COMPLETED)

### ✅ auto_learning_ocr.py
- Updated `detect_bank_and_extract()` to accept `tenant_id`
- Updated `_get_bank_patterns()` to filter by tenant
- Updated `learn_from_verification()` to require tenant_id
- Added tenant-aware caching with cache keys like `{bank}:{tenant}`

### ✅ smart_ocr_service.py
- Updated `_try_pattern_extraction()` to pass tenant_id
- Updated `_learn_from_success()` to accept and pass tenant/merchant IDs
- Updated `_learn_from_gpt4_success()` to pass tenant context

### ✅ Bot Handlers
- OCR handlers already pass `tenant_id` correctly
- Client handlers use `merchant_id` as tenant context

## Security Benefits

### Before (CRITICAL VULNERABILITY)
- Bank patterns learned from Tenant A affected Tenant B's verifications
- Cross-tenant data leakage in pattern learning
- No isolation between merchant-specific patterns

### After (SECURE)
- Each tenant gets their own pattern learning space
- Patterns learned from Tenant A only improve Tenant A's accuracy
- Merchant-specific patterns isolated within tenant boundaries
- Global fallback patterns available to all tenants

## Pattern Priority System

1. **Merchant-specific patterns** (highest accuracy, tenant+merchant filtered)
2. **Tenant-specific patterns** (tenant filtered)
3. **Global patterns** (fallback, available to all)

## Monitoring Queries

### Check tenant isolation is working:
```javascript
// Count patterns per tenant
db.bank_format_templates.aggregate([
  { $group: { _id: "$tenant_id", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Check for learning records without tenant_id (security issue)
db.ocr_learning_queue.find(
  {
    tenant_id: { $in: [null, "unknown"] },
    processed: false
  }
).count()
```

### Performance monitoring:
```javascript
// Most active learning tenants
db.ocr_learning_queue.aggregate([
  { $match: { learned_at: { $gte: new Date(Date.now() - 24*60*60*1000) } } },
  { $group: { _id: "$tenant_id", daily_learning: { $sum: 1 } } },
  { $sort: { daily_learning: -1 } }
])
```

## Production Deployment

1. **Apply migration during maintenance window**
2. **Test with sample tenant data**
3. **Verify no cross-tenant pattern leakage**
4. **Monitor learning accuracy per tenant**
5. **Set up alerts for tenant_id validation failures**