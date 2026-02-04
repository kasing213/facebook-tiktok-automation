# Test Screenshot Fixtures

This directory contains payment screenshot images for testing the OCR authentication system.

## Test Screenshots

### Valid Payment Screenshots
- `valid_payment_100_khr.png` - Clear payment of 100,000 KHR
- `valid_payment_500_usd.png` - Clear payment of 500 USD
- `valid_bank_transfer.png` - Bank transfer screenshot with clear details

### Edge Case Screenshots
- `blurry_payment.jpg` - Unclear/blurry image for testing low confidence
- `wrong_amount.png` - Payment with amount that doesn't match expected
- `partial_screenshot.png` - Cropped or incomplete payment image
- `non_payment_image.png` - Non-payment image for negative testing

## Expected OCR Results

Each screenshot should be tested with known expected results:

### valid_payment_100_khr.png
```json
{
  "amount": 100000,
  "currency": "KHR",
  "confidence": 0.95,
  "bank": "ABA Bank",
  "recipient": "Test Merchant"
}
```

### valid_payment_500_usd.png
```json
{
  "amount": 500,
  "currency": "USD",
  "confidence": 0.92,
  "bank": "ACLEDA Bank",
  "recipient": "Test Business"
}
```

## Usage in Tests

```python
def load_test_screenshot(filename: str) -> bytes:
    """Load test screenshot from fixtures."""
    path = Path(__file__).parent / "fixtures" / "screenshots" / filename
    return path.read_bytes()

# Example usage
screenshot_data = load_test_screenshot("valid_payment_100_khr.png")
```

## Creating New Test Screenshots

When adding new test screenshots:
1. Use realistic payment screenshots (anonymized)
2. Include variety of banks, amounts, currencies
3. Test both clear and problematic images
4. Document expected OCR results
5. Ensure images are reasonably sized (< 5MB each)