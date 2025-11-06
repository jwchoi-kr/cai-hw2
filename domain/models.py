from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


@dataclass
class ParsedTravelIntent(BaseModel):
    origin: str
    travel_duration_hours: int
    transportation: Optional[str] = None
    preferences: list[str] = None


@dataclass
class PlaceInfo:  # 장소 정보 (카카오맵 api 응답과 매핑)
    place_name: str
    address_name: str
    road_address_name: str
    phone: str
    distance: float


@dataclass
class DestinationCandidate:
    place_info: PlaceInfo  # 장소 정보
    round_trip_duration_hours: Optional[float] = None  # 왕복 소요 시간
    weather: Optional[str] = None  # 날씨
    reasons: list[str] = None  # 추천 이유
