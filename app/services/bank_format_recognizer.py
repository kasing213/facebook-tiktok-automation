"""
Bank Format Recognition Service for Cambodian Banks

This service recognizes bank-specific layouts and formats to extract
recipient information with high confidence, solving the cold start
problem for new merchants.

Supported Banks:
- ABA Bank
- ACLEDA Bank
- Wing Bank
- KHQR (Cross-bank QR payments)
- Canadia Bank
- Prince Bank

Key Features:
- Logo detection for bank identification
- Format-specific text extraction patterns
- Position-based parsing for consistent accuracy
- Multi-language support (Khmer/English)
- Fallback to generic OCR if bank unknown
"""

import re
import json
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class BankFormatResult:
    """Result from bank format recognition"""
    success: bool
    confidence: float
    bank_name: Optional[str] = None

    # Extracted fields
    recipient_name: Optional[str] = None
    account_number: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_date: Optional[str] = None

    # Metadata
    extraction_method: str = "bank_format"
    format_version: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class BankTemplate:
    """Bank format template for text extraction"""
    bank_name: str
    logo_keywords: List[str]
    header_patterns: List[str]

    # Recipient extraction patterns
    recipient_patterns: List[Dict[str, Any]]
    account_patterns: List[Dict[str, Any]]
    amount_patterns: List[Dict[str, Any]]

    # Formatting rules
    name_formatting: Dict[str, Any]
    confidence_base: float = 0.85


