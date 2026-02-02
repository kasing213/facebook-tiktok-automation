# Payment Screenshot Test Files

This directory contains mock payment screenshots for OCR testing. In a real beta test, these would be actual bank transfer screenshots from different Cambodian banks.

## Test Files Structure

- `payment_success_aba.png` - Valid ABA Bank payment screenshot
- `payment_success_acleda.png` - Valid ACLEDA Bank payment screenshot
- `payment_partial.png` - Partial payment screenshot (should not auto-approve)
- `payment_wrong_bank.png` - Wrong bank account screenshot (should reject)
- `payment_blurry.png` - Low quality image (should have low OCR confidence)
- `payment_foreign.png` - Non-Cambodian bank (should reject)

## OCR Test Scenarios

Each file tests different OCR confidence levels and approval logic:

1. **High Confidence (85%+)**: Clear screenshots with correct details → Auto-approve
2. **Medium Confidence (70-84%)**: Readable but not perfect → Manual review
3. **Low Confidence (<70%)**: Blurry/unclear → Reject automatically
4. **Wrong Details**: Clear image but wrong bank/amount → Reject

## Usage in Tests

```typescript
await page.setInputFiles('input[type="file"]', 'e2e/fixtures/payment-screenshots/payment_success_aba.png');
```

Note: For actual beta testing, replace these placeholder files with real bank screenshot examples (with sensitive data redacted).