"""
Content Moderation Service for Ads Alert System

Detects illegal, harmful, or policy-violating content in promotional materials
before they are sent to Telegram to ensure platform compliance and user safety.
"""

import re
import logging
import httpx
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from uuid import UUID

from app.core.models import ModerationStatus
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ViolationPattern:
    """Represents a content violation pattern with severity and category."""

    def __init__(self, pattern: str, category: str, severity: int, description: str, case_sensitive: bool = False):
        self.pattern = pattern if case_sensitive else pattern.lower()
        self.category = category  # "illegal", "adult", "scam", "hate_speech", etc.
        self.severity = severity  # 1-10 scale (10 = immediate block)
        self.description = description
        self.case_sensitive = case_sensitive
        self.regex = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)


class ContentModerationService:
    """
    Service for detecting illegal and policy-violating content in promotional materials.

    Supports both text analysis and OCR-based image analysis to detect:
    - Illegal content (drugs, weapons, prohibited services)
    - Adult/explicit content
    - Hate speech and discrimination
    - Scams and phishing attempts
    - Copyright violations
    - Misleading health claims
    """

    def __init__(self):
        self.violation_patterns = self._load_violation_patterns()
        # OCR is done via HTTP to api-gateway, not direct import
        _settings = get_settings()
        self.api_gateway_url = getattr(_settings, 'API_GATEWAY_URL', None)

    def _load_violation_patterns(self) -> List[ViolationPattern]:
        """Load violation patterns for Cambodia market with localized terms."""
        patterns = []

        # === ILLEGAL DRUGS & SUBSTANCES ===
        # English terms
        patterns.extend([
            ViolationPattern(r'\b(marijuana|cannabis|weed|ganja|hemp)\b', 'illegal_drugs', 9, 'Cannabis products'),
            ViolationPattern(r'\b(cocaine|heroin|meth|methamphetamine|ecstasy|mdma)\b', 'illegal_drugs', 10, 'Hard drugs'),
            ViolationPattern(r'\b(opium|morphine|fentanyl|ketamine|lsd|acid)\b', 'illegal_drugs', 10, 'Controlled substances'),
            ViolationPattern(r'\b(steroids|anabolic|testosterone|hgh)\b', 'illegal_drugs', 8, 'Performance enhancing drugs'),
            ViolationPattern(r'\b(viagra|cialis|levitra)\s+(without\s+prescription|no\s+rx)', 'illegal_drugs', 7, 'Prescription drugs without license'),
        ])

        # Khmer terms (transliterated)
        patterns.extend([
            ViolationPattern(r'(កញ្ឆា|ស្លឹកកញ្ឆា)', 'illegal_drugs', 9, 'Cannabis in Khmer'),
            ViolationPattern(r'(យ៉ាបា|យ៉ាម៉ា)', 'illegal_drugs', 10, 'Methamphetamine in Khmer'),
            ViolationPattern(r'(ហេរ៉ូអ៊ីន|កូកាអ៊ីន)', 'illegal_drugs', 10, 'Hard drugs in Khmer'),
        ])

        # === WEAPONS & EXPLOSIVES ===
        patterns.extend([
            ViolationPattern(r'\b(gun|pistol|rifle|ak47|ar15|weapon|firearm)\b', 'weapons', 10, 'Firearms'),
            ViolationPattern(r'\b(bomb|explosive|grenade|ammunition|bullet|gunpowder)\b', 'weapons', 10, 'Explosives'),
            ViolationPattern(r'\b(knife|sword|machete|dagger|blade)\s+(for\s+sale|sell|buy)', 'weapons', 8, 'Edged weapons for sale'),
            ViolationPattern(r'(កាំភ្លើង|អាវុធ|គ្រាប់បែក)', 'weapons', 10, 'Weapons in Khmer'),
        ])

        # === ADULT CONTENT ===
        patterns.extend([
            ViolationPattern(r'\b(porn|pornography|xxx|sex\s+videos|adult\s+videos)\b', 'adult_content', 9, 'Explicit content'),
            ViolationPattern(r'\b(escort|prostitute|brothel|massage\s+special)\b', 'adult_content', 9, 'Sexual services'),
            ViolationPattern(r'\b(nude|naked|topless|explicit|erotic)\s+(photos|pics|images)', 'adult_content', 8, 'Explicit imagery'),
            ViolationPattern(r'(ក្មេងស្រី|ស្រីលក់ខ្លួន|បុរសលក់ខ្លួន)', 'adult_content', 10, 'Sexual services in Khmer'),
        ])

        # === FINANCIAL SCAMS ===
        patterns.extend([
            ViolationPattern(r'\b(get\s+rich\s+quick|easy\s+money|work\s+from\s+home|guaranteed\s+profit)\b', 'scam', 7, 'Get rich quick schemes'),
            ViolationPattern(r'\b(pyramid\s+scheme|mlm|multi\s+level|ponzi)\b', 'scam', 9, 'Pyramid schemes'),
            ViolationPattern(r'\b(bitcoin|crypto|investment)\s+(guaranteed|double|triple)', 'scam', 8, 'Cryptocurrency scams'),
            ViolationPattern(r'\b(loan\s+shark|ខ្ចីប្រាក់|ការឆ្នោតដ៏ធំ)\b', 'scam', 8, 'Loan sharks'),
            ViolationPattern(r'(ឆ្នោត|ឈ្នះលុយ|ពីក្រៅប្រទេស)', 'scam', 7, 'Lottery scams in Khmer'),
        ])

        # === HATE SPEECH & DISCRIMINATION ===
        patterns.extend([
            ViolationPattern(r'\b(hate|kill|murder|death\s+to)\s+(cambodian|khmer|vietnamese|chinese|muslim)\b', 'hate_speech', 10, 'Ethnic hatred'),
            ViolationPattern(r'\b(terrorist|terrorism|jihad|infidel)\b', 'hate_speech', 9, 'Extremist content'),
            ViolationPattern(r'(ស្អប់|ពួកយួន|ពួកចិន|សម្លាប់)', 'hate_speech', 9, 'Hate speech in Khmer'),
        ])

        # === MEDICAL MISINFORMATION ===
        patterns.extend([
            ViolationPattern(r'\b(cure\s+cancer|cure\s+diabetes|cure\s+hiv|miracle\s+medicine)\b', 'medical_misinformation', 8, 'False medical claims'),
            ViolationPattern(r'\b(covid\s+cure|coronavirus\s+treatment|vaccine\s+dangerous)\b', 'medical_misinformation', 7, 'COVID misinformation'),
            ViolationPattern(r'(ថ្នាំព្យាបាលមហារីក|ព្យាបាលឆ្គង)', 'medical_misinformation', 8, 'Medical misinformation in Khmer'),
        ])

        # === COUNTERFEIT GOODS ===
        patterns.extend([
            ViolationPattern(r'\b(fake|replica|counterfeit)\s+(rolex|gucci|louis\s+vuitton|nike|adidas)\b', 'counterfeit', 7, 'Counterfeit luxury goods'),
            ViolationPattern(r'\b(copy|knockoff|aaa\s+grade)\s+(phone|iphone|samsung)\b', 'counterfeit', 6, 'Counterfeit electronics'),
        ])

        # === POLITICAL CONTENT (Cambodia-specific) ===
        patterns.extend([
            ViolationPattern(r'\b(hun\s+sen|sam\s+rainsy|kem\s+sokha)\s+(corrupt|dictator|traitor)', 'political_hate', 8, 'Political defamation'),
            ViolationPattern(r'(ផ្តាច់ការ|ក្បត់ជាតិ|រំលាយគណបក្ស)', 'political_hate', 8, 'Political attacks in Khmer'),
        ])

        return patterns

    async def moderate_content(
        self,
        text_content: Optional[str] = None,
        image_urls: Optional[List[str]] = None,
        media_files: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content moderation on text and images.

        Args:
            text_content: Text content to analyze
            image_urls: URLs of images to analyze with OCR
            media_files: Raw image bytes to analyze with OCR

        Returns:
            Moderation result with violations, score, and recommendation
        """
        violations = []
        extracted_texts = []
        confidence_scores = []

        # 1. Analyze text content directly
        if text_content:
            text_violations = self._analyze_text(text_content, source="text_content")
            violations.extend(text_violations)
            extracted_texts.append(text_content)

        # 2. Analyze images with OCR
        if image_urls or media_files:
            ocr_results = await self._analyze_images_with_ocr(image_urls, media_files)
            for result in ocr_results:
                if result.get('extracted_text'):
                    extracted_texts.append(result['extracted_text'])
                    text_violations = self._analyze_text(result['extracted_text'], source=f"image:{result['source']}")
                    violations.extend(text_violations)
                confidence_scores.append(result.get('confidence', 0))

        # 3. Calculate overall moderation score and status
        moderation_score, status, recommendation = self._calculate_moderation_result(violations, confidence_scores)

        # 4. Generate detailed result
        result = {
            "moderation_status": status.value,
            "moderation_score": moderation_score,
            "violations": violations,
            "extracted_texts": extracted_texts,
            "confidence_scores": confidence_scores,
            "recommendation": recommendation,
            "requires_manual_review": status == ModerationStatus.flagged,
            "can_be_sent": status in [ModerationStatus.approved, ModerationStatus.skipped],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_patterns_checked": len(self.violation_patterns),
            "analysis_details": {
                "text_sources": len([t for t in extracted_texts if t]),
                "image_sources": len(confidence_scores),
                "high_severity_violations": len([v for v in violations if v['severity'] >= 8]),
                "medium_severity_violations": len([v for v in violations if 5 <= v['severity'] < 8]),
                "low_severity_violations": len([v for v in violations if v['severity'] < 5])
            }
        }

        return result

    def _analyze_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """Analyze text content against violation patterns."""
        violations = []
        text_lower = text.lower()

        for pattern in self.violation_patterns:
            matches = pattern.regex.findall(text if pattern.case_sensitive else text_lower)
            if matches:
                violation = {
                    "pattern": pattern.pattern,
                    "category": pattern.category,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "matches": matches[:5],  # Limit to first 5 matches
                    "match_count": len(matches),
                    "source": source
                }
                violations.append(violation)

        return violations

    async def _analyze_images_with_ocr(
        self,
        image_urls: Optional[List[str]] = None,
        media_files: Optional[List[bytes]] = None
    ) -> List[Dict[str, Any]]:
        """Extract text from images using OCR and analyze for violations.

        Note: OCR is optional. If api-gateway is not available, image analysis
        is skipped and only text content is moderated.
        """
        results = []

        # Skip OCR if no api-gateway configured or no media to process
        if not (image_urls or media_files):
            return results

        # Process image URLs (placeholder - not implemented)
        if image_urls:
            for i, url in enumerate(image_urls):
                # URL-based OCR not yet implemented
                results.append({
                    "source": f"url_{i}",
                    "url": url,
                    "extracted_text": "",
                    "confidence": 0.0,
                    "error": "OCR URL processing not implemented - text analysis only"
                })

        # Process raw media files via api-gateway OCR endpoint
        if media_files and self.api_gateway_url:
            for i, file_bytes in enumerate(media_files):
                try:
                    # Call api-gateway OCR endpoint via HTTP
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        files = {
                            'file': (f'moderation_image_{i}.jpg', file_bytes, 'image/jpeg')
                        }
                        response = await client.post(
                            f"{self.api_gateway_url}/ocr/extract-text",
                            files=files
                        )

                        if response.status_code == 200:
                            ocr_result = response.json()
                            extracted_text = ocr_result.get("extracted_text", "")
                            raw_text = ocr_result.get("raw_text", "")
                            confidence = ocr_result.get("confidence", 0)

                            # Combine all text sources
                            all_text = (extracted_text or "") + " " + (raw_text or "")
                            all_text = all_text.strip()

                            results.append({
                                "source": f"file_{i}",
                                "extracted_text": all_text,
                                "confidence": confidence,
                                "language_detected": ocr_result.get("language_detected", "unknown"),
                                "text_blocks": ocr_result.get("text_blocks", [])
                            })
                        else:
                            logger.warning(f"OCR request failed with status {response.status_code}")
                            results.append({
                                "source": f"file_{i}",
                                "error": f"OCR request failed: {response.status_code}",
                                "confidence": 0
                            })

                except Exception as e:
                    logger.error(f"Error processing media file {i}: {e}")
                    results.append({
                        "source": f"file_{i}",
                        "error": str(e),
                        "confidence": 0
                    })
        elif media_files:
            # No api-gateway configured, skip OCR
            logger.info("OCR skipped - API_GATEWAY_URL not configured")
            for i, _ in enumerate(media_files):
                results.append({
                    "source": f"file_{i}",
                    "extracted_text": "",
                    "confidence": 0,
                    "error": "OCR skipped - api-gateway not configured"
                })

        return results

    def _calculate_moderation_result(
        self,
        violations: List[Dict[str, Any]],
        confidence_scores: List[float]
    ) -> Tuple[float, ModerationStatus, str]:
        """Calculate overall moderation score and determine status."""

        if not violations:
            # No violations found
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 100
            return avg_confidence, ModerationStatus.approved, "No violations detected"

        # Calculate severity score
        total_severity = sum(v['severity'] for v in violations)
        max_severity = max(v['severity'] for v in violations)
        violation_count = len(violations)

        # Weight calculation: consider both severity and quantity
        severity_score = min(100, (total_severity / violation_count) * 10)  # Normalize to 0-100

        # Determine status based on severity
        if max_severity >= 10:
            # Immediate block for severe violations
            status = ModerationStatus.rejected
            recommendation = f"Rejected: Severe violations detected (max severity: {max_severity})"
        elif max_severity >= 8:
            # High severity - requires review
            status = ModerationStatus.flagged
            recommendation = f"Flagged for manual review: High severity violations (max: {max_severity})"
        elif total_severity >= 15:
            # Multiple moderate violations
            status = ModerationStatus.flagged
            recommendation = f"Flagged for manual review: Multiple violations (total severity: {total_severity})"
        elif max_severity >= 6:
            # Moderate violations - could be false positives
            status = ModerationStatus.flagged
            recommendation = f"Flagged for review: Moderate violations detected (max: {max_severity})"
        else:
            # Low severity - likely acceptable with warning
            status = ModerationStatus.approved
            recommendation = f"Approved with caution: {violation_count} low-severity violations detected"

        return severity_score, status, recommendation

    def add_violation_pattern(self, pattern: ViolationPattern) -> None:
        """Add a custom violation pattern."""
        self.violation_patterns.append(pattern)

    def get_violation_categories(self) -> Dict[str, int]:
        """Get count of patterns by category."""
        categories = {}
        for pattern in self.violation_patterns:
            categories[pattern.category] = categories.get(pattern.category, 0) + 1
        return categories


# Global service instance
content_moderation_service = ContentModerationService()