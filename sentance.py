import streamlit as st
from openai import OpenAI

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="오늘의 동기부여",
    page_icon="🔥",
    layout="centered"
)

# -----------------------------
# OpenAI API 설정
# -----------------------------
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        font-size: 17px;
        margin-bottom: 35px;
    }

    .quote-box {
        padding: 30px;
        border-radius: 18px;
        background: #f7f7f7;
        text-align: center;
        margin-top: 25px;
        margin-bottom: 20px;
    }

    .quote {
        font-size: 28px;
        font-weight: 700;
        line-height: 1.5;
    }

    .reason {
        font-size: 17px;
        color: #555;
        line-height: 1.6;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 제목
# -----------------------------
st.markdown(
    '<div class="main-title">🔥 오늘의 동기부여</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">지금 당신에게 필요한 한마디를 AI가 만들어드립니다.</div>',
    unsafe_allow_html=True
)

# -----------------------------
# 사용자 입력
# -----------------------------
situation = st.text_input(
    "현재 어떤 상황인가요?",
    placeholder="예: 시험을 앞두고 공부하기 너무 힘들어요."
)

mood = st.selectbox(
    "어떤 느낌의 말을 원하시나요?",
    [
        "강하게 자극하는 말",
        "따뜻하게 위로하는 말",
        "자신감을 주는 말",
        "포기하지 않게 해주는 말",
        "차분하게 마음을 다잡는 말"
    ]
)

# -----------------------------
# 명언 생성
# -----------------------------
if st.button("✨ 동기부여 받기", use_container_width=True):

    if not situation.strip():
        st.warning("현재 상황을 입력해주세요.")
        st.stop()

    with st.spinner("당신에게 필요한 말을 생각하고 있습니다..."):

        prompt = f"""
당신은 사람에게 현실적인 동기부여를 해주는 AI입니다.

사용자의 상황:
{situation}

사용자가 원하는 분위기:
{mood}

위 상황에 맞는 짧고 강렬한 동기부여 문장을 하나 만들어주세요.

조건:
- 한국어로 작성
- 너무 뻔한 표현은 피할 것
- 실제 유명인의 명언을 그대로 인용하지 말 것
- AI가 직접 만든 문장일 것
- 한두 문장 정도로 짧게 작성
- 사용자의 상황에 직접적으로 도움이 되는 내용일 것

그리고 그 문장이 왜 지금 사용자에게 도움이 되는지
한 문장으로 짧게 설명해주세요.

반드시 아래 형식으로 출력하세요.

명언:
[동기부여 문장]

이유:
[짧은 설명]
"""

        try:
            response = client.responses.create(
                model="gpt-5.4-nano",
                input=prompt
            )

            result = response.output_text

            # 결과 표시
            st.markdown(
                f"""
                <div class="quote-box">
                    <div class="quote">
                        {result}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
