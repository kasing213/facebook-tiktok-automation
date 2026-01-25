# api-gateway/src/services/init_auto_learning.py
"""
Auto-Learning OCR Initialization

This script initializes the auto-learning OCR system on startup.
It should be called when the api-gateway starts to ensure all
learning components are ready.
"""

import logging
import asyncio
from src.services.smart_ocr_service import smart_ocr
from src.services.auto_learning_ocr import auto_learning_ocr
from src.jobs.ocr_training_job import training_scheduler

logger = logging.getLogger(__name__)


async def initialize_auto_learning_system():
    """
    Initialize all components of the auto-learning OCR system.

    This should be called during api-gateway startup to ensure:
    1. Auto-learning OCR service is connected to MongoDB
    2. Pattern cache is loaded with existing templates
    3. Background training job is running
    4. Smart OCR service is ready
    """
    logger.info("🚀 Initializing Auto-Learning OCR System...")

    try:
        # Step 1: Initialize auto-learning OCR service
        logger.info("📚 Initializing auto-learning OCR...")
        await auto_learning_ocr.initialize()

        # Step 2: Initialize smart OCR service
        logger.info("🧠 Initializing smart OCR service...")
        await smart_ocr.initialize()

        # Step 3: Start background training processor
        logger.info("⚙️ Starting background training processor...")
        asyncio.create_task(training_scheduler.start_background_processing())

        # Step 4: Verify system health
        health = await smart_ocr.health_check()
        if health.get('overall') == 'healthy':
            logger.info("✅ Auto-Learning OCR System initialized successfully!")

            # Log system capabilities
            stats = await smart_ocr.get_service_stats()
            learning_stats = stats.get('learning_system', {})

            logger.info(f"📊 System ready:")
            logger.info(f"   • Banks with patterns: {learning_stats.get('banks_with_patterns', 0)}")
            logger.info(f"   • Learning records: {learning_stats.get('total_learning_records', 0)}")
            logger.info(f"   • Training processor: {'Running' if training_scheduler.is_running else 'Stopped'}")

        else:
            logger.warning(f"⚠️ System initialized with warnings: {health}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize auto-learning OCR system: {e}")
        logger.error("🔄 Falling back to basic OCR service")
        return False


async def shutdown_auto_learning_system():
    """
    Gracefully shutdown the auto-learning system.

    This should be called during api-gateway shutdown.
    """
    logger.info("🛑 Shutting down Auto-Learning OCR System...")

    try:
        # Stop background training
        training_scheduler.stop_background_processing()

        # Close MongoDB connections
        if auto_learning_ocr.mongo_client:
            auto_learning_ocr.mongo_client.close()

        if training_scheduler.processor.mongo_client:
            training_scheduler.processor.mongo_client.close()

        logger.info("✅ Auto-Learning OCR System shutdown complete")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def check_system_requirements():
    """
    Check if system requirements for auto-learning are met.

    Returns:
        Dict with requirement check results
    """
    requirements = {
        'mongo_url': {'required': True, 'status': 'unknown'},
        'db_name': {'required': True, 'status': 'unknown'},
        'ocr_fallback': {'required': True, 'status': 'unknown'},
        'overall': 'unknown'
    }

    try:
        from src.config import settings

        # Check MongoDB URL
        if hasattr(settings, 'MONGO_URL') and settings.MONGO_URL:
            requirements['mongo_url']['status'] = 'ok'
        else:
            requirements['mongo_url']['status'] = 'missing'

        # Check Database name
        if hasattr(settings, 'DB_NAME') and settings.DB_NAME:
            requirements['db_name']['status'] = 'ok'
        else:
            requirements['db_name']['status'] = 'missing'

        # Check OCR fallback service
        from src.services.ocr_service import ocr_service
        if ocr_service.is_configured():
            requirements['ocr_fallback']['status'] = 'ok'
        else:
            requirements['ocr_fallback']['status'] = 'missing'

        # Overall status
        all_ok = all(req['status'] == 'ok' for req in requirements.values() if req.get('required'))
        requirements['overall'] = 'ready' if all_ok else 'incomplete'

    except Exception as e:
        logger.error(f"Requirements check failed: {e}")
        requirements['overall'] = 'error'

    return requirements


async def get_system_status():
    """
    Get current status of the auto-learning system.

    Returns:
        Dict with system status information
    """
    try:
        # Check requirements
        requirements = check_system_requirements()

        # Get health status
        health = await smart_ocr.health_check()

        # Get service statistics
        stats = await smart_ocr.get_service_stats()

        return {
            'requirements': requirements,
            'health': health,
            'statistics': stats,
            'features': {
                'auto_learning': health.get('auto_learning') == 'healthy',
                'pattern_caching': health.get('pattern_cache') == 'healthy',
                'background_training': health.get('training_scheduler') == 'active',
                'cost_optimization': stats.get('pattern_success_rate', 0) > 0
            },
            'timestamp': stats.get('timestamp')
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            'requirements': {'overall': 'error'},
            'health': {'overall': 'error'},
            'statistics': {'error': str(e)},
            'features': {
                'auto_learning': False,
                'pattern_caching': False,
                'background_training': False,
                'cost_optimization': False
            }
        }


# Convenience function for health checks
async def quick_health_check():
    """Quick health check for monitoring."""
    try:
        status = await get_system_status()
        return {
            'healthy': status['health'].get('overall') == 'healthy',
            'learning_active': status['features']['auto_learning'],
            'training_active': status['features']['background_training'],
            'cost_savings_active': status['features']['cost_optimization']
        }
    except Exception:
        return {
            'healthy': False,
            'learning_active': False,
            'training_active': False,
            'cost_savings_active': False
        }