"""
Pattern Learning Service for Payment Verification

This service learns from customer payment patterns to improve
recipient name matching accuracy. It works with both scriptclient
and ocr-service by learning which recipient names customers
actually use when making payments.

Key Features:
- Learns customer-recipient name relationships
- Fuzzy name matching with confidence scoring
- Gradual confidence building over multiple verifications
- Multi-tenant support with complete isolation
"""

import re
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Fuzzy matching library
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("Warning: rapidfuzz not available, using basic string matching")

logger = logging.getLogger(__name__)


@dataclass
class RecipientPattern:
    """Represents a learned pattern for how a customer pays"""
    extracted_name: str
    extracted_account: str
    occurrence_count: int
    confidence: float
    last_seen: datetime
    auto_approve: bool
    bank_name: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of pattern-based verification"""
    should_auto_approve: bool
    confidence: float
    reason: str
    matched_pattern: Optional[RecipientPattern] = None
    similarity_score: Optional[float] = None


class PatternLearningService:
    """Service for learning and applying payment verification patterns"""

    def __init__(self, db):
        self.db = db
        self.collection = db['payment_patterns']

        # Configuration
        self.MIN_AUTO_APPROVE_COUNT = 3      # Need 3 verifications before auto-approve
        self.AUTO_APPROVE_CONFIDENCE = 0.8   # Need 80% confidence for auto-approve
        self.FUZZY_MATCH_THRESHOLD = 0.75    # 75% similarity for fuzzy matching
        self.HIGH_CONFIDENCE_THRESHOLD = 0.9 # 90% confidence threshold

    async def learn_from_verification(
        self,
        tenant_id: str,
        customer_id: str,
        customer_name: str,
        extracted_name: str,
        extracted_account: str,
        was_approved: bool,
        bank_name: Optional[str] = None
    ) -> None:
        """
        Learn from a verification attempt (approved or rejected)

        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            customer_id: Unique customer identifier
            customer_name: Expected customer name (from invoice)
            extracted_name: Actual recipient name from OCR
            extracted_account: Account number from OCR
            was_approved: Whether this verification was approved
            bank_name: Bank name if available
        """
        try:
            # Get existing pattern for this customer
            pattern_doc = await self.collection.find_one({
                "tenant_id": tenant_id,
                "customer_id": customer_id
            })

            if not pattern_doc:
                # Create new pattern document
                pattern_doc = {
                    "tenant_id": tenant_id,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "recipient_patterns": [],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

            # Find existing recipient pattern
            existing_pattern = None
            for i, pattern in enumerate(pattern_doc["recipient_patterns"]):
                if (pattern["extracted_name"] == extracted_name and
                    pattern["extracted_account"] == extracted_account):
                    existing_pattern = (i, pattern)
                    break

            if existing_pattern:
                # Update existing pattern
                i, pattern = existing_pattern
                pattern_doc["recipient_patterns"][i] = self._update_pattern(
                    pattern, was_approved, bank_name
                )
            else:
                # Create new pattern
                new_pattern = {
                    "extracted_name": extracted_name,
                    "extracted_account": extracted_account,
                    "occurrence_count": 1,
                    "approval_count": 1 if was_approved else 0,
                    "rejection_count": 0 if was_approved else 1,
                    "confidence": 0.6 if was_approved else 0.2,
                    "last_seen": datetime.now(timezone.utc),
                    "auto_approve": False,
                    "bank_name": bank_name,
                    "created_at": datetime.now(timezone.utc)
                }
                pattern_doc["recipient_patterns"].append(new_pattern)

            pattern_doc["updated_at"] = datetime.now(timezone.utc)

            # Save to database
            await self.collection.replace_one(
                {"tenant_id": tenant_id, "customer_id": customer_id},
                pattern_doc,
                upsert=True
            )

            logger.info(f"Pattern learned: {customer_name} → {extracted_name} "
                       f"({'approved' if was_approved else 'rejected'})")

        except Exception as e:
            logger.error(f"Failed to learn pattern: {e}")

    def _update_pattern(self, pattern: dict, was_approved: bool, bank_name: Optional[str]) -> dict:
        """Update an existing recipient pattern with new verification data"""

        # Update counts
        pattern["occurrence_count"] += 1
        pattern["last_seen"] = datetime.now(timezone.utc)

        if was_approved:
            pattern["approval_count"] = pattern.get("approval_count", 0) + 1
        else:
            pattern["rejection_count"] = pattern.get("rejection_count", 0) + 1

        # Update bank name if provided
        if bank_name:
            pattern["bank_name"] = bank_name

        # Calculate new confidence based on approval rate
        total_attempts = pattern["approval_count"] + pattern["rejection_count"]
        approval_rate = pattern["approval_count"] / total_attempts

        # Confidence formula: base approval rate + bonus for frequency
        frequency_bonus = min(0.2, pattern["occurrence_count"] * 0.02)
        pattern["confidence"] = min(0.95, approval_rate + frequency_bonus)

        # Auto-approve criteria
        pattern["auto_approve"] = (
            pattern["occurrence_count"] >= self.MIN_AUTO_APPROVE_COUNT and
            pattern["confidence"] >= self.AUTO_APPROVE_CONFIDENCE and
            approval_rate >= 0.8  # At least 80% approval rate
        )

        return pattern

    async def verify_with_patterns(
        self,
        tenant_id: str,
        customer_id: str,
        extracted_name: str,
        extracted_account: str,
        extracted_amount: Optional[float] = None
    ) -> VerificationResult:
        """
        Verify a payment using learned patterns

        Args:
            tenant_id: Tenant identifier
            customer_id: Customer identifier
            extracted_name: Recipient name from OCR
            extracted_account: Account number from OCR
            extracted_amount: Payment amount (optional)

        Returns:
            VerificationResult with approval decision and confidence
        """
        try:
            # Get customer's patterns
            pattern_doc = await self.collection.find_one({
                "tenant_id": tenant_id,
                "customer_id": customer_id
            })

            if not pattern_doc:
                return VerificationResult(
                    should_auto_approve=False,
                    confidence=0.0,
                    reason="new_customer_no_patterns"
                )

            # Check for exact match first
            for pattern in pattern_doc["recipient_patterns"]:
                if (self._normalize_name(pattern["extracted_name"]) ==
                    self._normalize_name(extracted_name) and
                    self._normalize_account(pattern["extracted_account"]) ==
                    self._normalize_account(extracted_account)):

                    recipient_pattern = RecipientPattern(
                        extracted_name=pattern["extracted_name"],
                        extracted_account=pattern["extracted_account"],
                        occurrence_count=pattern["occurrence_count"],
                        confidence=pattern["confidence"],
                        last_seen=pattern["last_seen"],
                        auto_approve=pattern["auto_approve"],
                        bank_name=pattern.get("bank_name")
                    )

                    return VerificationResult(
                        should_auto_approve=pattern["auto_approve"],
                        confidence=pattern["confidence"],
                        reason=f"exact_match_seen_{pattern['occurrence_count']}_times",
                        matched_pattern=recipient_pattern
                    )

            # Check for fuzzy matches
            if FUZZY_AVAILABLE:
                best_match = self._find_fuzzy_match(
                    pattern_doc["recipient_patterns"],
                    extracted_name,
                    extracted_account
                )

                if best_match:
                    pattern, similarity = best_match

                    # Calculate combined confidence
                    combined_confidence = pattern["confidence"] * similarity

                    recipient_pattern = RecipientPattern(
                        extracted_name=pattern["extracted_name"],
                        extracted_account=pattern["extracted_account"],
                        occurrence_count=pattern["occurrence_count"],
                        confidence=pattern["confidence"],
                        last_seen=pattern["last_seen"],
                        auto_approve=pattern["auto_approve"],
                        bank_name=pattern.get("bank_name")
                    )

                    return VerificationResult(
                        should_auto_approve=(
                            combined_confidence >= self.AUTO_APPROVE_CONFIDENCE and
                            pattern["auto_approve"]
                        ),
                        confidence=combined_confidence,
                        reason=f"fuzzy_match_{similarity:.0%}_similarity",
                        matched_pattern=recipient_pattern,
                        similarity_score=similarity
                    )

            # Check amount patterns for additional context
            amount_confidence = self._check_amount_pattern(
                pattern_doc.get("amount_patterns", []),
                extracted_amount
            ) if extracted_amount else 0.0

            # No pattern match but has history with this customer
            return VerificationResult(
                should_auto_approve=False,
                confidence=max(0.3, amount_confidence),
                reason="customer_known_but_new_recipient_pattern"
            )

        except Exception as e:
            logger.error(f"Pattern verification failed: {e}")
            return VerificationResult(
                should_auto_approve=False,
                confidence=0.0,
                reason="verification_error"
            )

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""

        # Remove common prefixes/suffixes and normalize
        normalized = re.sub(r'\b(Mr|Ms|Mrs|Dr)\.?\s*', '', name, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized.strip().upper())

        # Handle initials (K. CHAN → K CHAN)
        normalized = re.sub(r'\.', '', normalized)

        return normalized

    def _normalize_account(self, account: str) -> str:
        """Normalize account number for comparison"""
        if not account:
            return ""

        # Remove spaces, dashes, and other separators
        return re.sub(r'[\s\-\.]', '', account).upper()

    def _find_fuzzy_match(
        self,
        patterns: List[dict],
        extracted_name: str,
        extracted_account: str
    ) -> Optional[Tuple[dict, float]]:
        """Find best fuzzy match among patterns"""
        if not FUZZY_AVAILABLE:
            return None

        best_match = None
        best_similarity = 0.0

        normalized_extracted_name = self._normalize_name(extracted_name)
        normalized_extracted_account = self._normalize_account(extracted_account)

        for pattern in patterns:
            # Name similarity
            name_similarity = fuzz.token_sort_ratio(
                normalized_extracted_name,
                self._normalize_name(pattern["extracted_name"])
            ) / 100.0

            # Account similarity
            account_similarity = fuzz.ratio(
                normalized_extracted_account,
                self._normalize_account(pattern["extracted_account"])
            ) / 100.0

            # Combined similarity (weighted toward account number)
            combined_similarity = (name_similarity * 0.6 + account_similarity * 0.4)

            if (combined_similarity > best_similarity and
                combined_similarity >= self.FUZZY_MATCH_THRESHOLD):
                best_match = pattern
                best_similarity = combined_similarity

        return (best_match, best_similarity) if best_match else None

    def _check_amount_pattern(self, amount_patterns: List[float], amount: float) -> float:
        """Check if amount matches typical patterns for this customer"""
        if not amount_patterns or not amount:
            return 0.0

        # Check if amount is within typical range
        for pattern_amount in amount_patterns:
            tolerance = pattern_amount * 0.1  # 10% tolerance
            if abs(amount - pattern_amount) <= tolerance:
                return 0.5  # Moderate confidence boost

        return 0.0

    async def get_customer_patterns(self, tenant_id: str, customer_id: str) -> Optional[dict]:
        """Get all patterns for a specific customer"""
        return await self.collection.find_one({
            "tenant_id": tenant_id,
            "customer_id": customer_id
        })

    async def get_learning_statistics(self, tenant_id: str) -> dict:
        """Get learning statistics for a tenant"""
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$unwind": "$recipient_patterns"},
            {"$group": {
                "_id": None,
                "total_patterns": {"$sum": 1},
                "auto_approvable": {
                    "$sum": {"$cond": ["$recipient_patterns.auto_approve", 1, 0]}
                },
                "avg_confidence": {"$avg": "$recipient_patterns.confidence"},
                "high_confidence": {
                    "$sum": {"$cond": [
                        {"$gte": ["$recipient_patterns.confidence", self.HIGH_CONFIDENCE_THRESHOLD]},
                        1, 0
                    ]}
                }
            }}
        ]

        result = await self.collection.aggregate(pipeline).to_list(1)

        if not result:
            return {
                "total_patterns": 0,
                "auto_approvable": 0,
                "auto_approval_rate": 0.0,
                "avg_confidence": 0.0,
                "high_confidence_rate": 0.0
            }

        stats = result[0]
        total = stats["total_patterns"]

        return {
            "total_patterns": total,
            "auto_approvable": stats["auto_approvable"],
            "auto_approval_rate": stats["auto_approvable"] / total if total > 0 else 0.0,
            "avg_confidence": stats["avg_confidence"] or 0.0,
            "high_confidence_rate": stats["high_confidence"] / total if total > 0 else 0.0
        }

    async def cleanup_old_patterns(self, days_old: int = 90) -> int:
        """Clean up patterns that haven't been seen in X days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        # Remove patterns with last_seen older than cutoff
        result = await self.collection.update_many(
            {},
            {
                "$pull": {
                    "recipient_patterns": {
                        "last_seen": {"$lt": cutoff_date}
                    }
                }
            }
        )

        # Remove empty pattern documents
        await self.collection.delete_many({
            "recipient_patterns": {"$size": 0}
        })

        return result.modified_count


# Export for use in other modules
__all__ = ['PatternLearningService', 'VerificationResult', 'RecipientPattern']