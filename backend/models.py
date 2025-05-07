from pydantic import BaseModel
from datetime import datetime

class Note(BaseModel):
    id: str
    subject: str
    content: str
    created_at: datetime