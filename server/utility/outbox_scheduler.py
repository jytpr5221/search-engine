import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OutboxScheduler:
    """Background scheduler for processing outbox entries"""
    
    def __init__(self, outbox_controller, interval: int = 30):
        self.outbox_controller = outbox_controller
        self.interval = interval
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info(f"Outbox scheduler started (interval: {self.interval}s)")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox scheduler stopped")
    
    async def _run(self):
        """Main scheduler loop"""
        while self.running:
            try:
                logger.debug(f"Processing outbox at {datetime.utcnow()}")
                result = await self.outbox_controller.process_pending_outbox()
                if result.get('processed', 0) > 0:
                    logger.info(f"Processed {result['processed']} outbox entries")
            except Exception as e:
                logger.error(f"Error in outbox scheduler: {e}")
            
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
