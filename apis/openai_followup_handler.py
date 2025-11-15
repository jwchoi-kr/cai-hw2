from __future__ import annotations

from typing import List, Optional

from domain.enums import Transportation, WeatherCode
from domain.models import ChatSessionState, DestinationCandidate


def _get_last_presented_candidate(
    state: ChatSessionState,
) -> Optional[DestinationCandidate]:
    if not state.candidates:
        return None

    last_index = state.current_index - 1
    if last_index < 0:
        return None
    if last_index >= len(state.candidates):
        last_index = len(state.candidates) - 1
    return state.candidates[last_index]


def _format_round_trip_hours(candidate: DestinationCandidate) -> str:
    parts: List[str] = []
    rth = candidate.round_trip_hours or {}

    car = rth.get(Transportation.CAR)
    if car is not None:
        parts.append(f"자동차로 왕복 약 {car:.1f}시간")

    pub = rth.get(Transportation.PUBLIC)
    if pub is not None:
        parts.append(f"대중교통으로 왕복 약 {pub:.1f}시간")

    if not parts:
        return "이동 시간 정보는 아직 없어요."

    return ", ".join(parts)


def _weather_label(code: WeatherCode) -> str:
    labels = {
        WeatherCode.CLEAR: "맑음",
        WeatherCode.MAINLY_CLEAR: "대체로 맑음",
        WeatherCode.PARTLY_CLOUDY: "부분적으로 흐림",
        WeatherCode.OVERCAST: "흐림",
        WeatherCode.FOG: "안개",
        WeatherCode.DEPOSITING_RIME_FOG: "서리가 끼는 안개",
        WeatherCode.DRIZZLE_LIGHT: "약한 이슬비",
        WeatherCode.DRIZZLE_MODERATE: "보통 이슬비",
        WeatherCode.DRIZZLE_DENSE: "강한 이슬비",
        WeatherCode.FREEZING_DRIZZLE_LIGHT: "약한 빙설비",
        WeatherCode.FREEZING_DRIZZLE_DENSE: "강한 빙설비",
        WeatherCode.RAIN_LIGHT: "약한 비",
        WeatherCode.RAIN_MODERATE: "보통 비",
        WeatherCode.RAIN_HEAVY: "강한 비",
        WeatherCode.FREEZING_RAIN_LIGHT: "약한 어는 비",
        WeatherCode.FREEZING_RAIN_HEAVY: "강한 어는 비",
        WeatherCode.SNOW_LIGHT: "약한 눈",
        WeatherCode.SNOW_MODERATE: "보통 눈",
        WeatherCode.SNOW_HEAVY: "강한 눈",
        WeatherCode.SNOW_GRAINS: "싸락눈",
        WeatherCode.RAIN_SHOWER_LIGHT: "약한 소나기",
        WeatherCode.RAIN_SHOWER_MODERATE: "보통 소나기",
        WeatherCode.RAIN_SHOWER_HEAVY: "강한 소나기",
        WeatherCode.SNOW_SHOWER_LIGHT: "가벼운 소낙눈",
        WeatherCode.SNOW_SHOWER_HEAVY: "강한 소낙눈",
        WeatherCode.THUNDERSTORM: "뇌우",
        WeatherCode.THUNDERSTORM_HAIL_LIGHT: "약한 우박 동반 뇌우",
        WeatherCode.THUNDERSTORM_HAIL_HEAVY: "강한 우박 동반 뇌우",
    }
    return labels.get(code, "날씨 정보 없음")


def _format_weather(candidate: DestinationCandidate) -> str:
    weather = candidate.daily_weather
    label = _weather_label(weather.weather_code)
    return (
        f"{label} 예상이며 최고 {weather.t_max:.1f}°C / 최저 {weather.t_min:.1f}°C, "
        f"강수량은 약 {weather.precipitation_sum:.1f}mm입니다."
    )


def handle_follow_up(user_input: str, state: ChatSessionState) -> str:
    candidate = _get_last_presented_candidate(state)
    if candidate is None:
        return "아직 소개해 드린 여행지가 없어 추가 설명을 드리기 어렵습니다. 먼저 여행 조건을 알려주세요."

    question = user_input.lower()
    name = candidate.place_info.place_name
    lines = [f"현재 살펴본 곳은 **{name}**입니다."]

    matched = False

    def maybe_add(condition: bool, text: str) -> None:
        nonlocal matched
        if condition:
            lines.append(text)
            matched = True

    maybe_add(
        any(keyword in question for keyword in ["이유", "추천", "특징", "설명"]),
        f"추천 이유: {candidate.reason or '추천 이유 정보가 없습니다.'}",
    )
    maybe_add(
        any(
            keyword in question
            for keyword in ["시간", "거리", "몇시간", "걸리", "이동"]
        ),
        _format_round_trip_hours(candidate),
    )
    maybe_add(
        any(keyword in question for keyword in ["날씨", "비", "기온", "온도"]),
        _format_weather(candidate),
    )
    maybe_add(
        any(keyword in question for keyword in ["주소", "어디", "위치"]),
        f"주소는 {candidate.place_info.road_address_name or '상세 주소 정보가 없습니다.'} 입니다.",
    )
    maybe_add(
        any(keyword in question for keyword in ["점수", "야외", "컨디션"]),
        f"실외 활동 적합도 점수는 {candidate.outdoor_score}점(0~100)입니다.",
    )

    if not matched:
        lines.append(
            "이동 시간, 날씨, 추천 이유 등 궁금한 정보를 말씀해 주시면 바로 알려드릴게요."
        )

    return "\n".join(lines)
