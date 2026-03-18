import streamlit as st
import pandas as pd

st.title("IT 자산 위험도 스코어링 앱")

st.write("자산/솔루션 군을 선택하면 위험도 점수와 그래프를 보여줍니다.")

risk_scores = {
    "보안 솔루션": 10,
    "네트워크 장비": 8,
    "WEB 서버": 7,
    "WAS 서버": 7,
    "DB 서버": 10
}

selected_asset = st.selectbox(
    "자산/솔루션 군을 선택하세요",
    list(risk_scores.keys())
)

score = risk_scores[selected_asset]

st.subheader("선택 결과")
st.write(f"선택한 자산/솔루션 군: **{selected_asset}**")
st.write(f"위험도 점수: **{score}점**")

st.subheader("위험도 시각화")

chart_data = pd.DataFrame({
    "자산/솔루션 군": list(risk_scores.keys()),
    "위험도 점수": list(risk_scores.values())
}).set_index("자산/솔루션 군")

st.bar_chart(chart_data)

st.subheader("선택 항목 강조")
selected_data = pd.DataFrame({
    "항목": [selected_asset],
    "위험도 점수": [score]
}).set_index("항목")

st.bar_chart(selected_data)
