from dataclasses import dataclass 
from datetime import datetime 

@dataclass
class NoteSection: 
    subject: str 
    content: str 
    created_at: datetime = datetime.now()