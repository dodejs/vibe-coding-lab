import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="IT 자산 위험 스코어링 대시보드", layout="wide")

# -----------------------------
# 기본 데이터
# -----------------------------
risk_scores = {
    "보안장비": 10,
    "네트워크 장비": 8,
    "서버장비": 7,
    "오피스 PC": 5
}

color_map = {
    "보안장비": "#e74c3c",
    "네트워크 장비": "#f39c12",
    "서버장비": "#3498db",
    "오피스 PC": "#2ecc71"
}

icon_map = {
    "보안장비": "🛡️",
    "네트워크 장비": "🌐",
    "서버장비": "🖥️",
    "오피스 PC": "💻"
}

# -----------------------------
# 상태 관리
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = None

# -----------------------------
# 공통 스타일
# -----------------------------
st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 30px;
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: #666666;
        margin-bottom: 40px;
    }
    .card-label {
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .card-icon {
        text-align: center;
        font-size: 48px;
        margin-top: 10px;
    }
    div.stButton > button {
        width: 100%;
        height: 160px;
        border-radius: 18px;
        font-size: 22px;
        font-weight: 700;
        border: 1px solid #d9d9d9;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        background-color: white;
    }
    div.stButton > button:hover {
        border: 2px solid #1f77b4;
        color: #1f77b4;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# 페이지 함수
# -----------------------------
def show_dashboard():
    st.markdown('<div class="main-title">IT 자산 위험 스코어링 대시보드</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">자산 분류를 선택하면 위험도 스코어링 화면으로 이동합니다.</div>', unsafe_allow_html=True)

    left_space, col1, col2, col3, col4, right_space = st.columns([0.5, 1, 1, 1, 1, 0.5])

    with col1:
        if st.button(f"{icon_map['보안장비']}\n\n보안장비", key="security_btn"):
            st.session_state.selected_asset = "보안장비"
            st.session_state.page = "scoring"
            st.rerun()

    with col2:
        if st.button(f"{icon_map['네트워크 장비']}\n\n네트워크 장비", key="network_btn"):
            st.session_state.selected_asset = "네트워크 장비"
            st.session_state.page = "scoring"
            st.rerun()

    with col3:
        if st.button(f"{icon_map['서버장비']}\n\n서버장비", key="server_btn"):
            st.session_state.selected_asset = "서버장비"
            st.session_state.page = "scoring"
            st.rerun()

    with col4:
        if st.button(f"{icon_map['오피스 PC']}\n\n오피스 PC", key="office_btn"):
            st.session_state.selected_asset = "오피스 PC"
            st.session_state.page = "scoring"
            st.rerun()


def show_scoring():
    selected_asset = st.session_state.selected_asset

    st.title("IT 자산 위험 스코어링 앱")

    if st.button("← 대시보드로 돌아가기"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("---")

    asset_list = list(risk_scores.keys())
    default_index = asset_list.index(selected_asset) if selected_asset in asset_list else 0

    selected_asset = st.selectbox(
        "자산/솔루션 군을 선택하세요",
        asset_list,
        index=default_index
    )

    score = risk_scores[selected_asset]

    st.subheader("선택 결과")
    st.write(f"선택한 자산/솔루션 군: **{selected_asset}**")
    st.write(f"위험도 점수: **{score}점**")

    df = pd.DataFrame({
        "자산/솔루션 군": list(risk_scores.keys()),
        "위험도 점수": list(risk_scores.values())
    })

    colors = [color_map[asset] for asset in df["자산/솔루션 군"]]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(df["자산/솔루션 군"], df["위험도 점수"], color=colors)

    for bar, asset in zip(bars, df["자산/솔루션 군"]):
        if asset == selected_asset:
            bar.set_edgecolor("black")
            bar.set_linewidth(3)

    ax.set_title("자산별 위험도 비교")
    ax.set_ylabel("위험도 점수")
    ax.set_ylim(0, 12)

    st.pyplot(fig)

# -----------------------------
# 라우팅
# -----------------------------
if st.session_state.page == "dashboard":
    show_dashboard()
else:
    show_scoring()
