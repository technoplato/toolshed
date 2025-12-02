from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

class Channel(BaseModel):
    name: str = Field(..., description="Name of the channel")
    id: Optional[str] = Field(None, description="Unique ID of the channel")
    url: Optional[str] = Field(None, description="URL of the channel")

class VideoMetadata(BaseModel):
    id: str = Field(..., description="Unique ID of the video")
    title: str = Field(..., description="Title of the video")
    video_url: str = Field(..., description="Full URL to the video")
    upload_date: Optional[str] = Field(None, description="Upload date in ISO format or YYYYMMDD")
    description: Optional[str] = Field(None, description="Video description")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    view_count: Optional[int] = Field(None, description="Number of views")
    channel: Channel = Field(..., description="Channel information")
