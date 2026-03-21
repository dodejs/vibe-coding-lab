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


def generate_time_options():
    options = []
    for hour in range(4, 24):
        for minute in range(0, 60, 10):
            options.append(f"{hour:02d}:{minute:02d}")
    options.append("24:00")
    return options


time_options = generate_time_options()


def time_to_minutes(time_str: str) -> int:
    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute


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


def load_tasks_from_supabase(selected_date_str: str):
    url = f"{SUPABASE_URL}/rest/v1/study_tasks"
    params = {
        "study_date": f"eq.{selected_date_str}",
        "select": "*",
        "order": "start_time.asc",
    }
    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def delete_tasks_by_date(selected_date_str: str):
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


def overwrite_tasks_to_supabase(selected_date_str: str, tasks: list[dict]):
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
        f"&order=study_date.asc,start_time.asc"
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
            completed_tasks=("completed", "sum"),
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


def blank_task():
    return {
        "task_name": "",
        "start_time": "04:00",
        "end_time": "04:10",
        "priority": "중",
        "completed": False,
    }


def rows_to_editor_tasks(rows):
    if not rows:
        return [blank_task() for _ in range(5)]

    tasks = []
    for row in rows:
        tasks.append({
            "task_name": row.get("task_name", ""),
            "start_time": row.get("start_time", "04:00"),
            "end_time": row.get("end_time", "04:10"),
            "priority": row.get("priority", "중"),
            "completed": bool(row.get("completed", False)),
        })
    return tasks


def init_editor_for_date(selected_date_str: str):
    rows = load_tasks_from_supabase(selected_date_str)
    st.session_state.editor_tasks = rows_to_editor_tasks(rows)
    st.session_state.loaded_date = selected_date_str


def sync_widget_values_to_editor_tasks():
    updated_tasks = []

    for i in range(len(st.session_state.editor_tasks)):
        task_name = st.session_state.get(f"task_name_{i}", "")
        start_time = st.session_state.get(f"start_time_{i}", "04:00")
        end_time = st.session_state.get(f"end_time_{i}", "04:10")
        raw_priority = st.session_state.get(f"priority_{i}", "중")
        raw_completed = st.session_state.get(f"completed_{i}", False)

        if start_time not in time_options:
            start_time = "04:00"
        if end_time not in time_options:
            end_time = "04:10"

        if time_to_minutes(end_time) <= time_to_minutes(start_time):
            start_index = time_options.index(start_time)
            if start_index + 1 < len(time_options):
                end_time = time_options[start_index + 1]
            else:
                end_time = "24:00"

        if raw_priority not in ["상", "중", "하"]:
            raw_priority = "중"

        updated_tasks.append({
            "task_name": task_name,
            "start_time": start_time,
            "end_time": end_time,
            "priority": raw_priority,
            "completed": bool(raw_completed),
        })

    st.session_state.editor_tasks = updated_tasks


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
    '<div class="sub-title">PC와 모바일에서 같은 날짜의 최신 임무 상태를 함께 보고 수정할 수 있어.</div>',
    unsafe_allow_html=True
)

selected_date = st.date_input("작전 날짜를 선택하세요", value=date.today())
selected_date_str = str(selected_date)

if "loaded_date" not in st.session_state:
    st.session_state.loaded_date = None

if "editor_tasks" not in st.session_state:
    st.session_state.editor_tasks = [blank_task() for _ in range(5)]

