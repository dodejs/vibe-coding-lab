import streamlit as st
import pandas as pd
from datetime import date
import requests

st.set_page_config(
    page_title="임상욱 일일 스케쥴러",
    layout="wide"
)

reward_amount = 5000

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

time_options = list(range(4, 25))


def format_hour(hour: int) -> str:
    return "24:00" if hour == 24 else f"{hour:02d}:00"


def priority_label(priority: str) -> str:
    if priority == "상":
        return "특급 임무"
    elif priority == "중":
        return "1급 임무"
    return "보조 임무"


def priority_icon(priority: str) -> str:
    if priority == "상":
        return "🔥"
    elif priority == "중":
        return "⚡"
    return "✨"


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }


def load_tasks_from_supabase(selected_date_str):
    url = f"{SUPABASE_URL}/rest/v1/study_tasks"
    params = {
        "study_date": f"eq.{selected_date_str}",
        "select": "*",
        "order": "start_hour.asc",
    }
    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def delete_tasks_by_date(selected_date_str):
    url = f"{SUPABASE_URL}/rest/v1/study_tasks"
    params = {
        "study_date": f"eq.{selected_date_str}",
    }
    response = requests.delete(
        url,
        headers={**supabase_headers(), "Prefer": "return=representation"},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def overwrite_tasks_to_supabase(selected_date_str, tasks):
    delete_tasks_by_date(selected_date_str)

    if tasks:
        url = f"{SUPABASE_URL}/rest/v1/study_tasks"
        response = requests.post(
            url,
            headers={**supabase_headers(), "Prefer": "return=representation"},
            json=tasks,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    return []


def get_month_range(selected_date_value):
    year = selected_date_value.year
    month = selected_date_value.month

    month_start = date(year, month, 1)

    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)

    return month_start, next_month_start


def load_month_tasks_from_supabase(selected_date_value):
    month_start, next_month_start = get_month_range(selected_date_value)

    query_url = (
        f"{SUPABASE_URL}/rest/v1/study_tasks"
        f"?select=*"
        f"&study_date=gte.{month_start}"
        f"&study_date=lt.{next_month_start}"
        f"&order=study_date.asc,start_hour.asc"
    )

    response = requests.get(
        query_url,
        headers=supabase_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def calculate_monthly_reward(rows):
    if not rows:
        return 0, 0

    df = pd.DataFrame(rows)

    if df.empty:
        return 0, 0

    daily_status = (
        df.groupby("study_date")
        .agg(
            total_tasks=("completed", "count"),
            completed_tasks=("completed", "sum")
        )
        .reset_index()
    )

    daily_status["all_completed"] = (
        (daily_status["total_tasks"] > 0) &
        (daily_status["total_tasks"] == daily_status["completed_tasks"])
    )

    completed_days = int(daily_status["all_completed"].sum())
    monthly_reward = completed_days * reward_amount

    return monthly_reward, completed_days


st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Arial", sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #0b1020 0%, #121a33 45%, #0f172a 100%);
    color: #f8fafc;
}

.main-title {
    text-align: center;
    font-size: 40px;
    font-weight: 900;
    margin-top: 16px;
    margin-bottom: 8px;
    color: #f5f3ff;
    text-shadow: 0 0 12px rgba(147, 51, 234, 0.7);
}

.sub-title {
    text-align: center;
    font-size: 18px;
    color: #cbd5e1;
    margin-bottom: 20px;
}

.hero-box {
    background: linear-gradient(135deg, rgba(88,28,135,0.95), rgba(30,41,59,0.95));
    border: 1px solid rgba(168,85,247,0.45);
    border-radius: 20px;
    padding: 22px;
    box-shadow: 0 0 22px rgba(168,85,247,0.18);
    margin-bottom: 20px;
}

.reward-box {
    background: linear-gradient(135deg, #1e1b4b, #6d28d9);
    border-radius: 18px;
    padding: 18px;
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    color: white;
    box-shadow: 0 0 18px rgba(124,58,237,0.35);
    margin-bottom: 14px;
}

.month-reward-box {
    background: linear-gradient(135deg, #0f172a, #1d4ed8);
    border: 1px solid rgba(96,165,250,0.45);
    border-radius: 18px;
    padding: 18px;
    text-align: center;
    font-size: 22px;
    font-weight: 800;
    color: white;
    box-shadow: 0 0 18px rgba(59,130,246,0.28);
    margin-bottom: 18px;
}

.section-title {
    font-size: 24px;
    font-weight: 800;
    color: #e9d5ff;
    margin-top: 8px;
    margin-bottom: 12px;
}

.metric-box {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(168,85,247,0.28);
    border-radius: 16px;
    padding: 14px;
    text-align: center;
    margin-bottom: 10px;
}

.metric-title {
    font-size: 14px;
    color: #cbd5e1;
}

.metric-value {
    font-size: 28px;
    font-weight: 900;
    color: #f8fafc;
    margin-top: 4px;
}

div.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid rgba(168,85,247,0.45);
    background: linear-gradient(90deg, #4c1d95, #7c3aed);
    color: white;
    font-weight: 800;
    box-shadow: 0 0 14px rgba(124,58,237,0.25);
}

div.stButton > button:hover {
    border: 1px solid #c084fc;
    background: linear-gradient(90deg, #5b21b6, #8b5cf6);
    color: white;
}

div[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.85);
    border-radius: 14px;
    padding: 6px;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #22d3ee, #8b5cf6) !important;
}

label, .stMarkdown, .stText, p {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">임상욱 일일 스케쥴러</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">오늘의 임무를 배치하고, 주술 에너지를 100%까지 채워보자.</div>',
    unsafe_allow_html=True
)

selected_date = st.date_input("작전 날짜를 선택하세요", value=date.today())

try:
    month_rows = load_month_tasks_from_supabase(selected_date)
    monthly_reward, completed_days = calculate_monthly_reward(month_rows)
    st.markdown(
        f"""
        <div class="month-reward-box">
            📅 {selected_date.year}년 {selected_date.month}월 누적 임무 보상<br>
            {monthly_reward:,}원 / 완료한 날 {completed_days}일
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.warning(f"월별 누적 보상 조회 중 오류가 있어: {e}")

st.markdown(
    f"""
    <div class="hero-box">
        <div style="font-size:20px; font-weight:800; color:#f5f3ff; margin-bottom:8px;">
            ⚔️ 오늘의 미션 브리핑
        </div>
        <div style="font-size:15px; color:#e2e8f0; line-height:1.6;">
            특정 날짜를 다시 저장하면 그 날짜의 기존 데이터는 지워지고,
            <b>마지막 저장 상태만 최종본으로 반영</b>돼.
            모든 임무를 완수하면 <b>임무 보상 {reward_amount:,}원</b>이 활성화돼.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="section-title">📘 오늘의 임무 입력</div>', unsafe_allow_html=True)

task_count = st.number_input(
    "오늘 등록할 임무 개수",
    min_value=1,
    max_value=15,
    value=5,
    step=1
)

tasks_data = []

for i in range(int(task_count)):
    st.markdown(f"#### 임무 {i+1}")

    col1, col2, col3, col4, col5 = st.columns([4, 1.2, 1.2, 1.4, 1])

    with col1:
        task_name = st.text_input(
            f"임무 내용 {i+1}",
            placeholder="예: 고등 물리 숙제 완료하기",
            key=f"task_name_{i}"
        )

    with col2:
        start_hour = st.selectbox(
            f"시작 {i+1}",
            time_options[:-1],
            format_func=format_hour,
            key=f"start_hour_{i}"
        )

    with col3:
        valid_end_hours = [h for h in time_options if h > start_hour]
        end_hour = st.selectbox(
            f"종료 {i+1}",
            valid_end_hours,
            format_func=format_hour,
            key=f"end_hour_{i}"
        )

    with col4:
        priority = st.selectbox(
            f"등급 {i+1}",
            ["상", "중", "하"],
            format_func=priority_label,
            key=f"priority_{i}"
        )

    with col5:
        completed = st.checkbox("완료", key=f"completed_{i}")

    if task_name.strip():
        tasks_data.append({
            "study_date": str(selected_date),
            "task_name": task_name,
            "start_hour": start_hour,
            "end_hour": end_hour,
            "priority": priority,
            "completed": completed
        })

st.markdown("---")
st.markdown('<div class="section-title">🌀 오늘의 임무 요약</div>', unsafe_allow_html=True)

if tasks_data:
    input_df = pd.DataFrame(tasks_data)
    view_df = input_df.copy()
    view_df["시간"] = view_df["start_hour"].apply(format_hour) + " ~ " + view_df["end_hour"].apply(format_hour)
    view_df["등급"] = view_df["priority"].apply(lambda x: f"{priority_icon(x)} {priority_label(x)}")
    view_df["완료 여부"] = view_df["completed"].apply(lambda x: "✅ 완료" if x else "⬜ 진행중")
    view_df = view_df[["study_date", "시간", "task_name", "등급", "완료 여부"]]
    view_df.columns = ["날짜", "시간", "임무", "등급", "상태"]

    st.dataframe(view_df, use_container_width=True, hide_index=True)

    total_tasks = len(input_df)
    completed_tasks = int(input_df["completed"].sum())
    remaining_tasks = total_tasks - completed_tasks
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-title">총 임무 수</div>
                <div class="metric-value">{total_tasks}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-title">완료한 임무</div>
                <div class="metric-value">{completed_tasks}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-title">남은 임무</div>
                <div class="metric-value">{remaining_tasks}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title">⚡ 주술 에너지 충전율</div>', unsafe_allow_html=True)
    st.progress(completion_rate / 100)
    st.write(f"현재 에너지 충전율: **{completion_rate}%**")

    st.markdown('<div class="section-title">🕒 시간표 형태 보기</div>', unsafe_allow_html=True)

    schedule_rows = []
    for hour in range(4, 24):
        matched_tasks = []
        for _, row in input_df.iterrows():
            if row["start_hour"] <= hour < row["end_hour"]:
                status_icon = "✅" if row["completed"] else "⬜"
                matched_tasks.append(
                    f"{status_icon} {priority_icon(row['priority'])} {row['task_name']}"
                )

        schedule_rows.append({
            "시간대": f"{hour:02d}:00 ~ {hour+1:02d}:00",
            "계획": " / ".join(matched_tasks) if matched_tasks else ""
        })

    schedule_df = pd.DataFrame(schedule_rows)
    st.dataframe(schedule_df, use_container_width=True, hide_index=True)

    if total_tasks > 0 and completed_tasks == total_tasks:
        st.markdown(
            f"""
            <div class="reward-box">
                🎉 모든 임무 완수!<br>
                임무 보상 {reward_amount:,}원 획득
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info(f"모든 임무를 완료하면 임무 보상 {reward_amount:,}원이 활성화돼.")

    col_save, col_load = st.columns(2)

    with col_save:
        if st.button("💾 최종 상태로 저장"):
            try:
                overwrite_tasks_to_supabase(str(selected_date), tasks_data)
                st.success("해당 날짜 데이터가 최종 상태로 저장되었어. 이전 이력은 덮어써졌어.")
            except requests.HTTPError as e:
                detail = e.response.text if e.response is not None else str(e)
                st.error(f"저장 중 HTTP 오류: {detail}")
            except Exception as e:
                st.error(f"저장 중 오류: {e}")

    with col_load:
        if st.button("📂 저장된 최종 데이터 불러오기"):
            try:
                rows = load_tasks_from_supabase(str(selected_date))
                if rows:
                    saved_df = pd.DataFrame(rows)
                    saved_df["시간"] = saved_df["start_hour"].apply(format_hour) + " ~ " + saved_df["end_hour"].apply(format_hour)
                    saved_df["등급"] = saved_df["priority"].apply(lambda x: f"{priority_icon(x)} {priority_label(x)}")
                    saved_df["완료 여부"] = saved_df["completed"].apply(lambda x: "✅ 완료" if x else "⬜ 진행중")
                    saved_df = saved_df[["study_date", "시간", "task_name", "등급", "완료 여부"]]
                    saved_df.columns = ["날짜", "시간", "임무", "등급", "상태"]
                    st.dataframe(saved_df, use_container_width=True, hide_index=True)
                else:
                    st.info("해당 날짜에 저장된 최종 데이터가 없어.")
            except requests.HTTPError as e:
                detail = e.response.text if e.response is not None else str(e)
                st.error(f"조회 중 HTTP 오류: {detail}")
            except Exception as e:
                st.error(f"조회 중 오류: {e}")
else:
    st.warning("임무를 하나 이상 입력해줘.")
