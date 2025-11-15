from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pydantic import BaseModel

from domain.enums import ChatIntent, PlaceCategory, Transportation, WeatherCode


@dataclass
class PlaceInfo:  # 장소 정보 (카카오맵 api 응답과 매핑)
    id: str
    place_name: str
    road_address_name: str
    dest_lat: float
    dest_lon: float


@dataclass
class DailyWeather:
    weather_code: WeatherCode  # 날씨 상태 코드
    t_max: float  # 최고 기온 (°C)
    t_min: float  # 최저 기온 (°C)
    precipitation_sum: float  # 일 강수량 총합 (mm)


@dataclass
class DestinationCandidate:
    place_info: PlaceInfo  # 장소 정보
    round_trip_hours: Dict[Transportation, float | None]  # 왕복 이동 시간
    daily_weather: DailyWeather  # 일일 날씨 정보
    outdoor_score: int  # 실외 활동 적합도 점수 (0~100)
    reason: Optional[str] = None  # 추천 이유


@dataclass
class FinalOutput:
    candidates: DestinationCandidate  # 최종 추천 여행지
    summary: str  # 장소 요약
    reviews: List[str]  # 장소 리뷰
    photo_urls: List[str]  # 장소 사진 URL 목록


class ParsedUserIntent(BaseModel):  # openai를 이용한 사용자 의도 파악 결과
    intent: ChatIntent


class ParsedUserInfo(BaseModel):  # openai를 이용한 사용자 입력 파싱 결과
    # 기본 정보
    origin: str  # 출발지
    departure_datetime: str  # 출발 날짜, 시각 (ISO 8601 형식)
    max_travel_hours: float  # 최대 여행 시간(왕복, 시간 단위)
    destination_categories: List[
        PlaceCategory
    ]  # 희망 장소 카테고리 (관광명소, 문화시설)
    transportation: Transportation | None  # 교통수단

    # 선호/제약
    likes: Optional[List[str]] = None  # 가중치 ↑ (예: "자연", "호수", "카페")
    dislikes: Optional[List[str]] = None  # 가중치 ↓ (예: "쇼핑몰", "복잡함")
    must_include: Optional[List[str]] = None  # 반드시 포함(태그/카테고리/속성)
    must_avoid: Optional[List[str]] = None  # 반드시 제외

    # 키워드 ("미술관", "전시회", "호수" 같은 명시적 키워드)
    keyword: Optional[str] = None


class FilteredPlaces(BaseModel):  # openai를 이용한 장소 필터링 결과
    places: List[str]


class LLMRecommendedCandidate(BaseModel):
    place_name: str
    reason: str


class LLMRecommendedCandidates(BaseModel):
    candidates: List[LLMRecommendedCandidate]


@dataclass
class ChatSessionState:
    parsed_user_info: Optional[ParsedUserInfo] = None
    candidates: List[DestinationCandidate] = field(default_factory=list)
    current_index: int = 0
