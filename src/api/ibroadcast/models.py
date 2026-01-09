from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseModel:
    id: int = 0
    name: str = ""

@dataclass
class Artist(BaseModel):
    rating: int = 0
    artwork_id: int = 0

@dataclass
class Album(BaseModel):
    rating: int = 0
    disc: int = 0
    year: int = 0

@dataclass
class Track(BaseModel):
    track_number: int = 0
    year: int = 0
    length: int = 0
    artwork_id: int = 0
    rating: int = 0
    plays: int = 0
    file: str = ""

@dataclass
class Playlist(BaseModel):
    description: Optional[str] = None
    artwork_id: int = 0