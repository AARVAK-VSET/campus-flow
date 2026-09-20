import asyncio

from backend.services import llm
from backend.services.analytics import get_medical_analytics
from backend.services.insight_cache import insight_cache
from backend.models.medical import MedicalRecord


class _Query:
    def __init__(self, records):
        self.records = records

    def all(self):
        return self.records


class _Database:
    def __init__(self, records):
        self.records = records

    def query(self, model):
        assert model is MedicalRecord
        return _Query(self.records)


def test_analytics_insight_cache_hits_and_invalidates_after_record_insertion(monkeypatch):
    calls = []

    async def fake_ask(system_prompt, user_prompt):
        calls.append(user_prompt)
        return f"insight-{len(calls)}"

    monkeypatch.setattr(llm, "_ask_llm", fake_ask)
    insight_cache.clear()
    records = [
        MedicalRecord(issue="Fever", severity="low", student_name="Asha", branch="CSE", year=2)
    ]
    db = _Database(records)

    async def exercise():
        first_stats = get_medical_analytics(db)
        first = await llm.get_medical_insights(first_stats)
        cached = await llm.get_medical_insights(get_medical_analytics(db))
        records.append(
            MedicalRecord(issue="Cough", severity="medium", student_name="Ravi", branch="ECE", year=1)
        )
        changed = await llm.get_medical_insights(get_medical_analytics(db))
        return first, cached, changed

    first, cached, changed = asyncio.run(exercise())

    assert (first, cached, changed) == ("insight-1", "insight-1", "insight-2")
    assert len(calls) == 2


def test_each_analytics_module_uses_a_separate_cache_key(monkeypatch):
    calls = 0

    async def fake_ask(system_prompt, user_prompt):
        nonlocal calls
        calls += 1
        return "insight"

    monkeypatch.setattr(llm, "_ask_llm", fake_ask)
    insight_cache.clear()

    async def exercise():
        data = {"total": 1}
        await llm.get_medical_insights(data)
        await llm.get_stationery_insights(data)
        await llm.get_parking_insights(data)

    asyncio.run(exercise())

    assert calls == 3


def test_cache_ttl_starts_after_slow_request():
    cache = insight_cache.__class__(ttl_seconds=1, max_entries=4)
    calls = 0

    async def create():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.2)
        return "insight"

    async def exercise():
        await cache.get_or_create("medical", {"total": 1}, create)
        await asyncio.sleep(0.9)
        await cache.get_or_create("medical", {"total": 1}, create)

    asyncio.run(exercise())

    assert calls == 1
