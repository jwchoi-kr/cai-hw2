from domain.enums import WeatherCode
from domain.models import DailyWeather
from utils.http import safe_get
from utils.weather_helper import get_daily_index


def get_weather_new(
    lat: float, lon: float, departure_datetime_iso: str
) -> DailyWeather | None:
    """
    open-meteo.com의 API를 사용하여 특정 날짜(departure_datetime_iso)의
    하루 단위 요약 날씨를 가져온다.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Asia/Seoul",
        "daily": (
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ),
    }

    # 응답 JSON 전체
    res = safe_get(url, params=params)
    daily = res["daily"]

    # ISO 날짜에서 날짜 부분만 추출
    date_only = departure_datetime_iso.split("T", 1)[0]

    # ISO 날짜 기반으로 해당 인덱스 찾기
    try:
        daily_index = get_daily_index(date_only, daily["time"])
    except Exception as e:
        print("날짜 매칭 오류:", e)
        return None

    # 하루 요약 날씨만 추출
    daily_weather = DailyWeather(
        weather_code=WeatherCode(daily["weathercode"][daily_index]),
        t_max=daily["temperature_2m_max"][daily_index],
        t_min=daily["temperature_2m_min"][daily_index],
        precipitation_sum=daily["precipitation_sum"][daily_index],
    )

    return daily_weather
