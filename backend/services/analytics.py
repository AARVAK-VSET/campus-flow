from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models.medical import MedicalRecord
from backend.models.stationery import StationeryItem
from backend.models.parking import ParkingRecord


def get_medical_analytics(db: Session) -> dict:
    records = db.query(MedicalRecord).all()
    if not records:
        return {"total": 0, "by_issue": [], "by_severity": [], "daily_visits": [], "trends": []}

    issue_counts = Counter(r.issue for r in records)
    severity_counts = Counter(r.severity for r in records)

    # Daily visits (last 30 days)
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    recent = [r for r in records if r.date_time and r.date_time >= thirty_days_ago]
    daily = Counter(r.date_time.strftime("%Y-%m-%d") for r in recent)
    daily_sorted = sorted(daily.items(), key=lambda x: x[0])

    # Trend: top rising issues
    trends = []
    for issue, count in issue_counts.most_common(5):
        trends.append({"issue": issue, "count": count, "risk": "high" if count > 5 else "medium" if count > 2 else "low"})

    return {
        "total": len(records),
        "by_issue": [{"name": k, "count": v} for k, v in issue_counts.most_common(10)],
        "by_severity": [{"name": k, "count": v} for k, v in severity_counts.items()],
        "daily_visits": [{"date": d, "count": c} for d, c in daily_sorted],
        "trends": trends,
    }


def get_stationery_analytics(db: Session) -> dict:
    items = db.query(StationeryItem).all()
    if not items:
        return {"total": 0, "by_category": [], "top_demand": [], "low_stock": [], "stock_overview": []}

    category_counts = Counter(i.category or "Uncategorized" for i in items)
    by_demand = sorted(items, key=lambda i: i.student_demand, reverse=True)
    low_stock = [i for i in items if i.quantity < 10]

    return {
        "total": len(items),
        "by_category": [{"name": k, "count": v} for k, v in category_counts.items()],
        "top_demand": [{"name": i.item_name, "demand": i.student_demand, "quantity": i.quantity} for i in by_demand[:10]],
        "low_stock": [{"name": i.item_name, "quantity": i.quantity, "category": i.category} for i in low_stock],
        "stock_overview": [{"name": i.item_name, "quantity": i.quantity, "price": i.price} for i in items],
    }


def get_parking_analytics(db: Session) -> dict:
    records = db.query(ParkingRecord).all()
    if not records:
        return {"total": 0, "occupied": 0, "free": 0, "hourly": [], "slot_usage": []}

    occupied = sum(1 for r in records if r.status == "occupied")
    free = sum(1 for r in records if r.status == "free")

    # Hourly distribution
    hourly = Counter(r.time_in.hour for r in records if r.time_in)
    hourly_sorted = sorted(hourly.items(), key=lambda x: x[0])

    # Slot usage frequency
    slot_usage = Counter(r.slot_number for r in records)

    return {
        "total": len(records),
        "occupied": occupied,
        "free": free,
        "hourly": [{"hour": h, "count": c} for h, c in hourly_sorted],
        "slot_usage": [{"slot": s, "count": c} for s, c in sorted(slot_usage.items())],
    }

