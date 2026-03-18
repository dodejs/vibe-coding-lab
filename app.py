import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("IT 자산 위험도 스코어링 앱")

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

# ===== 색상 지정 =====
colors = ["red", "orange", "blue", "green", "purple"]

# ===== 데이터 =====
assets = list(risk_scores.keys())
scores = list(risk_scores.values())

# ===== 그래프 생성 =====
fig, ax = plt.subplots()

ax.bar(assets, scores, color=colors)

ax.set_ylabel("위험도 점수")
ax.set_title("자산별 위험도 비교")

# 선택 항목 강조 (테두리)
for i, asset in enumerate(assets):
    if asset == selected_asset:
        ax.bar(assets[i], scores[i], color=colors[i], edgecolor='black', linewidth=3)

plt.xticks(rotation=30)

st.pyplot(fig)
