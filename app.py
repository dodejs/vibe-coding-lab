import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("IT 자산 위험도 스코어링 앱")
st.write("자산/솔루션 군을 선택하면 위험도 점수와 색상이 다른 그래프를 보여줍니다.")

# 자산별 위험도 점수
risk_scores = {
    "보안 솔루션": 10,
    "네트워크 장비": 8,
    "WEB 서버": 7,
    "WAS 서버": 7,
    "DB 서버": 10
}

# 자산 선택
selected_asset = st.selectbox(
    "자산/솔루션 군을 선택하세요",
    list(risk_scores.keys())
)

score = risk_scores[selected_asset]

# 선택 결과 표시
st.subheader("선택 결과")
st.write(f"선택한 자산/솔루션 군: **{selected_asset}**")
st.write(f"위험도 점수: **{score}점**")

# 데이터프레임 생성
df = pd.DataFrame({
    "자산/솔루션 군": list(risk_scores.keys()),
    "위험도 점수": list(risk_scores.values())
})

# 색상 지정
color_map = {
    "보안 솔루션": "red",
    "네트워크 장비": "orange",
    "WEB 서버": "blue",
    "WAS 서버": "green",
    "DB 서버": "purple"
}

colors = [color_map[asset] for asset in df["자산/솔루션 군"]]

# 그래프 그리기
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(df["자산/솔루션 군"], df["위험도 점수"], color=colors)

# 선택한 항목 강조
for bar, asset in zip(bars, df["자산/솔루션 군"]):
    if asset == selected_asset:
        bar.set_edgecolor("black")
        bar.set_linewidth(3)

ax.set_title("자산별 위험도 비교")
ax.set_ylabel("위험도 점수")
ax.set_ylim(0, 12)
plt.xticks(rotation=20)

st.subheader("위험도 시각화")
st.pyplot(fig)
