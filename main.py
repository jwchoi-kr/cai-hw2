from apis.openai_followup_handler import handle_follow_up
from apis.openai_intent_parser import parse_user_intent
from apis.openai_unknown_handler import handle_unknown_input
from domain.enums import ChatIntent
from domain.models import ChatSessionState
from services.travel_input_service import (
    generate_travel_candidates,
)
from services.travel_output_service import generate_final_output


def run_chatbot():
    state = ChatSessionState()

    print(
        "Bot: 안녕하세요! 저는 여행 추천 챗봇입니다. 출발지, 여행 시간, 교통수단, 취향 등을 알려주시면 맞춤 여행지를 추천해드릴게요.\n"
    )

    while True:
        user_input = input("User: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "종료"):
            break

        has_already_recommended = len(state.candidates) > 0

        # Intent 추출
        intent = parse_user_intent(
            user_input,
            has_already_recommended,
        )

        # Intent 라우팅
        if intent == ChatIntent.TRIP_INFO:
            generate_travel_candidates(user_input, 5, state)
            response = generate_final_output(state)

        elif intent == ChatIntent.NEXT_CANDIDATE:
            response = generate_final_output(state)

        elif intent == ChatIntent.FOLLOW_UP:
            response = handle_follow_up(user_input, state)

        else:
            response = handle_unknown_input(user_input, has_already_recommended)

        print(f"Bot: {response}\n")


if __name__ == "__main__":
    run_chatbot()
