from enum import Enum


class PlaceCategory(Enum):
    """
    장소 카테고리 Enum
    카카오 로컬 API 기준 카테고리 코드 사용
    """

    TOURIST_SPOT = "AT4"  # 관광명소
    CULTURE_FACILITY = "CT1"  # 문화시설
    # RESTAURANT = "FD6"  # 음식점
    # CAFE = "CE7"  # 카페


class WeatherCondition(Enum):
    CLEAR = "clear"  # 맑음
    PARTLY_CLOUDY = "partly_cloudy"  # 구름 조금
    CLOUDY = "cloudy"  # 흐림
    OVERCAST = "overcast"  # 매우 흐림

    RAIN = "rain"  # 비
    HEAVY_RAIN = "heavy_rain"  # 강한 비
    DRIZZLE = "drizzle"  # 이슬비

    SNOW = "snow"  # 눈
    RAIN_SNOW = "rain_snow"  # 비/눈 섞임
    SLEET = "sleet"  # 진눈깨비

    THUNDER = "thunder"  # 뇌우
    FOG = "fog"  # 안개


class AirQualityGrade(Enum):
    GOOD = 1  # 좋음
    NORMAL = 2  # 보통
    BAD = 3  # 나쁨
    VERY_BAD = 4  # 매우 나쁨
