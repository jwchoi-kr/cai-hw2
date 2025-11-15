from enum import Enum, IntEnum


class ChatIntent(str, Enum):
    """
    유저의 챗 의도 Enum
    - TRIP_INFO: 새로운 여행지 추천 요청
    - NEXT_CANDIDATE: 다음 여행지 추천 요청
    - FOLLOW_UP: 추가 질문/요청
    - UNKNOWN: 의도를 파악할 수 없음
    """

    TRIP_INFO = "TRIP_INFO"
    NEXT_CANDIDATE = "NEXT_CANDIDATE"
    FOLLOW_UP = "FOLLOW_UP"
    UNKNOWN = "UNKNOWN"


class PlaceCategory(Enum):
    """
    장소 카테고리 Enum
    카카오 로컬 API 기준 카테고리 코드 사용
    """

    TOURIST_SPOT = "AT4"  # 관광명소
    CULTURE_FACILITY = "CT1"  # 문화시설
    # RESTAURANT = "FD6"  # 음식점
    # CAFE = "CE7"  # 카페


class Transportation(Enum):
    CAR = "CAR"
    PUBLIC = "PUBLIC"


class WeatherCode(IntEnum):
    # 0~3: 맑음~흐림
    CLEAR = 0  # 맑음
    MAINLY_CLEAR = 1  # 대체로 맑음
    PARTLY_CLOUDY = 2  # 부분 흐림
    OVERCAST = 3  # 흐림 (매우 흐림)

    # 45~48: 안개
    FOG = 45  # 안개
    DEPOSITING_RIME_FOG = 48  # 서리 안개

    # 51~57: 이슬비
    DRIZZLE_LIGHT = 51  # 약한 이슬비
    DRIZZLE_MODERATE = 53  # 보통 이슬비
    DRIZZLE_DENSE = 55  # 강한 이슬비
    FREEZING_DRIZZLE_LIGHT = 56
    FREEZING_DRIZZLE_DENSE = 57

    # 61~67: 비
    RAIN_LIGHT = 61  # 약한 비
    RAIN_MODERATE = 63  # 보통 비
    RAIN_HEAVY = 65  # 강한 비
    FREEZING_RAIN_LIGHT = 66
    FREEZING_RAIN_HEAVY = 67

    # 71~77: 눈
    SNOW_LIGHT = 71
    SNOW_MODERATE = 73
    SNOW_HEAVY = 75
    SNOW_GRAINS = 77

    # 80~86: 소나기/눈
    RAIN_SHOWER_LIGHT = 80
    RAIN_SHOWER_MODERATE = 81
    RAIN_SHOWER_HEAVY = 82
    SNOW_SHOWER_LIGHT = 85
    SNOW_SHOWER_HEAVY = 86

    # 95~99: 뇌우
    THUNDERSTORM = 95
    THUNDERSTORM_HAIL_LIGHT = 96
    THUNDERSTORM_HAIL_HEAVY = 99
