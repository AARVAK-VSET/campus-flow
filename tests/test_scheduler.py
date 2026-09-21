"""Tests for the recurring-announcement scheduler.

Timing is controlled with a fake clock, so the tests are instant and never depend
on real waiting. The database is a throw-away in-memory SQLite database and text
to speech is replaced by a fake, so nothing is written to disk or sent over the
network.
"""
import asyncio
import time
from collections import deque
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.announcement import Announcement
from backend.routers import announcements
from backend.services import scheduler as scheduler_module
from backend.services.scheduler import AnnouncementScheduler, BroadcastEvent


class FakeClock:
    """A clock the test moves by hand (seconds)."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Announcement.__table__.create(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()


@pytest.fixture()
def clock():
    return FakeClock()


@pytest.fixture()
def spoken():
    """Every (text, language) the fake speech service was asked to speak."""
    return []


@pytest.fixture()
def sched(session_factory, clock, spoken):
    async def fake_speech(text, language="en"):
        spoken.append((text, language))
        return f"/cache/speech-{len(spoken)}.mp3"

    return AnnouncementScheduler(
        session_factory=session_factory,
        speech_generator=fake_speech,
        clock=clock,
        poll_interval=0.01,
    )


def add_announcement(factory, **fields):
    values = {"message": "Library closes at 8 PM", "language": "en", "repeat_interval": 60}
    values.update(fields)
    with factory() as db:
        announcement = Announcement(**values)
        db.add(announcement)
        db.commit()
        return announcement.id


def update_announcement(factory, announcement_id, **fields):
    with factory() as db:
        db.query(Announcement).filter(Announcement.id == announcement_id).update(fields)
        db.commit()


def delete_announcement(factory, announcement_id):
    with factory() as db:
        db.query(Announcement).filter(Announcement.id == announcement_id).delete()
        db.commit()


def tick(scheduler):
    """Run one scheduler check and return the broadcasts it made."""
    return asyncio.run(scheduler.run_pending())


async def wait_until(condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "condition was not met in time"
        await asyncio.sleep(0.005)


# ------------------------------------------------------------ interval timing


def test_first_broadcast_is_one_interval_after_the_announcement_is_seen(
    sched, session_factory, clock
):
    add_announcement(session_factory, repeat_interval=300)

    assert tick(sched) == []  # t=0: the scheduler notices it, countdown starts
    clock.advance(299)
    assert tick(sched) == []  # one second early
    clock.advance(1)
    assert len(tick(sched)) == 1  # t=300: the interval has expired


def test_repeats_every_interval(sched, session_factory, clock, spoken):
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)

    for _ in range(5):
        clock.advance(60)
        assert len(tick(sched)) == 1

    assert len(spoken) == 5


def test_late_checks_do_not_make_the_schedule_drift(sched, session_factory, clock):
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)

    clock.now = 61  # checked 1 second late: due at 60
    assert len(tick(sched)) == 1
    clock.now = 119
    assert tick(sched) == []
    clock.now = 120  # the next one is still due at 120, not 121
    assert len(tick(sched)) == 1


def test_long_pause_gives_one_broadcast_not_a_burst(sched, session_factory, clock):
    add_announcement(session_factory, repeat_interval=10)
    tick(sched)

    clock.now = 95  # nine intervals missed
    assert len(tick(sched)) == 1
    clock.now = 99
    assert tick(sched) == []
    clock.now = 100
    assert len(tick(sched)) == 1


def test_each_announcement_follows_its_own_interval(sched, session_factory, clock):
    fast = add_announcement(session_factory, message="Fast", repeat_interval=10)
    slow = add_announcement(session_factory, message="Slow", repeat_interval=25)
    tick(sched)

    fired = []
    for _ in range(5):
        clock.advance(10)
        fired += [event.announcement_id for event in tick(sched)]

    # t=10,20,30,40,50: "fast" every time, "slow" at 25 -> seen at 30, and 50
    assert fired.count(fast) == 5
    assert fired.count(slow) == 2


# --------------------------------------------------- which announcements run


def test_inactive_announcements_are_never_broadcast(sched, session_factory, clock):
    add_announcement(session_factory, is_active=False)
    tick(sched)

    clock.advance(1000)

    assert tick(sched) == []


@pytest.mark.parametrize("interval", [0, None])
def test_announcements_without_a_repeat_interval_are_never_broadcast(
    sched, session_factory, clock, interval
):
    add_announcement(session_factory, repeat_interval=interval)
    tick(sched)

    clock.advance(1000)

    assert tick(sched) == []


def test_deleted_announcement_stops_being_broadcast(sched, session_factory, clock):
    announcement_id = add_announcement(session_factory, repeat_interval=60)
    tick(sched)
    clock.advance(60)
    assert len(tick(sched)) == 1

    delete_announcement(session_factory, announcement_id)
    clock.advance(600)

    assert tick(sched) == []


def test_deactivated_announcement_stops_and_restarts_its_countdown_when_reactivated(
    sched, session_factory, clock
):
    announcement_id = add_announcement(session_factory, repeat_interval=60)
    tick(sched)  # t=0

    clock.now = 70
    update_announcement(session_factory, announcement_id, is_active=False)
    assert tick(sched) == []

    clock.now = 100
    update_announcement(session_factory, announcement_id, is_active=True)
    assert tick(sched) == []  # countdown restarts: due at 160
    clock.now = 159
    assert tick(sched) == []
    clock.now = 160
    assert len(tick(sched)) == 1


def test_changing_the_interval_restarts_the_countdown(sched, session_factory, clock):
    announcement_id = add_announcement(session_factory, repeat_interval=60)
    tick(sched)  # t=0

    clock.now = 30
    update_announcement(session_factory, announcement_id, repeat_interval=10)
    assert tick(sched) == []  # new countdown: due at 40
    clock.now = 39
    assert tick(sched) == []
    clock.now = 40
    assert len(tick(sched)) == 1


def test_announcement_created_later_is_picked_up(sched, session_factory, clock):
    tick(sched)  # nothing exists yet

    clock.now = 500
    add_announcement(session_factory, repeat_interval=60)
    assert tick(sched) == []
    clock.now = 560
    assert len(tick(sched)) == 1


# ------------------------------------------- speech generation and broadcasting


def test_broadcast_generates_speech_and_publishes_an_event(sched, session_factory, clock, spoken):
    announcement_id = add_announcement(
        session_factory, message="Namaste, class starts", language="hi", repeat_interval=60
    )
    tick(sched)
    clock.advance(60)

    (event,) = tick(sched)

    assert spoken == [("Namaste, class starts", "hi")]
    assert event.announcement_id == announcement_id
    assert event.message == "Namaste, class starts"
    assert event.language == "hi"
    assert event.audio_url == "/audio/speech-1.mp3"
    assert event.error is None
    assert event.triggered_at.tzinfo is not None
    assert list(sched.history) == [event]


def test_speech_failure_is_reported_but_the_schedule_keeps_running(
    session_factory, clock
):
    calls = []

    async def flaky_speech(text, language="en"):
        calls.append(text)
        if len(calls) == 1:
            raise RuntimeError("speech service down")
        return "/cache/ok.mp3"

    sched = AnnouncementScheduler(
        session_factory=session_factory, speech_generator=flaky_speech, clock=clock
    )
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)

    clock.advance(60)
    (failed,) = tick(sched)
    clock.advance(60)
    (recovered,) = tick(sched)

    assert failed.audio_url is None
    assert failed.error == "speech service down"
    assert failed.message == "Library closes at 8 PM"  # the text is still broadcast
    assert recovered.audio_url == "/audio/ok.mp3"
    assert recovered.error is None


def test_slow_speech_service_times_out(session_factory, clock):
    async def hanging_speech(text, language="en"):
        await asyncio.sleep(30)

    sched = AnnouncementScheduler(
        session_factory=session_factory,
        speech_generator=hanging_speech,
        clock=clock,
        speech_timeout=0.05,
    )
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)
    clock.advance(60)

    (event,) = tick(sched)

    assert event.audio_url is None
    assert event.error == "TimeoutError"


def test_subscribers_receive_every_event(sched, session_factory, clock):
    received_sync, received_async = [], []

    async def async_subscriber(event):
        received_async.append(event)

    sched.subscribe(received_sync.append)
    sched.subscribe(async_subscriber)
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)
    clock.advance(60)

    (event,) = tick(sched)

    assert received_sync == [event]
    assert received_async == [event]


def test_failing_subscriber_does_not_stop_the_others(sched, session_factory, clock):
    received = []

    def broken_subscriber(event):
        raise RuntimeError("boom")

    sched.subscribe(broken_subscriber)
    sched.subscribe(received.append)
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)
    clock.advance(60)

    tick(sched)

    assert len(received) == 1


def test_unsubscribed_callback_is_not_called(sched, session_factory, clock):
    received = []
    sched.subscribe(received.append)
    sched.unsubscribe(received.append)
    add_announcement(session_factory, repeat_interval=60)
    tick(sched)
    clock.advance(60)

    tick(sched)

    assert received == []


def test_history_keeps_only_the_most_recent_events(session_factory, clock):
    async def speech(text, language="en"):
        return "/cache/a.mp3"

    sched = AnnouncementScheduler(
        session_factory=session_factory, speech_generator=speech, clock=clock, history_size=2
    )
    add_announcement(session_factory, repeat_interval=10)
    tick(sched)

    for _ in range(3):
        clock.advance(10)
        tick(sched)

    assert len(sched.history) == 2


# ------------------------------------------------- the background worker itself


def test_background_worker_broadcasts_when_the_interval_expires(
    sched, session_factory, clock, spoken
):
    add_announcement(session_factory, repeat_interval=60)

    async def scenario():
        await sched.run_pending()  # t=0: the scheduler notices the announcement
        sched.start()
        try:
            clock.now = 60
            await wait_until(lambda: len(spoken) == 1)
            clock.now = 120
            await wait_until(lambda: len(spoken) == 2)
        finally:
            await sched.stop()

    asyncio.run(scenario())

    assert len(sched.history) == 2


def test_start_is_idempotent_and_stop_cleans_up(sched):
    async def scenario():
        assert not sched.is_running
        sched.start()
        first_task = sched._task
        sched.start()  # second start must not create a second worker
        assert sched._task is first_task
        assert sched.is_running

        await sched.stop()
        assert not sched.is_running
        assert first_task.done()

        await sched.stop()  # stopping twice is harmless

        sched.start()  # and it can be started again
        assert sched.is_running
        await sched.stop()

    asyncio.run(scenario())


def test_stop_does_not_wait_for_a_broadcast_in_progress(session_factory, clock):
    started = []

    async def never_finishes(text, language="en"):
        started.append(text)
        await asyncio.sleep(3600)

    sched = AnnouncementScheduler(
        session_factory=session_factory,
        speech_generator=never_finishes,
        clock=clock,
        poll_interval=0.01,
        speech_timeout=3600,
    )
    add_announcement(session_factory, repeat_interval=60)

    async def scenario():
        await sched.run_pending()
        sched.start()
        clock.now = 60
        await wait_until(lambda: started)
        await asyncio.wait_for(sched.stop(), timeout=2)

    asyncio.run(scenario())

    assert not sched.is_running


def test_worker_survives_a_failing_check(session_factory, clock, spoken):
    class FlakyFactory:
        """Fails the first time the scheduler reads the database, then works."""

        def __init__(self, factory):
            self.factory = factory
            self.calls = 0

        def __call__(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("database unavailable")
            return self.factory()

    async def speech(text, language="en"):
        spoken.append(text)
        return "/cache/a.mp3"

    flaky = FlakyFactory(session_factory)
    sched = AnnouncementScheduler(
        session_factory=flaky, speech_generator=speech, clock=clock, poll_interval=0.01
    )
    add_announcement(session_factory, repeat_interval=60)

    async def scenario():
        sched.start()
        try:
            await wait_until(lambda: flaky.calls >= 2)  # it kept going after the error
            assert sched.is_running
        finally:
            await sched.stop()

    asyncio.run(scenario())


# ------------------------------------------------------ application lifecycle


def test_scheduler_starts_and_stops_with_the_application(monkeypatch, session_factory):
    monkeypatch.setattr(scheduler_module.scheduler, "session_factory", session_factory)
    app = FastAPI()
    app.include_router(announcements.router)

    assert not scheduler_module.scheduler.is_running
    with TestClient(app):
        assert scheduler_module.scheduler.is_running
    assert not scheduler_module.scheduler.is_running


# ------------------------------------------------------------ HTTP endpoint


def _event(announcement_id, message):
    return BroadcastEvent(
        announcement_id=announcement_id,
        message=message,
        language="en",
        audio_url=f"/audio/{announcement_id}.mp3",
        triggered_at=datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def broadcasts_client(monkeypatch):
    history = deque(maxlen=100)
    monkeypatch.setattr(scheduler_module.scheduler, "history", history)
    app = FastAPI()
    app.include_router(announcements.router)
    return TestClient(app), history  # not used as a context manager: no scheduler is started


def test_broadcasts_endpoint_is_empty_at_first(broadcasts_client):
    client, _ = broadcasts_client

    response = client.get("/api/announcements/broadcasts")

    assert response.status_code == 200
    assert response.json() == []


def test_broadcasts_endpoint_lists_newest_first(broadcasts_client):
    client, history = broadcasts_client
    history.extend([_event(1, "first"), _event(2, "second"), _event(3, "third")])

    body = client.get("/api/announcements/broadcasts").json()

    assert [item["message"] for item in body] == ["third", "second", "first"]
    assert body[0] == {
        "announcement_id": 3,
        "message": "third",
        "language": "en",
        "audio_url": "/audio/3.mp3",
        "triggered_at": "2026-09-22T10:00:00+00:00",
        "error": None,
    }


def test_broadcasts_endpoint_supports_a_limit(broadcasts_client):
    client, history = broadcasts_client
    history.extend([_event(1, "first"), _event(2, "second"), _event(3, "third")])

    body = client.get("/api/announcements/broadcasts?limit=2").json()

    assert [item["message"] for item in body] == ["third", "second"]


@pytest.mark.parametrize("limit", [0, 101, "abc"])
def test_broadcasts_endpoint_rejects_invalid_limits(broadcasts_client, limit):
    client, _ = broadcasts_client

    assert client.get(f"/api/announcements/broadcasts?limit={limit}").status_code == 422
