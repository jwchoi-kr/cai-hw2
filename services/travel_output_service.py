from apis.google_places import (
    get_photo_urls,
    get_place_description,
    search_place_id,
)
from domain.enums import Transportation
from domain.models import ChatSessionState


def generate_final_output(state: ChatSessionState) -> str:
    if not state.candidates:
        return "추천할 여행지가 없습니다. 새로운 여행 계획을 입력해 주세요."

    candidate = state.candidates[state.current_index]

    # Google place_id 검색
    place_id = search_place_id(candidate.place_info.place_name)
    if not place_id:
        summary = None
        reviews = []
        photos = []
    else:
        description = get_place_description(place_id) or {}
        summary = description.get("summary")
        reviews = description.get("reviews", [])
        photos = get_photo_urls(place_id, max_photos=3)

    # --- 포맷팅 ---
    name = candidate.place_info.place_name
    reason = candidate.reason or "추천 이유 정보가 없습니다."

    lines = []
    lines.append(f"📍 **{name}**")
    lines.append("")
    lines.append(f"✨ 추천 이유:\n{reason}")

    # Summary
    if summary:
        lines.append("")
        lines.append(f"📝 요약:\n{summary}")

    # Reviews
    if reviews:
        lines.append("")
        lines.append("💬 인기 리뷰:")
        for r in reviews[:2]:  # 최대 2개
            short = r.strip()
            if len(short) > 180:
                short = short[:180] + "..."
            lines.append(f"- {short}")

    # Photos
    if photos:
        lines.append("")
        lines.append("📸 사진:")
        for url in photos:
            lines.append(f"- {url}")

    # 이동시간
    rth = candidate.round_trip_hours
    if rth:
        car = rth.get(Transportation.CAR)
        pub = rth.get(Transportation.PUBLIC)

        lines.append("")
        lines.append("⏱️ 이동 시간(왕복):")

        if car is not None:
            lines.append(f"- 🚗 자동차: 약 {car:.1f}시간")

        if pub is not None:
            lines.append(f"- 🚌 대중교통: 약 {pub:.1f}시간")

    # 다음 후보 이동
    state.current_index += 1

    return "\n".join(lines)
