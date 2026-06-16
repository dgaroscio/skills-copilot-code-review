"""
Announcements API router for managing school announcements
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from ..database import announcements_collection

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("")
def get_announcements(active_only: bool = Query(True)) -> List[Dict[str, Any]]:
    """Get all announcements or only active ones"""
    query = {}
    
    if active_only:
        now = datetime.now()
        query = {
            "$or": [
                {"expiration_date": {"$gt": now.isoformat()}},
                {"expiration_date": None}
            ]
        }
    
    announcements = list(announcements_collection.find(query).sort("_id", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["id"] = str(announcement.pop("_id"))
    
    return announcements


@router.post("")
def create_announcement(
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    announcement_type: str = Query("info")
) -> Dict[str, Any]:
    """Create a new announcement (admin only)"""
    
    # Validate dates
    try:
        if start_date:
            datetime.fromisoformat(start_date)
        datetime.fromisoformat(expiration_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
        )
    
    new_announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "type": announcement_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(new_announcement)
    new_announcement["id"] = str(result.inserted_id)
    
    return new_announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    title: Optional[str] = None,
    message: Optional[str] = None,
    expiration_date: Optional[str] = None,
    start_date: Optional[str] = None,
    announcement_type: Optional[str] = None
) -> Dict[str, Any]:
    """Update an announcement (admin only)"""
    
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    # Build update dict with only provided fields
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if message is not None:
        update_data["message"] = message
    if start_date is not None:
        update_data["start_date"] = start_date
    if expiration_date is not None:
        # Validate date
        try:
            datetime.fromisoformat(expiration_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid expiration_date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
            )
        update_data["expiration_date"] = expiration_date
    if announcement_type is not None:
        update_data["type"] = announcement_type
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    result = announcements_collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    result["id"] = str(result.pop("_id"))
    return result


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str) -> Dict[str, str]:
    """Delete an announcement (admin only)"""
    
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
