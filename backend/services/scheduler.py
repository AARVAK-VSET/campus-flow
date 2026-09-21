"""Background scheduler that broadcasts recurring announcements.

An announcement is *recurring* when it is active and its ``repeat_interval``
(in seconds) is greater than zero. The scheduler wakes up every
``poll_interval`` seconds, reads the recurring announcements from the database
and, for every one whose interval has expired:

1. generates speech audio for the message (text-to-speech), and
2. publishes a :class:`BroadcastEvent` to the subscribers and to the in-memory
   ``history`` (readable through ``GET /api/announcements/broadcasts``).

Schedule rules
--------------
* The first broadcast happens one full interval after the scheduler first sees
  the announcement, so nothing is played the moment it is created or the
  server starts.
* After that it repeats every ``repeat_interval`` seconds without drifting.
* If the server was paused for several intervals, only ONE broadcast is made
  (no burst of catch-up announcements).
* Deleting or deactivating an announcement, or setting its interval to 0, stops
  it. Changing the interval restarts its countdown.
"""
import asyncio
import inspect
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Deque, Dict, List, Optional, Union

from backend.database import SessionLocal
from backend.models.announcement import Announcement
from backend.services.tts import generate_speech

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecurringAnnouncement:
    """The announcement columns the scheduler needs, copied out of the database."""

    id: int
    message: str
    language: str
    repeat_interval: int


@dataclass(frozen=True)
class BroadcastEvent:
    """One broadcast of a recurring announcement."""

    announcement_id: int
    message: str
    language: str
    audio_url: Optional[str]
    triggered_at: datetime
    error: Optional[str] = None  # set when speech generation failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "announcement_id": self.announcement_id,
            "message": self.message,
            "language": self.language,
            "audio_url": self.audio_url,
            "triggered_at": self.triggered_at.isoformat(),
            "error": self.error,
        }


Subscriber = Callable[[BroadcastEvent], Union[None, Awaitable[None]]]


@dataclass
class _Schedule:
    interval: int
    due: float


class AnnouncementScheduler:
    def __init__(
        self,
        session_factory: Callable[[], Any] = SessionLocal,
        speech_generator: Callable[..., Awaitable[str]] = generate_speech,
        clock: Callable[[], float] = time.monotonic,
        poll_interval: float = 1.0,
        speech_timeout: float = 30.0,
        history_size: int = 100,
    ):
        self.session_factory = session_factory
        self.speech_generator = speech_generator
        self.clock = clock  # seconds; only differences matter, so it can be faked in tests
        self.poll_interval = poll_interval
        self.speech_timeout = speech_timeout
        self.history: Deque[BroadcastEvent] = deque(maxlen=history_size)
        self._schedules: Dict[int, _Schedule] = {}
        self._subscribers: List[Subscriber] = []
        self._task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------ lifecycle

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        """Start the background worker. Must be called while an event loop is running."""
        if self.is_running:
            return
        self._task = asyncio.get_running_loop().create_task(
            self._run(), name="announcement-scheduler"
        )

    async def stop(self) -> None:
        """Stop the background worker and wait until it has finished."""
        task, self._task = self._task, None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        logger.info("Announcement scheduler started (checking every %.1fs)", self.poll_interval)
        try:
            while True:
                # Sleep first: nothing touches the database the moment the app starts.
                await asyncio.sleep(self.poll_interval)
                try:
                    await self.run_pending()
                except Exception:
                    # One bad tick (e.g. a database hiccup) must not kill the worker.
                    logger.exception("Announcement scheduler tick failed")
        finally:
            logger.info("Announcement scheduler stopped")

    # ------------------------------------------------------------ broadcasting

    def subscribe(self, callback: Subscriber) -> None:
        """Call ``callback(event)`` (sync or async) for every broadcast."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Subscriber) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def run_pending(self) -> List[BroadcastEvent]:
        """Run one scheduler tick and broadcast every announcement whose interval expired."""
        now = self.clock()
        recurring = await asyncio.to_thread(self._load_recurring)
        due = self._collect_due(recurring, now)
        return [await self._broadcast(announcement) for announcement in due]

    def _load_recurring(self) -> List[RecurringAnnouncement]:
        with self.session_factory() as db:
            rows = (
                db.query(Announcement)
                .filter(Announcement.is_active.is_(True), Announcement.repeat_interval > 0)
                .order_by(Announcement.id)
                .all()
            )
            return [
                RecurringAnnouncement(row.id, row.message, row.language or "en", row.repeat_interval)
                for row in rows
            ]

    def _collect_due(
        self, recurring: List[RecurringAnnouncement], now: float
    ) -> List[RecurringAnnouncement]:
        # Forget announcements that were deleted, deactivated or made non-recurring.
        current_ids = {announcement.id for announcement in recurring}
        for stale_id in set(self._schedules) - current_ids:
            del self._schedules[stale_id]

        due = []
        for announcement in recurring:
            interval = announcement.repeat_interval
            schedule = self._schedules.get(announcement.id)
            if schedule is None or schedule.interval != interval:
                # Newly seen (or its interval changed): count one full interval from now.
                self._schedules[announcement.id] = _Schedule(interval, now + interval)
            elif now >= schedule.due:
                # Move on by whole intervals so a long pause gives one broadcast, not a burst.
                missed_intervals = int((now - schedule.due) // interval) + 1
                schedule.due += missed_intervals * interval
                due.append(announcement)
        return due

    async def _broadcast(self, announcement: RecurringAnnouncement) -> BroadcastEvent:
        audio_url = None
        error = None
        try:
            audio_path = await asyncio.wait_for(
                self.speech_generator(announcement.message, announcement.language),
                timeout=self.speech_timeout,
            )
            audio_url = f"/audio/{os.path.basename(audio_path)}"
        except Exception as exc:
            # A broken or slow speech service must not stop the schedule; the text is
            # still broadcast, with the error attached.
            error = str(exc) or exc.__class__.__name__
            logger.warning("Speech generation failed for announcement %s: %s", announcement.id, error)

        event = BroadcastEvent(
            announcement_id=announcement.id,
            message=announcement.message,
            language=announcement.language,
            audio_url=audio_url,
            triggered_at=datetime.now(timezone.utc),
            error=error,
        )
        self.history.append(event)
        await self._notify(event)
        logger.info("Broadcast announcement %s (audio: %s)", announcement.id, audio_url or "none")
        return event

    async def _notify(self, event: BroadcastEvent) -> None:
        for callback in list(self._subscribers):
            try:
                result = callback(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Broadcast subscriber %r failed", callback)


# The scheduler used by the application.
scheduler = AnnouncementScheduler()


@asynccontextmanager
async def scheduler_lifespan(app):
    """Start the scheduler with the application and stop it on shutdown."""
    scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
