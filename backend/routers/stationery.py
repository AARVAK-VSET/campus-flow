from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.stationery import StationeryItem
from backend.schemas import StationeryItemCreate, StationeryItemUpdate, StationeryItemOut
from backend.services.analytics import get_stationery_analytics
from backend.services.llm import get_stationery_insights, generate_proposal, parse_voice_command

router = APIRouter(prefix="/api/stationery", tags=["Stationery"])

@router.get("/", response_model=List[StationeryItemOut])
def read_stationery_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(StationeryItem).offset(skip).limit(limit).all()
    return items

@router.post("/", response_model=StationeryItemOut)
def create_stationery_item(item: StationeryItemCreate, db: Session = Depends(get_db)):
    db_item = StationeryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}", response_model=StationeryItemOut)
def update_stationery_item(item_id: int, item: StationeryItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(StationeryItem).filter(StationeryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_stationery_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(StationeryItem).filter(StationeryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}

@router.get("/analytics")
async def get_stationery_dashboard(db: Session = Depends(get_db)):
    stats = get_stationery_analytics(db)
    insights = await get_stationery_insights(stats)
    return {"stats": stats, "insights": insights}

@router.post("/proposal")
async def make_proposal(db: Session = Depends(get_db)):
    items = db.query(StationeryItem).filter(StationeryItem.quantity < 10).all()
    item_list = [{"name": i.item_name, "stock": i.quantity, "category": i.category} for i in items]
    proposal = await generate_proposal(item_list)
    return {"proposal": proposal}

@router.post("/voice")
async def process_stationery_voice(command: str):
    return await parse_voice_command(command, "stationery")

