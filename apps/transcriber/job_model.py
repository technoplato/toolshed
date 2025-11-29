from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from instantdb_admin_client import Update

class JobType(str, Enum):
    VIDEO_DOWNLOAD = "video_download"
    TRANSCRIPTION_PROCESSING = "transcription_processing"

class Video(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    platform: str
    original_url: str
    title: str
    duration: Optional[float] = None
    channel: Optional[str] = None
    upload_date: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def to_instant_update(self) -> Update:
        """Converts the Pydantic model to an InstantDB Update step."""
        data = self.model_dump(mode='json')
        video_id = str(data.pop('id'))
        
        return Update(
            collection="videos",
            id=video_id,
            data=data
        )

class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: JobType
    progress: str
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def to_instant_update(self) -> Update:
        """Converts the Pydantic model to an InstantDB Update step."""
        # model_dump(mode='json') handles UUIDs and datetimes correctly for JSON serialization
        data = self.model_dump(mode='json')
        
        # We don't need to send the ID in the data payload if it's the key, 
        # but InstantDB often likes it there too. 
        # The Update class requires 'id' as a separate argument.
        job_id = str(data.pop('id'))
        
        return Update(
            collection="jobs",
            id=job_id,
            data=data
        )
