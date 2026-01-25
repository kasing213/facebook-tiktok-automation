# api-gateway/src/jobs/ocr_training_job.py
"""
Background OCR Training Job

This job continuously processes the learning queue to improve OCR patterns
without manual intervention. It runs automatically after each verification
to ensure the system gets smarter with every payment.
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

import motor.motor_asyncio
from src.config import settings
from src.services.pattern_cache import pattern_cache, merchant_cache

logger = logging.getLogger(__name__)


class OCRTrainingProcessor:
    """
    Processes learning data from verification results to improve OCR accuracy.

    Features:
    - Batch processing of learning queue
    - Pattern validation and scoring
    - Automatic template updates
    - Performance monitoring
    """

    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.processing_batch_size = 50
        self.min_pattern_confidence = 0.70
        self.min_samples_for_update = 3

    async def initialize(self):
        """Initialize MongoDB connection."""
        if not settings.MONGO_URL:
            logger.error("MONGO_URL not configured for OCR training")
            return False

        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_URL,
                tls=True,
                tlsAllowInvalidCertificates=True
            )
            self.db = self.mongo_client[settings.DB_NAME or 'customerDB']
            logger.info("OCR training processor initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OCR training processor: {e}")
            return False

    async def process_learning_queue(self) -> Dict[str, Any]:
        """
        Process pending learning records to update bank patterns.

        Returns:
            Processing statistics and results
        """
        if not self.db:
            return {'error': 'Database not initialized'}

        try:
            # Get unprocessed learning records
            cursor = self.db.ocr_learning_queue.find(
                {'processed': False}
            ).limit(self.processing_batch_size)

            records = await cursor.to_list(length=self.processing_batch_size)

            if not records:
                return {
                    'processed_count': 0,
                    'message': 'No pending records to process'
                }

            # Group records by bank for batch processing
            records_by_bank = defaultdict(list)
            for record in records:
                bank_code = record.get('bank_code')
                if bank_code:
                    records_by_bank[bank_code].append(record)

            processing_stats = {
                'total_records': len(records),
                'banks_processed': 0,
                'patterns_updated': 0,
                'patterns_added': 0,
                'errors': []
            }

            # Process each bank's learning data
            for bank_code, bank_records in records_by_bank.items():
                try:
                    bank_result = await self._process_bank_learning(bank_code, bank_records)
                    processing_stats['banks_processed'] += 1
                    processing_stats['patterns_updated'] += bank_result.get('patterns_updated', 0)
                    processing_stats['patterns_added'] += bank_result.get('patterns_added', 0)

                except Exception as e:
                    error_msg = f"Failed to process {bank_code}: {str(e)}"
                    processing_stats['errors'].append(error_msg)
                    logger.error(error_msg)

            # Mark records as processed
            record_ids = [record['_id'] for record in records]
            await self.db.ocr_learning_queue.update_many(
                {'_id': {'$in': record_ids}},
                {
                    '$set': {
                        'processed': True,
                        'processed_at': datetime.now(timezone.utc)
                    }
                }
            )

            processing_stats['processed_at'] = datetime.now(timezone.utc).isoformat()

            logger.info(f"Processed {len(records)} learning records for {len(records_by_bank)} banks")

            return processing_stats

        except Exception as e:
            logger.error(f"Failed to process learning queue: {e}")
            return {'error': str(e)}

    async def _process_bank_learning(self, bank_code: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process learning records for a specific bank.

        Args:
            bank_code: Bank identifier (ABA, ACLEDA, etc.)
            records: List of learning records for this bank

        Returns:
            Processing results for this bank
        """
        if len(records) < self.min_samples_for_update:
            logger.debug(f"Insufficient samples for {bank_code} ({len(records)} < {self.min_samples_for_update})")
            return {'patterns_updated': 0, 'patterns_added': 0}

        # Analyze patterns from all records
        pattern_analysis = await self._analyze_patterns(bank_code, records)

        # Get current bank template
        current_template = await self._get_current_template(bank_code)

        # Determine which patterns to add/update
        new_patterns = self._select_patterns_for_addition(pattern_analysis, current_template)

        # Update bank template in database
        update_result = await self._update_bank_template(bank_code, new_patterns, pattern_analysis)

        # Update pattern cache
        if new_patterns:
            pattern_cache.update_patterns(bank_code, new_patterns)

        # Process merchant-specific patterns
        await self._process_merchant_patterns(records)

        return {
            'patterns_updated': update_result.get('patterns_updated', 0),
            'patterns_added': len(new_patterns),
            'analysis': pattern_analysis
        }

    async def _analyze_patterns(self, bank_code: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze extracted patterns from learning records.

        Args:
            bank_code: Bank identifier
            records: Learning records to analyze

        Returns:
            Pattern analysis results
        """
        pattern_frequency = defaultdict(lambda: defaultdict(int))
        pattern_confidence = defaultdict(lambda: defaultdict(list))
        pattern_success_rate = defaultdict(lambda: defaultdict(lambda: {'successes': 0, 'total': 0}))

        total_records = len(records)
        confidence_threshold = 0.80

        for record in records:
            verification_confidence = record.get('verification_confidence', 0)
            extracted_patterns = record.get('extracted_patterns', {})

            # Only process high-confidence verifications
            if verification_confidence < confidence_threshold:
                continue

            for pattern_type, regex_list in extracted_patterns.items():
                for regex_pattern in regex_list:
                    # Clean and normalize the pattern
                    normalized_pattern = self._normalize_pattern(regex_pattern)
                    if not normalized_pattern:
                        continue

                    # Count frequency
                    pattern_frequency[pattern_type][normalized_pattern] += 1

                    # Track confidence
                    pattern_confidence[pattern_type][normalized_pattern].append(verification_confidence)

                    # Track success rate (assume success since it's in learning queue)
                    pattern_success_rate[pattern_type][normalized_pattern]['successes'] += 1
                    pattern_success_rate[pattern_type][normalized_pattern]['total'] += 1

        # Calculate pattern statistics
        pattern_stats = {}
        for pattern_type in pattern_frequency:
            pattern_stats[pattern_type] = []

            for pattern, frequency in pattern_frequency[pattern_type].items():
                confidence_scores = pattern_confidence[pattern_type][pattern]
                success_info = pattern_success_rate[pattern_type][pattern]

                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                success_rate = success_info['successes'] / success_info['total']
                frequency_score = frequency / total_records

                # Calculate overall pattern score
                pattern_score = (avg_confidence * 0.4 + success_rate * 0.4 + frequency_score * 0.2)

                pattern_stats[pattern_type].append({
                    'pattern': pattern,
                    'frequency': frequency,
                    'avg_confidence': avg_confidence,
                    'success_rate': success_rate,
                    'frequency_score': frequency_score,
                    'overall_score': pattern_score,
                    'sample_size': len(confidence_scores)
                })

            # Sort by overall score
            pattern_stats[pattern_type].sort(key=lambda x: x['overall_score'], reverse=True)

        return {
            'bank_code': bank_code,
            'total_records_analyzed': total_records,
            'pattern_stats': pattern_stats,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _normalize_pattern(self, pattern: str) -> str:
        """
        Normalize and clean a regex pattern.

        Args:
            pattern: Raw regex pattern

        Returns:
            Cleaned pattern or empty string if invalid
        """
        if not pattern or len(pattern) < 5:
            return ""

        # Remove excessive whitespace
        normalized = " ".join(pattern.split())

        # Basic validation - must contain capture group
        if '(' not in normalized or ')' not in normalized:
            return ""

        # Remove patterns that are too specific (contain exact values)
        if any(char.isdigit() and normalized.count(char) > 3 for char in normalized):
            return ""

        return normalized

    def _select_patterns_for_addition(
        self,
        pattern_analysis: Dict[str, Any],
        current_template: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Select high-quality patterns to add to the bank template.

        Args:
            pattern_analysis: Results from pattern analysis
            current_template: Current bank template

        Returns:
            List of new patterns to add
        """
        new_patterns = []
        pattern_stats = pattern_analysis.get('pattern_stats', {})

        # Get existing patterns to avoid duplicates
        existing_patterns = set()
        if current_template and current_template.get('patterns'):
            for pattern_info in current_template['patterns']:
                existing_patterns.add(pattern_info.get('regex', ''))

        for pattern_type, patterns in pattern_stats.items():
            # Select top patterns that meet quality thresholds
            for pattern_info in patterns[:3]:  # Top 3 patterns per type
                if (pattern_info['overall_score'] >= 0.75 and
                    pattern_info['frequency'] >= 2 and
                    pattern_info['pattern'] not in existing_patterns):

                    new_pattern = {
                        'type': pattern_type,
                        'regex': pattern_info['pattern'],
                        'confidence': min(0.95, pattern_info['avg_confidence']),
                        'priority': len(new_patterns) + 1,
                        'source': 'auto_learning',
                        'frequency': pattern_info['frequency'],
                        'success_rate': pattern_info['success_rate'],
                        'sample_size': pattern_info['sample_size'],
                        'learned_at': datetime.now(timezone.utc).isoformat()
                    }

                    new_patterns.append(new_pattern)

        logger.info(f"Selected {len(new_patterns)} new patterns for addition")
        return new_patterns

    async def _get_current_template(self, bank_code: str) -> Dict[str, Any]:
        """Get current bank template from database."""
        try:
            template = await self.db.bank_format_templates.find_one({'bank_code': bank_code})
            return template.get('template', {}) if template else {}
        except Exception as e:
            logger.error(f"Failed to get template for {bank_code}: {e}")
            return {}

    async def _update_bank_template(
        self,
        bank_code: str,
        new_patterns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update bank template in database with new patterns.

        Args:
            bank_code: Bank identifier
            new_patterns: New patterns to add
            analysis: Pattern analysis results

        Returns:
            Update results
        """
        if not new_patterns:
            return {'patterns_updated': 0}

        try:
            # Get current template
            current_doc = await self.db.bank_format_templates.find_one({'bank_code': bank_code})

            if current_doc and current_doc.get('template'):
                # Update existing template
                template = current_doc['template']
                existing_patterns = template.get('patterns', [])

                # Add new patterns at the beginning (higher priority)
                all_patterns = new_patterns + existing_patterns

                # Limit total patterns to prevent bloat
                max_patterns_per_type = 8
                pattern_counts = defaultdict(int)
                filtered_patterns = []

                for pattern in all_patterns:
                    pattern_type = pattern.get('type', 'unknown')
                    if pattern_counts[pattern_type] < max_patterns_per_type:
                        filtered_patterns.append(pattern)
                        pattern_counts[pattern_type] += 1

                template['patterns'] = filtered_patterns
                template['last_updated'] = datetime.now(timezone.utc).isoformat()
                template['update_source'] = 'auto_learning'
                template['learning_stats'] = analysis

                # Update in database
                await self.db.bank_format_templates.update_one(
                    {'bank_code': bank_code},
                    {'$set': {'template': template}}
                )

            else:
                # Create new template
                new_template = {
                    'bank_code': bank_code,
                    'bank_name': bank_code,
                    'template': {
                        'bank_name': bank_code,
                        'patterns': new_patterns,
                        'confidence_base': 0.80,
                        'generated_at': datetime.now(timezone.utc).isoformat(),
                        'source': 'auto_learning',
                        'learning_stats': analysis
                    },
                    'validation_accuracy': 0.80,
                    'sample_count': analysis.get('total_records_analyzed', 0),
                    'last_updated': datetime.now(timezone.utc)
                }

                await self.db.bank_format_templates.insert_one(new_template)

            return {'patterns_updated': len(new_patterns)}

        except Exception as e:
            logger.error(f"Failed to update template for {bank_code}: {e}")
            return {'patterns_updated': 0, 'error': str(e)}

    async def _process_merchant_patterns(self, records: List[Dict[str, Any]]) -> None:
        """Process merchant-specific patterns from learning records."""
        for record in records:
            tenant_id = record.get('verified_data', {}).get('customer_id')  # Assuming customer_id maps to tenant
            if not tenant_id:
                continue

            bank_code = record.get('bank_code')
            verification_confidence = record.get('verification_confidence', 0)
            extracted_patterns = record.get('extracted_patterns', {})

            if verification_confidence < 0.85:  # Higher threshold for merchant patterns
                continue

            for pattern_type, regex_list in extracted_patterns.items():
                for regex_pattern in regex_list:
                    normalized_pattern = self._normalize_pattern(regex_pattern)
                    if normalized_pattern:
                        pattern_obj = {
                            'type': pattern_type,
                            'regex': normalized_pattern,
                            'confidence': verification_confidence,
                            'source': 'merchant_learning'
                        }

                        merchant_cache.add_merchant_pattern(
                            tenant_id=tenant_id,
                            bank_code=bank_code,
                            pattern=pattern_obj,
                            success_rate=verification_confidence
                        )

    async def cleanup_old_records(self, days_old: int = 7) -> int:
        """
        Clean up old processed learning records.

        Args:
            days_old: Remove records older than this many days

        Returns:
            Number of records removed
        """
        if not self.db:
            return 0

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            result = await self.db.ocr_learning_queue.delete_many({
                'processed': True,
                'processed_at': {'$lt': cutoff_date}
            })

            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old learning records")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0

    async def get_training_stats(self) -> Dict[str, Any]:
        """Get training job statistics."""
        if not self.db:
            return {'error': 'Database not initialized'}

        try:
            # Count learning queue status
            total_records = await self.db.ocr_learning_queue.count_documents({})
            processed_records = await self.db.ocr_learning_queue.count_documents({'processed': True})
            pending_records = total_records - processed_records

            # Get recent activity
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_processed = await self.db.ocr_learning_queue.count_documents({
                'processed_at': {'$gte': one_hour_ago}
            })

            # Count bank templates
            template_count = await self.db.bank_format_templates.count_documents({})

            # Recent learning activity by bank
            pipeline = [
                {'$match': {'learned_at': {'$gte': one_hour_ago}}},
                {'$group': {'_id': '$bank_code', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            recent_by_bank = await self.db.ocr_learning_queue.aggregate(pipeline).to_list(length=10)

            return {
                'total_learning_records': total_records,
                'processed_records': processed_records,
                'pending_records': pending_records,
                'recent_processed_1h': recent_processed,
                'bank_templates_count': template_count,
                'recent_activity_by_bank': {item['_id']: item['count'] for item in recent_by_bank},
                'cache_info': pattern_cache.get_cache_info(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get training stats: {e}")
            return {'error': str(e)}


# Background task runner
class OCRTrainingScheduler:
    """Manages scheduled training jobs."""

    def __init__(self):
        self.processor = OCRTrainingProcessor()
        self.is_running = False
        self.last_run = None

    async def start_background_processing(self):
        """Start background training processor."""
        if not await self.processor.initialize():
            logger.error("Failed to initialize OCR training processor")
            return

        self.is_running = True
        logger.info("Started OCR training background processor")

        while self.is_running:
            try:
                # Process learning queue every 5 minutes
                result = await self.processor.process_learning_queue()
                self.last_run = datetime.now(timezone.utc)

                if result.get('processed_count', 0) > 0:
                    logger.info(f"Training batch completed: {result}")

                # Cleanup old records once per hour
                if self.last_run and self.last_run.minute == 0:
                    await self.processor.cleanup_old_records()

                # Cleanup expired cache patterns
                if pattern_cache.should_cleanup():
                    pattern_cache.cleanup_expired()
                    merchant_cache.cleanup_expired_merchants()

            except Exception as e:
                logger.error(f"Training processor error: {e}")

            # Wait 5 minutes before next run
            await asyncio.sleep(300)

    def stop_background_processing(self):
        """Stop background processing."""
        self.is_running = False
        logger.info("Stopped OCR training background processor")

    async def process_now(self) -> Dict[str, Any]:
        """Process learning queue immediately (for manual triggers)."""
        if not self.processor.db:
            await self.processor.initialize()

        return await self.processor.process_learning_queue()


# Global instance
training_scheduler = OCRTrainingScheduler()