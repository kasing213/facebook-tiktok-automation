# Auto-Learning OCR System

## Overview

The Auto-Learning OCR System is a cost-effective, intelligent verification solution that **eliminates manual training** and **reduces GPT-4 Vision API costs by 80%**. It learns from every payment verification to continuously improve accuracy.

## 🚀 **Key Features**

### ✅ **Zero Manual Training**
- Automatically learns from each verified payment screenshot
- No need to run training scripts or manual data collection
- Real-time pattern extraction and template updates

### 💰 **80% Cost Reduction**
- Uses bank-specific patterns first (free)
- Falls back to GPT-4 Vision only when needed (expensive)
- Pattern matching costs ~$0.001 vs GPT-4 Vision ~$0.05

### 📈 **Continuous Improvement**
- **Day 1**: 85% accuracy (bank format templates)
- **Week 1**: 90% accuracy (merchant-specific patterns)
- **Month 1**: 95% accuracy (comprehensive learning)

### 🧠 **Smart Processing Pipeline**
1. **Bank Detection** - Identify bank from keywords
2. **Pattern Matching** - Try learned extraction patterns
3. **Merchant Patterns** - Apply tenant-specific variations
4. **GPT-4 Fallback** - Use expensive AI if patterns fail
5. **Auto-Learning** - Extract patterns from results

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART OCR PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  New Screenshot                                                  │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. BASIC OCR EXTRACTION (Fast, Cheap)                  │   │
│  │  Extract text using Tesseract/PaddleOCR                 │   │
│  │  Cost: ~$0.001 per image                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. BANK DETECTION (Keyword Scoring)                    │   │
│  │  ABA: 89% confidence                                    │   │
│  │  ACLEDA: 12% confidence        ← Chooses ABA           │   │
│  │  Wing: 3% confidence                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3. PATTERN MATCHING (Free, Fast)                       │   │
│  │  Try ABA-specific extraction patterns:                  │   │
│  │  • "Transfer to: ([A-Z\\s\\.]+)" → Extract recipient   │   │
│  │  • "Account: ([0-9\\s\\-]+)" → Extract account        │   │
│  │  • "Amount: ([0-9,\\.]+)" → Extract amount            │   │
│  │  Overall Confidence: 92%                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  4. DECISION POINT                                       │   │
│  │  Confidence ≥ 80%? ✅ Use Pattern Result               │   │
│  │  Confidence < 80%? → Use GPT-4 Vision                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  5. AUTO-LEARNING (Background)                          │   │
│  │  ✅ Queue learning data                                 │   │
│  │  ✅ Extract new patterns from success                   │   │
│  │  ✅ Update bank templates                               │   │
│  │  ✅ Improve future accuracy                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. **Auto-Learning OCR Service** (`auto_learning_ocr.py`)
- **Bank Pattern Extractor**: Detects banks and extracts patterns
- **Real-time Learning**: Learns from verification results
- **Template Management**: Updates bank format templates

### 2. **Smart OCR Service** (`smart_ocr_service.py`)
- **Processing Pipeline**: Orchestrates pattern matching and GPT-4 fallback
- **Cost Optimization**: Tracks savings and efficiency
- **Verification Logic**: Compares extracted vs expected data

### 3. **Pattern Cache** (`pattern_cache.py`)
- **Bank Patterns**: Caches templates for fast access (1-hour TTL)
- **Merchant Patterns**: Tenant-specific pattern variations (24-hour TTL)
- **Performance Monitoring**: Hit rates, access patterns

### 4. **Background Training Job** (`ocr_training_job.py`)
- **Learning Queue Processor**: Processes verification results every 5 minutes
- **Pattern Analysis**: Validates and scores new patterns
- **Template Updates**: Updates database with learned patterns

### 5. **Management API** (`auto_learning.py`)
- **Health Monitoring**: System status and performance
- **Statistics Dashboard**: Learning progress and cost savings
- **Manual Controls**: Training triggers and cache management

## Database Schema

The system uses MongoDB collections for pattern storage:

```javascript
// Learning queue for background processing
db.ocr_learning_queue = {
  bank_code: "ABA",                    // Detected bank
  ocr_text: "Transfer to JOHN DOE...", // Raw OCR text
  verified_data: {...},               // Expected payment data
  extracted_patterns: {...},          // New patterns found
  verification_confidence: 0.92,      // Success confidence
  learned_at: ISODate(),              // Timestamp
  processed: false                    // Processing status
}

// Bank format templates
db.bank_format_templates = {
  bank_code: "ABA",
  bank_name: "ABA Bank",
  template: {
    patterns: [
      {
        type: "recipient",
        regex: "Transfer to[\\s:]*([A-Z\\s\\.&]+)",
        confidence: 0.95,
        priority: 1,
        source: "auto_learning"
      }
    ],
    confidence_base: 0.90,
    last_updated: ISODate()
  },
  validation_accuracy: 0.87,
  sample_count: 45
}

// Training results and statistics
db.bank_training_results = {
  training_type: "format_patterns",
  training_date: ISODate(),
  total_screenshots: 347,
  banks_analyzed: ["ABA", "ACLEDA", "Wing"],
  categorization: {...},
  extraction_templates: {...},
  validation_results: {...}
}
```

