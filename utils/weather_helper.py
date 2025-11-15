from datetime import date

from domain.enums import WeatherCode
from domain.models import DailyWeather


def get_daily_index(target_iso_date: str, daily_times: list[str]) -> int:
    """
    주어진 ISO 날짜 문자열(target_iso_date)이 daily["time"] 리스트에서
    몇 번째 인덱스인지 반환한다.

    예:
        daily["time"] = [
            "2025-11-15",  # 오늘
            "2025-11-16",  # 내일
            "2025-11-17",  # 모레
        ]
        target_iso_date = "2025-11-17" → 반환값 2
    """

    # iso 문자열을 date 객체로 변환
    target_date = date.fromisoformat(target_iso_date)

    # daily_times 배열을 순회하며 찾음
    for idx, iso_str in enumerate(daily_times):
        if date.fromisoformat(iso_str) == target_date:
            return idx

    # 없다면 에러
    raise ValueError(f"해당 날짜({target_iso_date})는 daily 예보 범위에 없음.")


def calculate_outdoor_score(daily_weather: DailyWeather) -> int:
    """
    일일 날씨 정보를 기반으로 실외 활동 적합도 점수(0~100)를 계산한다.

    입력값:
        weather_code (int): Open-Meteo의 WMO 날씨 코드.
        t_max (float): 해당 일자의 최고 기온(°C).
        t_min (float): 해당 일자의 최저 기온(°C).
        precipitation_sum (float): 일 강수량 총합(mm).

    점수 계산 로직:
        • 기본 점수 = 100.

        • 날씨 코드 패널티:
            - 폭우/폭설/뇌우 계열: -80
            - 약/중간 비, 이슬비, 소나기: -40
            - 안개: -20

        • 강수량 패널티:
            - >10mm: -50
            - >5mm: -30
            - >1mm: -15

        • 온도 패널티(체감 기준):
            - t_max ≥ 32°C: -30
            - t_max ≥ 28°C: -20
            - t_max ≤ 0°C: -30
            - t_max ≤ 5°C: -20
            - t_min ≤ -5°C: -20
            - t_min ≤ 0°C: -10

    최종 점수 해석:
        • 80~100 → 실외 활동에 매우 적합
        • 60~79  → 무난하게 가능
        • 40~59  → 다소 애매함
        • 20~39  → 실외 비추천
        • 0~19   → 실외 활동 거의 불가능

    반환값:
        int: 실외 활동 적합도 점수(0~100).
    """

    # 초기 점수 (기본 좋음 가정)
    score = 100

    wc = WeatherCode(daily_weather.weather_code)

    # 1) 날씨 유형 패널티
    if wc in [
        WeatherCode.RAIN_HEAVY,
        WeatherCode.RAIN_SHOWER_HEAVY,
        WeatherCode.SNOW_HEAVY,
        WeatherCode.THUNDERSTORM,
        WeatherCode.THUNDERSTORM_HAIL_LIGHT,
        WeatherCode.THUNDERSTORM_HAIL_HEAVY,
    ]:
        score -= 80

    elif wc in [
        WeatherCode.RAIN_LIGHT,
        WeatherCode.RAIN_MODERATE,
        WeatherCode.RAIN_SHOWER_LIGHT,
        WeatherCode.RAIN_SHOWER_MODERATE,
        WeatherCode.DRIZZLE_LIGHT,
        WeatherCode.DRIZZLE_MODERATE,
    ]:
        score -= 40

    elif wc in [
        WeatherCode.FOG,
        WeatherCode.DEPOSITING_RIME_FOG,
    ]:
        score -= 20

    # 2) 강수량 패널티
    if daily_weather.precipitation_sum > 10:
        score -= 50
    elif daily_weather.precipitation_sum > 5:
        score -= 30
    elif daily_weather.precipitation_sum > 1:
        score -= 15

    # 3) 온도 패널티
    if daily_weather.t_max >= 32:
        score -= 30
    elif daily_weather.t_max >= 28:
        score -= 20
    elif daily_weather.t_max <= 0:
        score -= 30
    elif daily_weather.t_max <= 5:
        score -= 20

    if daily_weather.t_min <= -5:
        score -= 20
    elif daily_weather.t_min <= 0:
        score -= 10

    # 점수 보정
    score = max(0, min(score, 100))
    return score
