# api-gateway/src/services/smart_ocr_service.py
"""
Smart OCR Service with Auto-Learning

This service integrates the auto-learning OCR system with the existing
verification flow. It tries bank patterns first, falls back to GPT-4 Vision
only when needed, and learns from every verification to improve accuracy.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from src.services.ocr_service import ocr_service  # Original OCR service
from src.services.auto_learning_ocr import auto_learning_ocr
from src.services.pattern_cache import pattern_cache, merchant_cache
from src.jobs.ocr_training_job import training_scheduler

logger = logging.getLogger(__name__)


class SmartOCRService:
    """
    Smart OCR service that combines pattern matching with GPT-4 Vision
    and learns from every verification to continuously improve accuracy.

    Processing Pipeline:
    1. Auto-detect bank from screenshot
    2. Try bank-specific patterns (fast, free)
    3. Check merchant-specific patterns
    4. Fall back to GPT-4 Vision if needed (expensive)
    5. Learn from verification result (auto-improvement)
    """

    def __init__(self):
        self.cost_savings = {
            'pattern_successes': 0,
            'gpt4_calls_avoided': 0,
            'total_verifications': 0,
            'estimated_savings_usd': 0.0
        }
        self.gpt4_vision_cost_per_call = 0.05  # Estimated cost per GPT-4 Vision call

    async def initialize(self):
        """Initialize the auto-learning system."""
        await auto_learning_ocr.initialize()

    async def verify_screenshot_smart(
        self,
        image_data: bytes,
        filename: str = "screenshot.jpg",
        invoice_id: Optional[str] = None,
        expected_payment: Optional[Dict[str, Any]] = None,
        customer_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        use_learning: bool = True
    ) -> Dict[str, Any]:
        """
        Smart verification that tries patterns first, then GPT-4 Vision.

        Args:
            image_data: Screenshot bytes
            filename: Original filename
            invoice_id: Invoice ID for reference
            expected_payment: Expected payment details
            customer_id: Customer reference
            tenant_id: Tenant/merchant ID for merchant-specific patterns
            use_learning: Whether to use learning system (default True)

        Returns:
            Verification result with cost-saving info
        """
        self.cost_savings['total_verifications'] += 1
        start_time = datetime.now(timezone.utc)

        verification_result = {
            'success': False,
            'processing_method': 'unknown',
            'pattern_matched': False,
            'gpt4_used': False,
            'cost_effective': False,
            'processing_time_seconds': 0,
            'learning_applied': False
        }

        try:
            # Step 1: Extract OCR text using simple OCR (free/cheap)
            ocr_text = await self._extract_basic_ocr_text(image_data)

            # Step 2: Try pattern-based extraction first
            if use_learning and ocr_text:
                pattern_result = await self._try_pattern_extraction(
                    ocr_text=ocr_text,
                    expected_payment=expected_payment,
                    tenant_id=tenant_id
                )

                if pattern_result['success'] and pattern_result['confidence'] >= 0.80:
                    # High confidence pattern match - use this result
                    verification_result.update(pattern_result)
                    verification_result.update({
                        'processing_method': 'pattern_matching',
                        'pattern_matched': True,
                        'cost_effective': True,
                        'gpt4_used': False,
                        'learning_applied': True
                    })

                    # Track cost savings
                    self.cost_savings['pattern_successes'] += 1
                    self.cost_savings['gpt4_calls_avoided'] += 1
                    self.cost_savings['estimated_savings_usd'] += self.gpt4_vision_cost_per_call

                    logger.info(
                        f"✅ Pattern matching success for {invoice_id}: "
                        f"{pattern_result['confidence']:.1%} confidence, "
                        f"saved ${self.gpt4_vision_cost_per_call:.3f}"
                    )

                    # Learn from this successful pattern match
                    if use_learning and pattern_result.get('verification_status') in ['verified']:
                        await self._learn_from_success(
                            ocr_text=ocr_text,
                            expected_payment=expected_payment,
                            verification_result=pattern_result,
                            tenant_id=tenant_id,  # SECURITY: Pass tenant_id for learning isolation
                            merchant_id=tenant_id  # Using tenant_id as merchant_id for now
                        )

                    # Calculate processing time
                    processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                    verification_result['processing_time_seconds'] = processing_time

                    return verification_result

            # Step 3: Pattern matching failed or low confidence - use GPT-4 Vision
            logger.info(f"⚡ Pattern matching insufficient, using GPT-4 Vision for {invoice_id}")

            gpt4_result = await ocr_service.verify_screenshot(
                image_data=image_data,
                filename=filename,
                invoice_id=invoice_id,
                expected_payment=expected_payment,
                customer_id=customer_id
            )

            verification_result.update(gpt4_result)
            verification_result.update({
                'processing_method': 'gpt4_vision',
                'pattern_matched': False,
                'cost_effective': False,
                'gpt4_used': True,
                'ocr_text': ocr_text  # Include OCR text for learning
            })

            # Learn from GPT-4 result to improve future pattern matching
            if (use_learning and gpt4_result.get('success') and
                gpt4_result.get('verification', {}).get('status') == 'verified'):

                await self._learn_from_gpt4_success(
                    ocr_text=ocr_text,
                    expected_payment=expected_payment,
                    verification_result=gpt4_result,
                    tenant_id=tenant_id
                )

                verification_result['learning_applied'] = True

            # Calculate processing time
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            verification_result['processing_time_seconds'] = processing_time

            return verification_result

        except Exception as e:
            logger.error(f"❌ Smart OCR verification failed: {e}")
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return {
                'success': False,
                'error': str(e),
                'processing_method': 'error',
                'processing_time_seconds': processing_time,
                'gpt4_used': False,
                'cost_effective': False
            }

    async def _extract_basic_ocr_text(self, image_data: bytes) -> str:
        """
        Extract basic OCR text using lightweight OCR (not GPT-4 Vision).

        In production, this could use:
        - Tesseract OCR
        - PaddleOCR
        - Google Cloud Vision Text Detection (cheaper than GPT-4)
        - AWS Textract

        For now, simulates OCR text extraction.
        """
        try:
            # TODO: Replace with actual lightweight OCR
            # For now, return placeholder that would come from real OCR

            # Simulate OCR text based on image size (mock implementation)
            image_size = len(image_data)

            # In reality, you would:
            # import cv2, pytesseract
            # image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            # ocr_text = pytesseract.image_to_string(image)

            # Mock OCR text (replace with real implementation)
            if image_size > 100000:  # Large image
                return "Transfer to JOHN DOE Account 012-345-678 Amount 50,000 KHR ABA Bank"
            elif image_size > 50000:  # Medium image
                return "ACLEDA Beneficiary Name JANE SMITH Account No 987-654-321 Amount 25,000 KHR"
            else:  # Small image
                return "Wing Receiver 123456789 Amount 10,000 KHR"

        except Exception as e:
            logger.warning(f"Basic OCR extraction failed: {e}")
            return ""

    async def _try_pattern_extraction(
        self,
        ocr_text: str,
        expected_payment: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Try to extract payment information using learned patterns.

        Args:
            ocr_text: Raw OCR text from image
            expected_payment: Expected payment for verification
            tenant_id: Merchant ID for merchant-specific patterns

        Returns:
            Extraction and verification result
        """
        try:
            # Step 1: Detect bank and extract using tenant-specific patterns
            detection_result = await auto_learning_ocr.detect_bank_and_extract(
                ocr_text=ocr_text,
                bank_name=expected_payment.get('bank') if expected_payment else None,
                tenant_id=tenant_id  # SECURITY: Pass tenant_id for tenant-specific pattern learning
            )

            if not detection_result['pattern_matched']:
                return {'success': False, 'confidence': 0, 'error': 'No patterns matched'}

            detected_bank = detection_result['detected_bank']
            extracted_data = detection_result['extracted_data']
            overall_confidence = detection_result['overall_confidence']

            logger.debug(f"Pattern extraction: {detected_bank}, confidence: {overall_confidence:.2f}")

            # Step 2: Try merchant-specific patterns for higher accuracy
            if tenant_id and detected_bank != 'Unknown':
                merchant_patterns = merchant_cache.get_merchant_patterns(tenant_id, detected_bank)
                if merchant_patterns:
                    # Apply merchant-specific patterns for refinement
                    refined_data = await self._apply_merchant_patterns(
                        ocr_text, merchant_patterns, extracted_data
                    )
                    if refined_data:
                        extracted_data.update(refined_data)
                        overall_confidence = min(0.95, overall_confidence + 0.10)  # Boost confidence

            # Step 3: Verify against expected payment if provided
            if expected_payment:
                verification_result = self._verify_extracted_against_expected(
                    extracted_data, expected_payment
                )
            else:
                verification_result = {
                    'status': 'extracted',
                    'message': 'Data extracted successfully'
                }

            return {
                'success': True,
                'confidence': overall_confidence,
                'extracted_data': extracted_data,
                'verification': verification_result,
                'verification_status': verification_result.get('status', 'pending'),
                'detected_bank': detected_bank,
                'processing_method': 'pattern_extraction'
            }

        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            return {'success': False, 'confidence': 0, 'error': str(e)}

    async def _apply_merchant_patterns(
        self,
        ocr_text: str,
        merchant_patterns: List[Dict[str, Any]],
        base_extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply merchant-specific patterns to refine extraction."""
        refined_data = {}

        for pattern in merchant_patterns:
            try:
                pattern_type = pattern.get('type')
                regex = pattern.get('regex')

                if not pattern_type or not regex:
                    continue

                import re
                matches = re.findall(regex, ocr_text, re.IGNORECASE)
                if matches:
                    refined_data[pattern_type] = matches[0].strip()

            except Exception as e:
                logger.warning(f"Merchant pattern failed: {e}")

        return refined_data

    def _verify_extracted_against_expected(
        self,
        extracted_data: Dict[str, Any],
        expected_payment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify extracted data against expected payment details.

        Args:
            extracted_data: Data extracted from OCR
            expected_payment: Expected payment details

        Returns:
            Verification result
        """
        verification_flags = {}
        rejection_reasons = []
        warnings = []

        # Check amount
        extracted_amount_str = extracted_data.get('amount', '')
        expected_amount = expected_payment.get('amount', 0)

        if extracted_amount_str:
            try:
                # Clean extracted amount string
                import re
                amount_clean = re.sub(r'[^\d\.]', '', extracted_amount_str)
                extracted_amount = float(amount_clean) if amount_clean else 0

                tolerance = expected_payment.get('tolerancePercent', 5) / 100
                amount_diff = abs(extracted_amount - expected_amount) / expected_amount if expected_amount else 1

                verification_flags['amount'] = amount_diff <= tolerance

                if not verification_flags['amount']:
                    rejection_reasons.append(f"Amount mismatch: expected {expected_amount}, found {extracted_amount}")

            except ValueError:
                verification_flags['amount'] = False
                rejection_reasons.append(f"Could not parse amount: {extracted_amount_str}")
        else:
            verification_flags['amount'] = False
            rejection_reasons.append("Amount not found in screenshot")

        # Check recipient name
        extracted_recipient = extracted_data.get('recipient', '')
        expected_recipients = expected_payment.get('recipientNames', [])

        if expected_recipients and extracted_recipient:
            # Check if extracted name matches any expected name (fuzzy matching)
            recipient_match = any(
                self._fuzzy_name_match(extracted_recipient, expected_name)
                for expected_name in expected_recipients
            )
            verification_flags['recipient'] = recipient_match

            if not recipient_match:
                warnings.append(f"Recipient name mismatch: expected {expected_recipients[0]}, found {extracted_recipient}")

        # Check account number
        extracted_account = extracted_data.get('account', '')
        expected_account = expected_payment.get('toAccount', '')

        if expected_account and extracted_account:
            # Clean both account numbers for comparison
            import re
            clean_extracted = re.sub(r'[\s\-]', '', extracted_account)
            clean_expected = re.sub(r'[\s\-]', '', expected_account)

            verification_flags['account'] = clean_extracted == clean_expected

            if not verification_flags['account']:
                warnings.append(f"Account mismatch: expected {expected_account}, found {extracted_account}")

        # Determine overall verification status
        if rejection_reasons:
            status = 'rejected'
            message = '; '.join(rejection_reasons)
        elif warnings and len(warnings) > 1:
            status = 'pending'
            message = 'Multiple fields need manual review: ' + '; '.join(warnings)
        elif warnings:
            status = 'pending'
            message = warnings[0] + ' - needs manual review'
        else:
            status = 'verified'
            message = 'Payment verified successfully'

        return {
            'status': status,
            'message': message,
            'matched': verification_flags,
            'warnings': warnings,
            'rejectionReasons': rejection_reasons
        }

    def _fuzzy_name_match(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two names match with fuzzy matching."""
        if not name1 or not name2:
            return False

        # Simple fuzzy matching - in production, use libraries like fuzzywuzzy
        name1_clean = ''.join(name1.lower().split())
        name2_clean = ''.join(name2.lower().split())

        if name1_clean == name2_clean:
            return True

        # Check if one name contains the other
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return True

        # Simple character similarity (placeholder for real fuzzy matching)
        common_chars = set(name1_clean) & set(name2_clean)
        total_chars = set(name1_clean) | set(name2_clean)

        similarity = len(common_chars) / len(total_chars) if total_chars else 0
        return similarity >= threshold

    async def _learn_from_success(
        self,
        ocr_text: str,
        expected_payment: Dict[str, Any],
        verification_result: Dict[str, Any],
        tenant_id: Optional[str] = None,
        merchant_id: Optional[str] = None
    ):
        """Learn from a successful pattern-based verification."""
        try:
            await auto_learning_ocr.learn_from_verification(
                ocr_text=ocr_text,
                verified_data=expected_payment,
                verification_result=verification_result,
                tenant_id=tenant_id,  # SECURITY: Pass tenant_id for isolation
                merchant_id=merchant_id  # SECURITY: Pass merchant_id for isolation
            )

            logger.debug("✅ Learning data queued from pattern success")

        except Exception as e:
            logger.warning(f"Learning from pattern success failed: {e}")

    async def _learn_from_gpt4_success(
        self,
        ocr_text: str,
        expected_payment: Dict[str, Any],
        verification_result: Dict[str, Any],
        tenant_id: Optional[str] = None
    ):
        """Learn from a successful GPT-4 Vision verification to improve patterns."""
        try:
            # Queue for pattern learning with tenant isolation
            await auto_learning_ocr.learn_from_verification(
                ocr_text=ocr_text,
                verified_data=expected_payment,
                verification_result=verification_result,
                tenant_id=tenant_id,  # SECURITY: Pass tenant_id for isolation
                merchant_id=tenant_id  # Using tenant_id as merchant_id for now
            )

            # Add to merchant-specific patterns if tenant provided
            if tenant_id and verification_result.get('confidence', 0) > 0.85:
                extracted_data = verification_result.get('extracted_data', {})
                bank = expected_payment.get('bank', 'Unknown')

                # Create merchant-specific patterns from GPT-4 success
                for field_type, value in extracted_data.items():
                    if value and isinstance(value, str):
                        # Create simple pattern based on GPT-4 extraction
                        import re
                        escaped_value = re.escape(value)
                        context_pattern = f'.{{0,20}}{escaped_value}.{{0,20}}'

                        merchant_pattern = {
                            'type': field_type,
                            'regex': context_pattern,
                            'confidence': min(0.90, verification_result.get('confidence', 0.85)),
                            'source': 'gpt4_learning'
                        }

                        merchant_cache.add_merchant_pattern(
                            tenant_id=tenant_id,
                            bank_code=bank,
                            pattern=merchant_pattern,
                            success_rate=verification_result.get('confidence', 0.85)
                        )

            logger.debug("✅ Learning data queued from GPT-4 success")

        except Exception as e:
            logger.warning(f"Learning from GPT-4 success failed: {e}")

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""
        try:
            # Get learning stats from auto-learning system
            learning_stats = await auto_learning_ocr.get_learning_stats()

            # Get training job stats
            training_stats = await training_scheduler.processor.get_training_stats() if training_scheduler.processor.db else {}

            # Calculate efficiency metrics
            total_verifications = self.cost_savings['total_verifications']
            pattern_success_rate = (
                self.cost_savings['pattern_successes'] / total_verifications
                if total_verifications > 0 else 0
            )

            return {
                'cost_savings': self.cost_savings.copy(),
                'pattern_success_rate': pattern_success_rate,
                'estimated_monthly_savings': self.cost_savings['estimated_savings_usd'] * 30,  # Rough estimate
                'learning_system': learning_stats,
                'training_system': training_stats,
                'cache_info': pattern_cache.get_cache_info(),
                'service_health': 'active',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {'error': str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        health = {
            'smart_ocr': 'healthy',
            'auto_learning': 'unknown',
            'pattern_cache': 'unknown',
            'training_scheduler': 'unknown',
            'fallback_ocr': 'unknown'
        }

        try:
            # Check auto-learning system
            learning_stats = await auto_learning_ocr.get_learning_stats()
            health['auto_learning'] = 'healthy' if 'error' not in learning_stats else 'error'

            # Check pattern cache
            cache_info = pattern_cache.get_cache_info()
            health['pattern_cache'] = 'healthy'

            # Check training scheduler
            health['training_scheduler'] = 'active' if training_scheduler.is_running else 'stopped'

            # Check fallback OCR service
            fallback_health = await ocr_service.health_check()
            health['fallback_ocr'] = fallback_health.get('status', 'unknown')

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health['error'] = str(e)

        health['overall'] = 'healthy' if all(
            status in ['healthy', 'active'] for status in health.values() if status != 'unknown'
        ) else 'degraded'

        return health


# Global instance
smart_ocr = SmartOCRService()