# models/data_location_model.py
from pydantic import BaseModel
from typing import List, Optional

class LocationEntry(BaseModel):
    system: str
    database: Optional[str] = None
    collection: Optional[str] = None
    bucket: Optional[str] = None
    table: Optional[str] = None
    field: Optional[str] = None
    value: Optional[str] = None
    file_path: Optional[str] = None

class DataLocation(BaseModel):
    user_id: str
    locations: List[LocationEntry]
    last_updated: str