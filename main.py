from services.travel_intent_service import generate_travel_candidates


def main():
    # user_input = input("여행 계획을 입력하세요: ")
    user_input = (
        "서울 강남역에서 이번 주 토요일 오전 9시에 출발해서 여자친구랑 하루 나들이 가고 싶어. "
        "왕복으로 6시간 정도 걸리는 거리면 좋겠고, 예산은 8만 원이야. "
        "차로 이동할 거고, 사람 많은 도심이나 쇼핑몰은 피하고 싶어. "
        "자연 풍경이 예쁘고 조용한 곳이나, 미술관이나 전시회처럼 문화적인 장소도 괜찮아."
    )

    try:
        final_candidates = generate_travel_candidates(
            user_input, k=5
        )  # List[FinalCandidate] 반환

        print("=== 추천된 상위 여행지 ===")
        for idx, fc in enumerate(final_candidates, start=1):
            print(f"{idx}. {fc.place}")
            print(f"   이유: {fc.reason}\n")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
