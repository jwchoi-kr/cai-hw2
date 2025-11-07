from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from domain.enums import AirQualityGrade, WeatherCondition


class ParsedTravelIntent(BaseModel):
    # 기본 정보
    origin: str  # 출발지
    departure_time: str  # 출발 시각
    max_travel_hours: float  # 최대 여행 시간(왕복, 시간 단위)
    budget: Optional[int] = None  # 예산(원)
    transportation: Optional[str] = None  # 교통수단
    companions: Optional[List[str]] = None  # 동행자 유형

    # 선호/제약
    likes: Optional[List[str]] = None  # 가중치 ↑ (예: "자연", "호수", "카페")
    dislikes: Optional[List[str]] = None  # 가중치 ↓ (예: "쇼핑몰", "복잡함")
    must_include: Optional[List[str]] = None  # 반드시 포함(태그/카테고리/속성)
    must_avoid: Optional[List[str]] = None  # 반드시 제외


@dataclass
class PlaceInfo:  # 장소 정보 (카카오맵 api 응답과 매핑)
    place_name: str
    address_name: str
    road_address_name: str
    phone: str
    distance_m: float


@dataclass
class WeatherSnapshot:
    timestamp: datetime  # 측정 시각
    weather_condition: WeatherCondition  # 날씨 상태 (enum)
    temperature: float  # 섭씨 온도
    humidity_percent: float  # 습도 (%)
    wind_speed_m_s: float  # 풍속 (m/s)
    air_quality: AirQualityGrade  # 대기질 등급 (enum)


@dataclass
class WeatherInfo:
    current: WeatherSnapshot  # 현재 날씨
    hourly_forecast: List[WeatherSnapshot] = field(  # 시간별 날씨 예보
        default_factory=list
    )


@dataclass
class DestinationCandidate:
    place_info: PlaceInfo  # 장소 정보
    weather: WeatherInfo  # 날씨 정보
    round_trip_hours: float  # 왕복 이동 시간 (시간 단위, 추후에 카카오 api로 계산 예정)
    reasons: List[str] = field(default_factory=list)  # 추천 이유
