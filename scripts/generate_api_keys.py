#!/usr/bin/env python3
"""
Script to generate secure API keys for Facebook-automation services.
Generates new INVOICE_API_KEY and OCR_API_KEY with cryptographically secure randomness.
"""

import secrets
import base64
import hashlib
from datetime import datetime
import sys


def generate_secure_api_key(service_name: str, length: int = 40) -> str:
    """
    Generate a secure API key with service prefix.

    Args:
        service_name: Name of the service (invoice, ocr)
        length: Length of the random part (default: 40 chars)

    Returns:
        Secure API key in format: {service}_api_{random_string}
    """
    # Generate cryptographically secure random bytes
    random_bytes = secrets.token_bytes(length)

    # Convert to URL-safe base64 string
    random_string = base64.urlsafe_b64encode(random_bytes).decode('ascii')

    # Remove padding characters and truncate to desired length
    random_string = random_string.replace('=', '')[:length]

    # Create API key with service prefix
    api_key = f"{service_name}_api_{random_string}"

    return api_key


def generate_secure_secret_key(purpose: str, length: int = 32) -> str:
    """
    Generate a secure secret key for encryption/signing.

    Args:
        purpose: Purpose of the key (jwt, encrypt, etc.)
        length: Length in bytes (default: 32 bytes = 256 bits)

    Returns:
        Base64-encoded secure secret key
    """
    # Generate cryptographically secure random bytes
    secret_bytes = secrets.token_bytes(length)

    # Convert to base64 for easy storage
    secret_key = base64.urlsafe_b64encode(secret_bytes).decode('ascii')

    return secret_key


def validate_key_strength(key: str) -> dict:
    """
    Validate the strength of generated keys.

    Args:
        key: The key to validate

    Returns:
        Dictionary with validation results
    """
    results = {
        'length': len(key),
        'has_numbers': any(c.isdigit() for c in key),
        'has_letters': any(c.isalpha() for c in key),
        'has_special': any(c in '-_' for c in key),
        'entropy_bits': len(key) * 6,  # Rough estimate for base64
        'strength': 'weak'
    }

    if results['length'] >= 32 and results['entropy_bits'] >= 192:
        if results['has_numbers'] and results['has_letters']:
            results['strength'] = 'strong'
        else:
            results['strength'] = 'medium'

    return results


def main():
    """Generate secure API keys for the Facebook-automation project."""

    print("🔐 Facebook-automation API Key Generator")
    print("=" * 50)
    print(f"Generated on: {datetime.now().isoformat()}")
    print()

    # Generate the two required API keys
    print("📋 Generating secure API keys...")
    print()

    # 1. Invoice API Key
    invoice_api_key = generate_secure_api_key("invoice", length=40)
    invoice_validation = validate_key_strength(invoice_api_key)

    print("1️⃣ INVOICE API KEY:")
    print(f"   Key: {invoice_api_key}")
    print(f"   Length: {invoice_validation['length']} characters")
    print(f"   Entropy: ~{invoice_validation['entropy_bits']} bits")
    print(f"   Strength: {invoice_validation['strength'].upper()}")
    print()

    # 2. OCR API Key
    ocr_api_key = generate_secure_api_key("ocr", length=40)
    ocr_validation = validate_key_strength(ocr_api_key)

    print("2️⃣ OCR API KEY:")
    print(f"   Key: {ocr_api_key}")
    print(f"   Length: {ocr_validation['length']} characters")
    print(f"   Entropy: ~{ocr_validation['entropy_bits']} bits")
    print(f"   Strength: {ocr_validation['strength'].upper()}")
    print()

    # Generate bonus secure secret keys for future use
    print("🎁 BONUS: Additional secure keys for future service isolation...")
    print()

    jwt_secret = generate_secure_secret_key("jwt", 32)
    encrypt_secret = generate_secure_secret_key("encrypt", 32)

    print("3️⃣ JWT SECRET KEY (for future service-to-service auth):")
    print(f"   Key: {jwt_secret}")
    print(f"   Purpose: JWT token signing/validation")
    print(f"   Length: 44 characters (256-bit)")
    print()

    print("4️⃣ ENCRYPTION SECRET KEY (for sensitive data):")
    print(f"   Key: {encrypt_secret}")
    print(f"   Purpose: Symmetric encryption of sensitive data")
    print(f"   Length: 44 characters (256-bit)")
    print()

    # Configuration output
    print("⚙️ CONFIGURATION")
    print("=" * 50)
    print("Add these to your Railway environment variables:")
    print()
    print("# Core API Keys (REPLACE EXISTING VALUES)")
    print(f"INVOICE_API_KEY={invoice_api_key}")
    print(f"OCR_API_KEY={ocr_api_key}")
    print()
    print("# Future Service Keys (NEW - for enhanced security)")
    print(f"SERVICE_JWT_SECRET={jwt_secret}")
    print(f"SERVICE_ENCRYPT_SECRET={encrypt_secret}")
    print()

    # Security recommendations
    print("🛡️ SECURITY RECOMMENDATIONS")
    print("=" * 50)
    print("1. Store these keys securely - never commit to git")
    print("2. Update Railway environment variables immediately")
    print("3. Rotate keys every 90 days for maximum security")
    print("4. Use different keys for development/staging/production")
    print("5. Monitor API key usage in application logs")
    print()

    # Generate key hashes for verification (first 8 chars)
    invoice_hash = hashlib.sha256(invoice_api_key.encode()).hexdigest()[:8]
    ocr_hash = hashlib.sha256(ocr_api_key.encode()).hexdigest()[:8]

    print("🔍 KEY VERIFICATION HASHES")
    print("=" * 50)
    print("Use these to verify keys are correctly configured:")
    print(f"INVOICE_API_KEY hash: {invoice_hash}...")
    print(f"OCR_API_KEY hash: {ocr_hash}...")
    print()

    print("✅ Key generation completed successfully!")
    print("🚀 Ready to update your Railway configuration!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Key generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error generating keys: {e}")
        sys.exit(1)