if st.session_state.loaded_date != selected_date_str:
    try:
        init_editor_for_date(selected_date_str)
    except Exception as e:
        st.error(f"해당 날짜 데이터 로드 중 오류: {e}")
        st.session_state.editor_tasks = [blank_task() for _ in range(5)]
        st.session_state.loaded_date = selected_date_str

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
            10분 단위로 임무 시간을 설정할 수 있어.
            같은 날짜를 PC와 모바일에서 열면 <b>최신 저장 상태가 자동 로드</b>돼.
            저장하면 그 날짜 데이터는 통째로 갱신되고, <b>마지막 저장 상태만 최종본</b>으로 남아.
            모든 임무를 완수하면 <b>임무 보상 {reward_amount:,}원</b>이 반영돼.
        </div>
        """,
    unsafe_allow_html=True
)

top_left, top_mid, top_right = st.columns([1, 1, 1])

with top_left:
    if st.button("➕ 임무 추가"):
        sync_widget_values_to_editor_tasks()
        st.session_state.editor_tasks.append(blank_task())
        st.rerun()

with top_mid:
    if st.button("➖ 마지막 임무 삭제"):
        sync_widget_values_to_editor_tasks()
        if len(st.session_state.editor_tasks) > 1:
            st.session_state.editor_tasks.pop()
        st.rerun()

with top_right:
    if st.button("🔄 최신 상태 다시 불러오기"):
        try:
            init_editor_for_date(selected_date_str)
            st.rerun()
        except Exception as e:
            st.error(f"최신 상태 불러오기 실패: {e}")

st.markdown('<div class="section-title">📘 오늘의 임무 입력</div>', unsafe_allow_html=True)

for i, task in enumerate(st.session_state.editor_tasks):
    st.markdown(f"#### 임무 {i+1}")

    col1, col2, col3, col4, col5 = st.columns([4, 1.5, 1.5, 1.4, 1])

    with col1:
        st.text_input(
            f"임무 내용 {i+1}",
            value=task["task_name"],
            placeholder="예: 고등 물리 숙제 완료하기",
            key=f"task_name_{i}"
        )

    with col2:
        current_start = task["start_time"] if task["start_time"] in time_options else "04:00"
        start_index = time_options.index(current_start)

        st.selectbox(
            f"시작 {i+1}",
            time_options[:-1],
            index=start_index,
            key=f"start_time_{i}"
        )

    with col3:
        current_start_widget = st.session_state.get(f"start_time_{i}", current_start)
        valid_end_times = [t for t in time_options if time_to_minutes(t) > time_to_minutes(current_start_widget)]
        current_end = task["end_time"] if task["end_time"] in valid_end_times else valid_end_times[0]
        end_index = valid_end_times.index(current_end)

        st.selectbox(
            f"종료 {i+1}",
            valid_end_times,
            index=end_index,
            key=f"end_time_{i}"
        )

    with col4:
        priority_options = ["상", "중", "하"]
        priority_index = priority_options.index(task["priority"]) if task["priority"] in priority_options else 1

        st.selectbox(
            f"등급 {i+1}",
            priority_options,
            index=priority_index,
            format_func=priority_label,
            key=f"priority_{i}"
        )

    with col5:
        st.checkbox(
            "완료",
            value=task["completed"],
            key=f"completed_{i}"
        )

sync_widget_values_to_editor_tasks()

tasks_data = []
for task in st.session_state.editor_tasks:
    task_name = str(task.get("task_name", "")).strip()
    start_time = task.get("start_time", "04:00")
    end_time = task.get("end_time", "04:10")
    priority = task.get("priority", "중")
    completed = bool(task.get("completed", False))

    if not task_name:
        continue

    if start_time not in time_options:
        start_time = "04:00"
    if end_time not in time_options:
        end_time = "04:10"

    if time_to_minutes(end_time) <= time_to_minutes(start_time):
        start_index = time_options.index(start_time)
        if start_index + 1 < len(time_options):
            end_time = time_options[start_index + 1]
        else:
            end_time = "24:00"

    if priority not in ["상", "중", "하"]:
        priority = "중"

    tasks_data.append({
        "study_date": selected_date_str,
        "task_name": task_name,
        "start_time": start_time,
        "end_time": end_time,
        "priority": priority,
        "completed": completed,
    })

st.markdown("---")
st.markdown('<div class="section-title">🌀 오늘의 임무 요약</div>', unsafe_allow_html=True)

if tasks_data:
    input_df = pd.DataFrame(tasks_data)
    view_df = input_df.copy()
    view_df["시간"] = view_df["start_time"] + " ~ " + view_df["end_time"]
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
    for idx in range(len(time_options) - 1):
        slot_start = time_options[idx]
        slot_end = time_options[idx + 1]
        matched_tasks = []

        for _, row in input_df.iterrows():
            if (
                time_to_minutes(row["start_time"]) <= time_to_minutes(slot_start)
                and time_to_minutes(row["end_time"]) > time_to_minutes(slot_start)
            ):
                status_icon = "✅" if row["completed"] else "⬜"
                matched_tasks.append(
                    f"{status_icon} {priority_icon(row['priority'])} {row['task_name']}"
                )

        schedule_rows.append({
            "시간대": f"{slot_start} ~ {slot_end}",
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

    save_col, load_col = st.columns(2)

    with save_col:
        if st.button("💾 최종 상태로 저장"):
            try:
                overwrite_tasks_to_supabase(selected_date_str, tasks_data)
                init_editor_for_date(selected_date_str)
                st.success("최종 상태 저장 완료. PC와 모바일 모두 같은 최신 상태를 보게 돼.")
                st.rerun()
            except requests.HTTPError as e:
                detail = e.response.text if e.response is not None else str(e)
                st.error(f"저장 중 HTTP 오류: {detail}")
            except Exception as e:
                st.error(f"저장 중 오류: {e}")

    with load_col:
        if st.button("📂 저장된 최종 데이터 보기"):
            try:
                rows = load_tasks_from_supabase(selected_date_str)
                if rows:
                    saved_df = pd.DataFrame(rows)
                    saved_df["시간"] = saved_df["start_time"] + " ~ " + saved_df["end_time"]
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
