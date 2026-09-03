"""Background monitoring service for processing queued refund events."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.base import SessionLocal
from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.services.ml_service import get_inference_service

logger = logging.getLogger(__name__)


class QueueMonitor:
    """Background service that monitors the refund event queue and processes events through Sentinel."""

    def __init__(self, poll_interval_seconds: int = 5):
        self.poll_interval_seconds = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._monitoring = False

        # Statistics
        self.events_received = 0
        self.events_processed = 0
        self.events_failed = 0
        self.last_processed_event: Optional[datetime] = None
        self.last_processed_refund_id: Optional[str] = None
        self.last_processed_risk_band: Optional[str] = None
        self.last_processed_action: Optional[str] = None

    @property
    def monitoring(self) -> bool:
        return self._monitoring

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start the background monitoring task."""
        if self._running:
            logger.warning("Queue monitor already running")
            return

        self._running = True
        self._monitoring = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Queue monitor started")

    async def stop(self) -> None:
        """Stop the background monitoring task."""
        if not self._running:
            logger.warning("Queue monitor not running")
            return

        self._running = False
        self._monitoring = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Queue monitor stopped")

    async def pause(self) -> None:
        """Pause monitoring without stopping the task."""
        self._monitoring = False
        logger.info("Queue monitor paused")

    async def resume(self) -> None:
        """Resume monitoring."""
        if not self._running:
            logger.warning("Cannot resume: monitor not running")
            return
        self._monitoring = True
        logger.info("Queue monitor resumed")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop that polls the queue and processes events."""
        while self._running:
            try:
                if self._monitoring:
                    await self._process_queue()
            except Exception as e:
                logger.error(f"Error in queue monitor loop: {e}")

            await asyncio.sleep(self.poll_interval_seconds)

    async def _process_queue(self) -> None:
        """Process pending refund events from the queue."""
        db = SessionLocal()
        try:
            # Get pending events (oldest first)
            pending_events = db.query(RefundEventQueue).filter(
                RefundEventQueue.status == "pending"
            ).order_by(RefundEventQueue.created_at.asc()).limit(10).all()

            if not pending_events:
                return

            service = get_inference_service()

            for event in pending_events:
                if not self._monitoring:
                    break

                try:
                    # Mark as processing
                    event.status = "processing"
                    db.commit()

                    # Score the refund using existing inference pipeline
                    result = service.score_refund(event.refund_id)
                    if result is None:
                        event.status = "failed"
                        event.error_message = f"Refund {event.refund_id} not found in historical data"
                        event.processed_at = datetime.utcnow()
                        self.events_failed += 1
                        db.commit()
                        continue

                    # Persist the case using the same logic as the ingestion endpoint
                    case = RiskCase(
                        customer_id=result["customer_id"],
                        refund_id=result["refund_id"],
                        order_id=result["order_id"],
                        risk_score=result["risk_score"],
                        risk_band=result["risk_band"],
                        recommended_action=result["recommended_action"],
                        status="pending",
                    )
                    db.add(case)
                    db.flush()

                    # Persist evidence
                    from backend.app.models.risk_case import CaseEvidence
                    for ev in result["evidence"]:
                        case_evidence = CaseEvidence(
                            case_id=case.id,
                            category=ev["category"],
                            metric=ev["metric"],
                            value=str(ev["value"]),
                            description=ev["description"],
                        )
                        db.add(case_evidence)

                    # Update event status
                    event.status = "completed"
                    event.processed_at = datetime.utcnow()
                    self.events_processed += 1
                    self.last_processed_event = datetime.utcnow()
                    self.last_processed_refund_id = result["refund_id"]
                    self.last_processed_risk_band = result["risk_band"]
                    self.last_processed_action = result["recommended_action"]

                    db.commit()
                    logger.info(f"Processed refund {event.refund_id}: risk_score={result['risk_score']:.4f}, band={result['risk_band']}, action={result['recommended_action']}")

                except Exception as e:
                    logger.error(f"Error processing refund {event.refund_id}: {e}")
                    event.status = "failed"
                    event.error_message = str(e)
                    event.processed_at = datetime.utcnow()
                    self.events_failed += 1
                    db.commit()

        finally:
            db.close()

    def get_stats(self) -> dict:
        """Get current monitoring statistics."""
        db = SessionLocal()
        try:
            queue_pending = db.query(RefundEventQueue).filter(RefundEventQueue.status == "pending").count()
            return {
                "connected": True,
                "monitoring": self._monitoring,
                "last_processed_event": self.last_processed_event,
                "last_processed_refund_id": self.last_processed_refund_id,
                "last_processed_risk_band": self.last_processed_risk_band,
                "last_processed_action": self.last_processed_action,
                "events_received": self.events_received,
                "events_processed": self.events_processed,
                "events_failed": self.events_failed,
                "queue_pending": queue_pending,
            }
        finally:
            db.close()

    def increment_received(self) -> None:
        """Increment the received events counter."""
        self.events_received += 1


# Global instance
_queue_monitor: Optional[QueueMonitor] = None


def get_queue_monitor() -> QueueMonitor:
    """Get or create the global queue monitor instance."""
    global _queue_monitor
    if _queue_monitor is None:
        _queue_monitor = QueueMonitor()
    return _queue_monitor


async def start_queue_monitor() -> None:
    """Start the queue monitor on application startup."""
    monitor = get_queue_monitor()
    await monitor.start()


async def stop_queue_monitor() -> None:
    """Stop the queue monitor on application shutdown."""
    monitor = get_queue_monitor()
    await monitor.stop()