import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="IT 자산 위험 스코어링 대시보드",
    layout="wide"
)

# -----------------------------
# 데이터
# -----------------------------
risk_scores = {
    "보안장비": 10,
    "네트워크 장비": 8,
    "서버장비": 7,
    "오피스 PC": 5
}

color_map = {
    "보안장비": "#E74C3C",
    "네트워크 장비": "#F39C12",
    "서버장비": "#3498DB",
    "오피스 PC": "#2ECC71"
}

icon_map = {
    "보안장비": "🛡️",
    "네트워크 장비": "🌐",
    "서버장비": "🖥️",
    "오피스 PC": "💻"
}

description_map = {
    "보안장비": "보안 통제 및 방어 체계",
    "네트워크 장비": "네트워크 연결 및 통신 인프라",
    "서버장비": "서비스 운영을 위한 핵심 서버 자산",
    "오피스 PC": "사용자 업무용 단말 환경"
}

# -----------------------------
# 상태값
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = None

# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
    <style>
        .main-title {
            text-align: center;
            font-size: 38px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 8px;
            color: #1F2937;
        }

        .sub-title {
            text-align: center;
            font-size: 17px;
            color: #6B7280;
            margin-bottom: 30px;
        }

        .summary-box {
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 18px 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 16px;
        }

        .summary-label {
            font-size: 14px;
            color: #6B7280;
            margin-bottom: 6px;
        }

        .summary-value {
            font-size: 28px;
            font-weight: 800;
            color: #111827;
        }

        .section-title {
            font-size: 22px;
            font-weight: 700;
            margin-top: 10px;
            margin-bottom: 14px;
            color: #111827;
        }

        div.stButton > button {
            width: 100%;
            height: 180px;
            border-radius: 20px;
            border: 1px solid #E5E7EB;
            background: white;
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
            font-size: 22px;
            font-weight: 700;
            color: #111827;
            white-space: pre-line;
        }

        div.stButton > button:hover {
            border: 2px solid #2563EB;
            color: #2563EB;
            transform: translateY(-2px);
            transition: 0.2s ease-in-out;
        }

        .info-card {
            border-radius: 16px;
            padding: 18px 20px;
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 14px;
        }

        .score-badge {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 700;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# 유틸
# -----------------------------
def get_risk_level(score):
    if score >= 9:
        return "High"
    elif score >= 7:
        return "Medium"
    else:
        return "Low"


def render_summary():
    total_assets = len(risk_scores)
    avg_score = round(sum(risk_scores.values()) / total_assets, 1)
    max_asset = max(risk_scores, key=risk_scores.get)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="summary-box">
                <div class="summary-label">총 자산 분류 수</div>
                <div class="summary-value">{total_assets}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="summary-box">
                <div class="summary-label">평균 위험 점수</div>
                <div class="summary-value">{avg_score}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="summary-box">
                <div class="summary-label">최고 위험 자산</div>
                <div class="summary-value" style="font-size:20px;">{max_asset}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# -----------------------------
# 페이지 1: 대시보드
# -----------------------------
def show_dashboard():
    st.markdown('<div class="main-title">IT 자산 위험 스코어링 대시보드</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">자산 분류 카드를 선택하면 위험도 분석 화면으로 이동합니다.</div>',
        unsafe_allow_html=True
    )

    render_summary()

    st.markdown('<div class="section-title">자산 분류 선택</div>', unsafe_allow_html=True)

    left_space, col1, col2, col3, col4, right_space = st.columns([0.3, 1, 1, 1, 1, 0.3])

    assets = list(risk_scores.keys())

    columns = [col1, col2, col3, col4]

    for col, asset in zip(columns, assets):
        with col:
            button_text = (
                f"{icon_map[asset]}\n\n"
                f"{asset}\n"
                f"위험 점수: {risk_scores[asset]}점"
            )
            if st.button(button_text, key=f"{asset}_button"):
                st.session_state.selected_asset = asset
                st.session_state.page = "scoring"
                st.rerun()

    st.markdown("")
    st.markdown('<div class="section-title">자산 분류 설명</div>', unsafe_allow_html=True)

    info_cols = st.columns(4)
    for col, asset in zip(info_cols, assets):
        with col:
            st.markdown(
                f"""
                <div class="info-card">
                    <div style="font-size:34px; margin-bottom:8px;">{icon_map[asset]}</div>
                    <div style="font-size:20px; font-weight:700; margin-bottom:8px;">{asset}</div>
                    <div style="font-size:14px; color:#6B7280; margin-bottom:10px;">
                        {description_map[asset]}
                    </div>
                    <div class="score-badge" style="background:{color_map[asset]};">
                        위험 점수 {risk_scores[asset]}점
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# -----------------------------
# 페이지 2: 스코어링
# -----------------------------
def show_scoring():
    selected_asset = st.session_state.selected_asset
    asset_list = list(risk_scores.keys())

    if selected_asset not in asset_list:
        selected_asset = asset_list[0]

    st.markdown('<div class="main-title">IT 자산 위험도 분석</div>', unsafe_allow_html=True)

    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("← 대시보드"):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("---")

    default_index = asset_list.index(selected_asset)

    selected_asset = st.selectbox(
        "자산/솔루션 군을 선택하세요",
        asset_list,
        index=default_index
    )

    score = risk_scores[selected_asset]
    risk_level = get_risk_level(score)
    selected_color = color_map[selected_asset]

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.markdown(
            f"""
            <div class="info-card">
                <div style="font-size:42px; margin-bottom:10px;">{icon_map[selected_asset]}</div>
                <div style="font-size:26px; font-weight:800; margin-bottom:10px;">{selected_asset}</div>
                <div style="font-size:15px; color:#6B7280; margin-bottom:12px;">
                    {description_map[selected_asset]}
                </div>
                <div style="font-size:18px; margin-bottom:8px;"><b>위험도 점수:</b> {score}점</div>
                <div style="font-size:18px; margin-bottom:8px;"><b>위험 수준:</b> {risk_level}</div>
                <div class="score-badge" style="background:{selected_color}; margin-top:6px;">
                    {selected_asset} 위험도
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        df = pd.DataFrame({
            "자산/솔루션 군": asset_list,
            "위험도 점수": [risk_scores[a] for a in asset_list]
        })

        colors = [color_map[a] for a in asset_list]

        fig, ax = plt.subplots(figsize=(9, 4.8))
        bars = ax.bar(df["자산/솔루션 군"], df["위험도 점수"], color=colors)

        for bar, asset in zip(bars, df["자산/솔루션 군"]):
            if asset == selected_asset:
                bar.set_edgecolor("black")
                bar.set_linewidth(3)

        ax.set_title("자산별 위험도 비교", fontsize=14, fontweight="bold")
        ax.set_ylabel("위험도 점수")
        ax.set_ylim(0, 12)
        plt.xticks(rotation=15)
        plt.tight_layout()

        st.pyplot(fig)

    st.markdown('<div class="section-title">점수 기준</div>', unsafe_allow_html=True)

    guide_df = pd.DataFrame({
        "점수 구간": ["9~10", "7~8", "0~6"],
        "위험 수준": ["High", "Medium", "Low"],
        "설명": [
            "핵심 통제 및 중요 자산으로 우선 관리 필요",
            "중간 수준의 운영 리스크 존재",
            "상대적으로 낮은 수준의 위험"
        ]
    })

    st.dataframe(guide_df, use_container_width=True, hide_index=True)


# -----------------------------
# 라우팅
# -----------------------------
if st.session_state.page == "dashboard":
    show_dashboard()
else:
    show_scoring()