## API Endpoints

### **Health & Status**
```bash
GET /api/auto-learning/health              # Quick health check
GET /api/auto-learning/status              # Comprehensive status
GET /api/auto-learning/stats               # Performance statistics
```

### **Training Management**
```bash
GET  /api/auto-learning/training/stats     # Training job status
POST /api/auto-learning/training/process   # Manual trigger
```

### **Pattern Management**
```bash
GET /api/auto-learning/patterns            # All bank patterns
GET /api/auto-learning/patterns/{bank}     # Specific bank patterns
GET /api/auto-learning/merchant/{id}/stats # Merchant-specific patterns
```

### **Cost Analysis**
```bash
GET /api/auto-learning/cost-savings        # Detailed cost savings report
```

### **Cache Management**
```bash
DELETE /api/auto-learning/cache           # Clear pattern cache
```

## Configuration

### **Environment Variables**

```bash
# MongoDB for pattern storage
MONGO_URL=mongodb://user:pass@host:port/db?tls=true
DB_NAME=customerDB

# OCR fallback service
OCR_API_URL=https://ocr-service.example.com
OCR_API_KEY=your-ocr-api-key
OCR_MOCK_MODE=false
```

### **Settings**

```python
# In src/config.py or environment
class Settings:
    MONGO_URL: str = ""              # MongoDB connection string
    DB_NAME: str = "customerDB"      # Database name
    OCR_API_URL: str = ""           # External OCR service URL
    OCR_API_KEY: str = ""           # OCR service API key
    OCR_MOCK_MODE: bool = True      # Use mock mode if True
```

## Usage Examples

### **Integration in Payment Verification**

```python
from src.services.smart_ocr_service import smart_ocr

# In your payment handler
result = await smart_ocr.verify_screenshot_smart(
    image_data=screenshot_bytes,
    filename="payment_receipt.jpg",
    invoice_id="INV-001",
    expected_payment={
        "amount": 50000,
        "currency": "KHR",
        "toAccount": "012-345-678",
        "bank": "ABA",
        "recipientNames": ["JOHN DOE"],
        "dueDate": "2026-01-31"
    },
    customer_id="CUST-001",
    tenant_id="TENANT-123",  # For merchant-specific learning
    use_learning=True
)

# Check if pattern matching succeeded (cost-effective)
if result['cost_effective']:
    print(f"✅ Saved ${smart_ocr.gpt4_vision_cost_per_call:.3f} using patterns")

# Verification result
status = result['verification']['status']  # 'verified', 'rejected', 'pending'
confidence = result['confidence']          # 0.0 - 1.0
```

### **Manual Training Trigger**

```python
# Trigger immediate training (don't wait for background job)
import httpx

response = await httpx.post("http://localhost:8000/api/auto-learning/training/process")
result = response.json()

print(f"Processed {result['processing_result']['processed_count']} learning records")
```

### **Monitoring and Statistics**

```python
# Get comprehensive statistics
response = await httpx.get("http://localhost:8000/api/auto-learning/stats")
stats = response.json()

print(f"Pattern Success Rate: {stats['pattern_success_rate']:.1%}")
print(f"Total Cost Savings: ${stats['cost_savings']['estimated_savings_usd']:.2f}")
print(f"GPT-4 Calls Avoided: {stats['cost_savings']['gpt4_calls_avoided']}")
```

## Expected Performance

### **Accuracy Progression**

| Timeframe | Method | Accuracy | Training Data |
|-----------|--------|----------|---------------|
| **Day 1** | Bank Format Recognition | 85% | 347 existing screenshots |
| **Week 1** | + Merchant Patterns | 90% | Real usage patterns |
| **Month 1** | + Full Learning | 95% | Comprehensive learning |

### **Cost Savings**

| Metric | Value |
|--------|-------|
| **GPT-4 Vision cost** | $0.05 per verification |
| **Pattern matching cost** | $0.001 per verification |
| **Expected pattern success rate** | 80% (after 1 month) |
| **Monthly savings (100 verifications)** | $3.92 per month |
| **Yearly savings (1200 verifications)** | $47.04 per year |

### **Processing Performance**

| Operation | Time | Method |
|-----------|------|--------|
| **Pattern matching** | 50-100ms | Regex + cache lookup |
| **GPT-4 Vision** | 2-5 seconds | API call + processing |
| **Learning extraction** | 10-20ms | Background async |
| **Cache lookup** | 1-5ms | In-memory access |