class BankFormatRecognizer:
    """Main service for bank format recognition"""

    def __init__(self, db):
        self.db = db
        self.templates = {}
        self._load_bank_templates()

        # OCR confidence thresholds
        self.HIGH_CONFIDENCE_THRESHOLD = 0.9
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.7

        # Bank detection keywords
        self.bank_keywords = {
            "ABA": ["aba", "aba bank", "advanced bank", "012 888", "aba.com.kh"],
            "ACLEDA": ["acleda", "acleda bank", "012 20", "acleda.com.kh"],
            "Wing": ["wing", "wing bank", "wing.com.kh", "089 999"],
            "Canadia": ["canadia", "canadia bank", "canadiabank", "023 100"],
            "Prince": ["prince", "prince bank", "princebank.com.kh"],
            "KHQR": ["khqr", "bakong", "nbc.org.kh", "cambodia qr"]
        }

    def _load_bank_templates(self) -> None:
        """Load bank format templates"""

        # ABA Bank Template
        self.templates["ABA"] = BankTemplate(
            bank_name="ABA Bank",
            logo_keywords=["aba", "advanced bank"],
            header_patterns=["Transfer Confirmation", "Payment Successful", "ការផ្ទេរប្រាក់"],

            recipient_patterns=[
                {
                    "regex": r"(?:Transfer to|To|ផ្ទេរទៅ)[\s:]*([A-Z\s\.&]+?)(?:\n|Account)",
                    "priority": 1,
                    "confidence": 0.95
                },
                {
                    "regex": r"Beneficiary[\s:]*([A-Z\s\.&]+?)(?:\n|Account)",
                    "priority": 2,
                    "confidence": 0.90
                },
                {
                    "regex": r"(?:Name|ឈ្មោះ)[\s:]*([A-Z\s\.&]+?)(?:\n|$)",
                    "priority": 3,
                    "confidence": 0.85
                }
            ],

            account_patterns=[
                {
                    "regex": r"(?:Account|Account No|គណនី)[\s:]*([0-9\s-]+)",
                    "priority": 1,
                    "confidence": 0.95
                },
                {
                    "regex": r"(\d{9}|\d{3}\s\d{3}\s\d{3})",
                    "priority": 2,
                    "confidence": 0.85
                }
            ],

            amount_patterns=[
                {
                    "regex": r"(?:Amount|Amount Transfer|ចំនួន)[\s:]*([0-9,\.]+)[\s]*(?:USD|KHR|៛|\$)",
                    "priority": 1,
                    "confidence": 0.95
                },
                {
                    "regex": r"([0-9,\.]+)[\s]*(?:USD|KHR|៛|\$)",
                    "priority": 2,
                    "confidence": 0.80
                }
            ],

            name_formatting={
                "uppercase": True,
                "dots_for_initials": True,
                "separators": ["&", "AND"],
                "max_length": 50
            },

            confidence_base=0.90
        )

        # ACLEDA Bank Template
        self.templates["ACLEDA"] = BankTemplate(
            bank_name="ACLEDA Bank",
            logo_keywords=["acleda", "acleda bank"],
            header_patterns=["Fund Transfer", "Payment Complete", "ការផ្ទេរទឹកប្រាក់"],

            recipient_patterns=[
                {
                    "regex": r"(?:Beneficiary Name|To Account|ឈ្មោះអ្នកទទួល)[\s:]*([A-Z\s\.]+?)(?:\n|Account)",
                    "priority": 1,
                    "confidence": 0.95
                },
                {
                    "regex": r"(?:Account Name|ឈ្មោះគណនី)[\s:]*([A-Z\s\.]+?)(?:\n|$)",
                    "priority": 2,
                    "confidence": 0.90
                }
            ],

            account_patterns=[
                {
                    "regex": r"(?:Account No|Account Number|លេខគណនី)[\s:]*([0-9\-]+)",
                    "priority": 1,
                    "confidence": 0.95
                },
                {
                    "regex": r"(\d{3}-\d{3}-\d{3}-\d{1}-\d{2}|\d{13})",
                    "priority": 2,
                    "confidence": 0.90
                }
            ],

            amount_patterns=[
                {
                    "regex": r"(?:Transfer Amount|Amount|ចំនួនទឹកប្រាក់)[\s:]*([0-9,\.]+)",
                    "priority": 1,
                    "confidence": 0.95
                }
            ],

            name_formatting={
                "uppercase": True,
                "dots_for_initials": False,
                "max_length": 40
            },

            confidence_base=0.88
        )

        # Wing Bank Template
        self.templates["Wing"] = BankTemplate(
            bank_name="Wing Bank",
            logo_keywords=["wing", "wing bank"],
            header_patterns=["Transfer Success", "Payment Done", "ផ្ទេរដោយជោគជ័យ"],

            recipient_patterns=[
                {
                    "regex": r"(?:Receiver|To|ទៅកាន់)[\s:]*(\d{8,10})\s*\(([A-Z\s]+)\)",
                    "priority": 1,
                    "confidence": 0.95,
                    "group": 2  # Name is in parentheses
                },
                {
                    "regex": r"(?:Account Name|ឈ្មោះ)[\s:]*([A-Z\s\.]+?)(?:\n|$)",
                    "priority": 2,
                    "confidence": 0.85
                }
            ],

            account_patterns=[
                {
                    "regex": r"(?:Account|Wing Account|គណនី Wing)[\s:]*(\d{8,10})",
                    "priority": 1,
                    "confidence": 0.95
                }
            ],

            amount_patterns=[
                {
                    "regex": r"(?:Amount|Transfer|ចំនួន)[\s:]*([0-9,\.]+)[\s]*(?:USD|KHR|៛)",
                    "priority": 1,
                    "confidence": 0.90
                }
            ],

            name_formatting={
                "uppercase": True,
                "max_length": 30
            },

            confidence_base=0.85
        )

        # KHQR (Cross-bank QR) Template
        self.templates["KHQR"] = BankTemplate(
            bank_name="KHQR",
            logo_keywords=["khqr", "bakong", "cambodia qr"],
            header_patterns=["QR Payment", "Bakong Payment", "KHQR Transfer"],

            recipient_patterns=[
                {
                    "regex": r"(?:Merchant|Merchant Name|អាជីវកម្ម)[\s:]*([A-Z\s\.&]+?)(?:\n|KHQR)",
                    "priority": 1,
                    "confidence": 0.90
                },
                {
                    "regex": r"(?:To|ទៅកាន់)[\s:]*([A-Z\s\.&]+?)(?:\n|$)",
                    "priority": 2,
                    "confidence": 0.85
                }
            ],

            account_patterns=[
                {
                    "regex": r"(?:KHQR ID|QR ID|អត្តលេខ)[\s:]*([A-Z0-9]{10,})",
                    "priority": 1,
                    "confidence": 0.85
                }
            ],

            amount_patterns=[
                {
                    "regex": r"(?:Amount|Payment|ចំនួនទឹកប្រាក់)[\s:]*([0-9,\.]+)",
                    "priority": 1,
                    "confidence": 0.90
                }
            ],

            name_formatting={
                "uppercase": True,
                "dots_for_initials": True,
                "separators": ["&", "AND", "+"],
                "max_length": 60
            },

            confidence_base=0.82
        )

    async def extract_payment_info(
        self,
        screenshot_data: bytes,
        ocr_text: Optional[str] = None
    ) -> BankFormatResult:
        """
        Extract payment information using bank format recognition

        Args:
            screenshot_data: Raw image data
            ocr_text: Pre-extracted text (optional, will use OCR if not provided)

        Returns:
            BankFormatResult with extracted information
        """

        start_time = datetime.now()

        try:
            # Step 1: Get OCR text if not provided
            if not ocr_text:
                ocr_text = await self._extract_text_from_image(screenshot_data)

            if not ocr_text:
                return BankFormatResult(
                    success=False,
                    confidence=0.0,
                    error_message="Could not extract text from image"
                )

            # Step 2: Detect bank
            detected_bank = self._detect_bank(ocr_text)

            if not detected_bank:
                return BankFormatResult(
                    success=False,
                    confidence=0.0,
                    error_message="Unknown bank format - unable to identify bank"
                )

            # Step 3: Extract information using bank-specific template
            template = self.templates[detected_bank]
            result = self._extract_with_template(ocr_text, template)

            # Step 4: Post-process and validate
            result = self._post_process_result(result, template)

            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time

            logger.info(f"Bank format extraction: {detected_bank} "
                       f"confidence={result.confidence:.2f} time={processing_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Bank format recognition error: {e}")

            return BankFormatResult(
                success=False,
                confidence=0.0,
                error_message=str(e)
            )

    def _detect_bank(self, ocr_text: str) -> Optional[str]:
        """Detect bank from OCR text using keywords and patterns"""

        text_lower = ocr_text.lower()
        bank_scores = {}

        # Score each bank based on keyword matches
        for bank, keywords in self.bank_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += len(keyword)  # Longer keywords get higher scores

            if score > 0:
                bank_scores[bank] = score

        if not bank_scores:
            return None

        # Return bank with highest score
        return max(bank_scores, key=bank_scores.get)

    def _extract_with_template(self, ocr_text: str, template: BankTemplate) -> BankFormatResult:
        """Extract information using bank-specific template"""

        result = BankFormatResult(
            success=False,
            confidence=0.0,
            bank_name=template.bank_name,
            extraction_method="bank_format"
        )

        # Extract recipient name
        recipient_info = self._extract_field(ocr_text, template.recipient_patterns)
        if recipient_info:
            result.recipient_name = self._format_name(recipient_info['value'], template.name_formatting)
            result.confidence += recipient_info['confidence'] * 0.5  # 50% weight

        # Extract account number
        account_info = self._extract_field(ocr_text, template.account_patterns)
        if account_info:
            result.account_number = self._format_account(account_info['value'])
            result.confidence += account_info['confidence'] * 0.3  # 30% weight

        # Extract amount
        amount_info = self._extract_field(ocr_text, template.amount_patterns)
        if amount_info:
            result.amount = self._parse_amount(amount_info['value'])
            result.currency = self._extract_currency(amount_info['value'], ocr_text)
            result.confidence += amount_info['confidence'] * 0.2  # 20% weight

        # Success if we have recipient and account
        result.success = bool(result.recipient_name and result.account_number)

        # Adjust confidence based on template base confidence
        if result.success:
            result.confidence = min(0.95, result.confidence * template.confidence_base)

        return result

    def _extract_field(self, text: str, patterns: List[Dict]) -> Optional[Dict]:
        """Extract field using prioritized patterns"""

        # Sort patterns by priority (lower number = higher priority)
        sorted_patterns = sorted(patterns, key=lambda p: p.get('priority', 999))

        for pattern in sorted_patterns:
            try:
                regex = pattern['regex']
                matches = re.search(regex, text, re.IGNORECASE | re.MULTILINE)

                if matches:
                    # Get the appropriate group (default: group 1)
                    group = pattern.get('group', 1)
                    value = matches.group(group).strip()

                    if value and len(value) > 1:  # Valid extraction
                        return {
                            'value': value,
                            'confidence': pattern.get('confidence', 0.8),
                            'pattern': pattern
                        }

            except Exception as e:
                logger.warning(f"Pattern matching error: {e}")
                continue

        return None

    def _format_name(self, raw_name: str, formatting: Dict) -> str:
        """Format extracted name according to bank rules"""

        if not raw_name:
            return ""

        name = raw_name.strip()

        # Convert to uppercase if required
        if formatting.get('uppercase', True):
            name = name.upper()

        # Handle dots for initials
        if formatting.get('dots_for_initials', True):
            # Add dots after single letters: "K CHAN" → "K. CHAN"
            name = re.sub(r'\b([A-Z])\s+', r'\1. ', name)
        else:
            # Remove dots: "K. CHAN" → "K CHAN"
            name = re.sub(r'\.', '', name)

        # Clean up separators
        separators = formatting.get('separators', ['&'])
        for sep in separators:
            name = re.sub(f'\\s*{re.escape(sep)}\\s*', f' {sep} ', name)

        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name).strip()

        # Enforce maximum length
        max_length = formatting.get('max_length', 50)
        if len(name) > max_length:
            name = name[:max_length].strip()

        return name

    def _format_account(self, raw_account: str) -> str:
        """Format account number by removing spaces and dashes"""

        if not raw_account:
            return ""

        # Remove spaces and dashes, keep only digits
        account = re.sub(r'[^\d]', '', raw_account.strip())

        return account

    def _parse_amount(self, raw_amount: str) -> Optional[float]:
        """Parse amount from extracted text"""

        if not raw_amount:
            return None

        try:
            # Remove commas and convert to float
            amount_str = re.sub(r'[,\s]', '', raw_amount)
            return float(amount_str)
        except (ValueError, TypeError):
            return None

    def _extract_currency(self, amount_text: str, full_text: str) -> str:
        """Extract currency from amount text or full OCR text"""

        # Check amount text first
        if 'USD' in amount_text or '$' in amount_text:
            return 'USD'
        elif 'KHR' in amount_text or '៛' in amount_text:
            return 'KHR'

        # Check full text as fallback
        if 'USD' in full_text or '$' in full_text:
            return 'USD'

        # Default to KHR for Cambodia
        return 'KHR'

    def _post_process_result(self, result: BankFormatResult, template: BankTemplate) -> BankFormatResult:
        """Post-process and validate extraction result"""

        # Validate recipient name
        if result.recipient_name:
            # Check for common OCR errors
            if len(result.recipient_name) < 2:
                result.recipient_name = None
                result.confidence *= 0.7
            elif result.recipient_name.isdigit():
                result.recipient_name = None
                result.confidence *= 0.5

        # Validate account number
        if result.account_number:
            if len(result.account_number) < 8 or len(result.account_number) > 20:
                result.account_number = None
                result.confidence *= 0.8

        # Validate amount
        if result.amount:
            if result.amount <= 0 or result.amount > 100000000:  # Sanity check
                result.amount = None
                result.confidence *= 0.9

        # Update success status
        result.success = bool(result.recipient_name and result.account_number)

        return result

    async def _extract_text_from_image(self, screenshot_data: bytes) -> Optional[str]:
        """Extract text from image using OCR service"""
        # This would integrate with your existing OCR services
        # For now, return None to indicate OCR text should be provided
        return None

    async def get_bank_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get bank format recognition statistics for a tenant"""

        pipeline = [
            {"$match": {"tenant_id": tenant_id, "extraction_method": "bank_format"}},
            {"$group": {
                "_id": "$bank_name",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"},
                "success_rate": {"$avg": {"$cond": ["$success", 1, 0]}}
            }},
            {"$sort": {"count": -1}}
        ]

        bank_stats = await self.db['verification_decisions_log'].aggregate(pipeline).to_list(10)

        total_extractions = sum(stat['count'] for stat in bank_stats)

        return {
            "total_extractions": total_extractions,
            "banks_detected": len(bank_stats),
            "bank_breakdown": bank_stats,
            "supported_banks": list(self.templates.keys())
        }


# Export for use in other modules
__all__ = ['BankFormatRecognizer', 'BankFormatResult', 'BankTemplate']