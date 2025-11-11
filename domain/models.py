from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from domain.enums import AirQualityGrade, PlaceCategory, WeatherCondition


class ParsedUserInput(BaseModel):
    # 기본 정보
    origin: str  # 출발지
    departure_time: str  # 출발 시각
    max_travel_hours: float  # 최대 여행 시간(왕복, 시간 단위)
    destination_categories: List[
        PlaceCategory
    ]  # 희망 장소 카테고리 (관광명소, 문화시설)
    budget: Optional[int] = None  # 예산(원)
    transportation: Optional[str] = None  # 교통수단
    companions: Optional[List[str]] = None  # 동행자 유형

    # 선호/제약
    likes: Optional[List[str]] = None  # 가중치 ↑ (예: "자연", "호수", "카페")
    dislikes: Optional[List[str]] = None  # 가중치 ↓ (예: "쇼핑몰", "복잡함")
    must_include: Optional[List[str]] = None  # 반드시 포함(태그/카테고리/속성)
    must_avoid: Optional[List[str]] = None  # 반드시 제외

    # 키워드 ("미술관", "전시회", "호수" 같은 명시적 키워드)
    keyword: Optional[str] = None


class FilteredPlaces(BaseModel):
    places: List[str]


@dataclass
class FinalCandidate:
    place: str
    reason: str


class FinalCandidates(BaseModel):
    candidates: List[FinalCandidate]


@dataclass
class PlaceInfo:  # 장소 정보 (카카오맵 api 응답과 매핑)
    place_name: str
    road_address_name: str
    dest_lat: float
    dest_lon: float


@dataclass
class WeatherSnapshot:
    dt: datetime  # 예보 시각
    TMP: Optional[float]  # 기온 (°C)
    SKY: Optional[int]  # 하늘상태 코드 (1,3,4)
    PTY: Optional[int]  # 강수형태 코드 (0~4)
    POP: Optional[int]  # 강수확률 (%)


@dataclass
class RawWeather:
    nx: int  # 격자 X 좌표
    ny: int  # 격자 Y 좌표
    snapshots: List[WeatherSnapshot]  # 시간별 날씨 스냅샷 리스트


@dataclass
class WeatherSummary:
    weather_condition: WeatherCondition  # 날씨 상태 (enum)
    temperature: float  # 섭씨 온도
    # air_quality: AirQualityGrade  # 대기질 등급 (enum)


@dataclass
class DestinationCandidate:
    place_info: PlaceInfo  # 장소 정보
    round_trip_hours: float  # 왕복 이동 시간 (시간 단위, 추후에 카카오 api로 계산 예정)
    # weather: WeatherSummary  # 날씨 정보
    # reasons: List[str] = field(default_factory=list)  # 추천 이유
