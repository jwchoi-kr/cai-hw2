import os

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import ParsedTravelIntent

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
)


def parse_travel_intent(user_input: str) -> ParsedTravelIntent:
    print("Parsing travel intent for input:", user_input)
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": f"다음 사용자의 입력을 분석하여 여행 의도를 추출하세요: {user_input}",
            },
        ],
        text_format=ParsedTravelIntent,
    )

    return response.output_parsed