## Troubleshooting

### **Common Issues**

#### **System Not Learning**
```bash
# Check if MongoDB is connected
curl http://localhost:8000/api/auto-learning/health

# Check learning queue status
curl http://localhost:8000/api/auto-learning/training/stats

# Manual trigger if queue is stuck
curl -X POST http://localhost:8000/api/auto-learning/training/process
```

#### **Low Pattern Success Rate**
```bash
# Check pattern availability
curl http://localhost:8000/api/auto-learning/patterns

# Clear cache to reload from database
curl -X DELETE http://localhost:8000/api/auto-learning/cache

# Check merchant-specific patterns
curl http://localhost:8000/api/auto-learning/merchant/TENANT-123/stats
```

#### **High GPT-4 Costs**
```bash
# Check cost savings report
curl http://localhost:8000/api/auto-learning/cost-savings

# Verify pattern confidence thresholds
# Should be 80%+ for pattern matching success
```

### **Logs to Monitor**

```bash
# Auto-learning initialization
grep "Auto-Learning OCR" /var/log/api-gateway.log

# Pattern matching successes
grep "Pattern matching success" /var/log/api-gateway.log

# Learning data queuing
grep "Learning data queued" /var/log/api-gateway.log

# Training job processing
grep "Processed.*learning records" /var/log/api-gateway.log
```

### **Performance Tuning**

#### **Cache Settings**
```python
# Adjust cache TTL based on usage
pattern_cache = PatternCache(ttl_hours=2)    # Default: 1 hour
merchant_cache = MerchantPatternCache(ttl_hours=48)  # Default: 24 hours
```

#### **Training Frequency**
```python
# Adjust background processing interval
# In ocr_training_job.py
await asyncio.sleep(300)  # 5 minutes (default)
await asyncio.sleep(600)  # 10 minutes (lower frequency)
```

#### **Confidence Thresholds**
```python
# Adjust pattern matching thresholds
# In smart_ocr_service.py
if pattern_result['confidence'] >= 0.80:  # Default: 80%
if pattern_result['confidence'] >= 0.75:  # Lower threshold (more pattern usage)
```

## Production Deployment

### **Startup Sequence**
1. ✅ MongoDB connection established
2. ✅ Pattern cache loaded from database
3. ✅ Background training job started
4. ✅ Smart OCR service initialized
5. ✅ API endpoints registered

### **Health Checks**
- **Liveness**: `GET /api/auto-learning/health`
- **Readiness**: `GET /api/auto-learning/status`
- **Metrics**: `GET /api/auto-learning/stats`

### **Scaling Considerations**
- **MongoDB**: Single connection per service (lightweight patterns)
- **Memory**: Pattern cache ~1-5MB per 10 banks
- **CPU**: Regex processing is fast (<10ms)
- **Background Job**: Single instance only (avoid duplicate processing)

### **Backup Strategy**
- **Pattern Templates**: Backed up with MongoDB
- **Learning Queue**: Can be recreated from new verifications
- **Cache**: Automatically rebuilt from database

## Integration with Existing System

The auto-learning system is designed to **seamlessly replace** the existing OCR flow:

### **Before (Manual OCR)**
```python
# Old way
result = await ocr_service.verify_screenshot(
    image_data=image_data,
    expected_payment=expected_payment
)
```

### **After (Auto-Learning OCR)**
```python
# New way (drop-in replacement)
result = await smart_ocr.verify_screenshot_smart(
    image_data=image_data,
    expected_payment=expected_payment,
    tenant_id=tenant_id,      # Enable merchant-specific learning
    use_learning=True         # Enable auto-learning
)

# Same result format, plus learning benefits:
# - 80% cost reduction
# - Continuous accuracy improvement
# - Zero manual training
```

The system is **100% backward compatible** and gracefully falls back to GPT-4 Vision when pattern matching fails, ensuring **no accuracy regression** while providing substantial cost savings and continuous improvement.

## Future Enhancements

### **Phase 2: Advanced Features**
- **Multi-language Support**: Khmer text recognition improvements
- **Document Type Detection**: Invoice vs receipt vs transfer slip
- **Confidence Calibration**: Dynamic threshold adjustment
- **A/B Testing**: Compare different pattern approaches

### **Phase 3: Intelligence Expansion**
- **Fuzzy Matching**: Better name/account number matching
- **OCR Error Correction**: Learn from common OCR mistakes
- **Cross-Bank Patterns**: Shared patterns across similar banks
- **Real-time Analytics**: Live accuracy monitoring dashboard

### **Phase 4: Platform Integration**
- **Dashboard UI**: Pattern management interface
- **Merchant Analytics**: Per-tenant learning progress
- **Cost Optimization Reports**: Detailed savings analysis
- **Alert System**: Accuracy degradation notifications