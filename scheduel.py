import streamlit as st
import pandas as pd
from datetime import date, datetime, timezone
import requests

st.set_page_config(
    page_title="임상욱 일일 스케쥴러",
    layout="wide"
)

reward_amount = 5000
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


def make_time_options():
    options = []
    for total_min in range(240, 1441, 10):  # 04:00 ~ 24:00
        hour = total_min // 60
        minute = total_min % 60
        if hour >= 24:
            options.append("24:00")
        else:
            options.append(f"{hour:02d}:{minute:02d}")
    return options


TIME_OPTIONS = make_time_options()


def time_text_to_minutes(time_text: str) -> int:
    if time_text == "24:00":
        return 1440
    hour, minute = time_text.split(":")
    return int(hour) * 60 + int(minute)


def minutes_to_text(total_minutes: int) -> str:
    if total_minutes >= 1440:
        return "24:00"
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


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
        "order": "start_minute_of_day.asc",
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
        f"&order=study_date.asc,start_minute_of_day.asc"
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
        "end_time": "05:00",
        "priority": "중",
        "completed": False,
    }


def rows_to_editor_tasks(rows):
    if not rows:
        return [blank_task() for _ in range(5)]

    tasks = []
    for row in rows:
        start_total = int(row.get("start_minute_of_day", 240))
        end_total = int(row.get("end_minute_of_day", 300))

        tasks.append({
            "task_name": row.get("task_name", ""),
            "start_time": minutes_to_text(start_total),
            "end_time": minutes_to_text(end_total),
            "priority": row.get("priority", "중"),
            "completed": bool(row.get("completed", False)),
        })
    return tasks


def extract_last_save_info(rows):
    if not rows:
        return "-", "-"

    latest_row = max(rows, key=lambda x: x.get("last_saved_at") or "")
    saved_by = latest_row.get("last_saved_by") or "-"
    saved_at_raw = latest_row.get("last_saved_at")

    if not saved_at_raw:
        return saved_by, "-"

    try:
        saved_at = datetime.fromisoformat(saved_at_raw.replace("Z", "+00:00"))
        saved_at_local = saved_at.astimezone()
        saved_at_text = saved_at_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        saved_at_text = saved_at_raw

    return saved_by, saved_at_text


def init_editor_for_date(selected_date_str: str):
    rows = load_tasks_from_supabase(selected_date_str)
    st.session_state.editor_tasks = rows_to_editor_tasks(rows)
    st.session_state.loaded_date = selected_date_str

    saved_by, saved_at = extract_last_save_info(rows)
    st.session_state.last_saved_by = saved_by
    st.session_state.last_saved_at = saved_at


def sync_widget_values_to_editor_tasks():
    updated_tasks = []

    for i in range(len(st.session_state.editor_tasks)):
        start_time = st.session_state.get(f"start_time_{i}", "04:00")
        end_time = st.session_state.get(f"end_time_{i}", "05:00")

        start_total = time_text_to_minutes(start_time)
        end_total = time_text_to_minutes(end_time)

        if end_total <= start_total:
            end_total = start_total + 10
            if end_total > 1440:
                end_total = 1440
            end_time = minutes_to_text(end_total)

        updated_tasks.append({
            "task_name": st.session_state.get(f"task_name_{i}", ""),
            "start_time": start_time,
            "end_time": end_time,
            "priority": st.session_state.get(f"priority_{i}", "중"),
            "completed": st.session_state.get(f"completed_{i}", False),
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
.info-box {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(168,85,247,0.28);
    border-radius: 16px;
    padding: 14px;
    text-align: center;
    margin-bottom: 12px;
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
if "last_saved_by" not in st.session_state:
    st.session_state.last_saved_by = "-"
if "last_saved_at" not in st.session_state:
    st.session_state.last_saved_at = "-"

if st.session_state.loaded_date != selected_date_str:
    try:
        init_editor_for_date(selected_date_str)
    except Exception as e:
        st.error(f"해당 날짜 데이터 로드 중 오류: {e}")
        st.session_state.editor_tasks = [blank_task() for _ in range(5)]
        st.session_state.loaded_date = selected_date_str
        st.session_state.last_saved_by = "-"
        st.session_state.last_saved_at = "-"

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

info1, info2 = st.columns(2)
with info1:
    st.markdown(
        f"""
        <div class="info-box">
            <div style="font-size:14px; color:#cbd5e1;">마지막 저장자</div>
            <div style="font-size:22px; font-weight:800; color:white;">{st.session_state.last_saved_by}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with info2:
    st.markdown(
        f"""
        <div class="info-box">
            <div style="font-size:14px; color:#cbd5e1;">마지막 저장 시간</div>
            <div style="font-size:22px; font-weight:800; color:white;">{st.session_state.last_saved_at}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    f"""
    <div class="hero-box">
        <div style="font-size:20px; font-weight:800; color:#f5f3ff; margin-bottom:8px;">
            ⚔️ 오늘의 미션 브리핑
        </div>
        <div style="font-size:15px; color:#e2e8f0; line-height:1.6;">
            시작 시간과 종료 시간은 각각 <b>1개 박스</b>에서 선택하고,
            박스 안에서 <b>10분 단위</b>까지 선택할 수 있어.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

saver_name = st.text_input(
    "저장자 이름",
    value=st.session_state.last_saved_by if st.session_state.last_saved_by != "-" else "",
    placeholder="예: 아빠 / 엄마 / 상욱",
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

    col1, col2, col3, col4 = st.columns([4, 2, 2, 1])

    with col1:
        st.text_input(
            f"임무 내용 {i+1}",
            value=task["task_name"],
            placeholder="예: 고등 물리 숙제 완료하기",
            key=f"task_name_{i}"
        )

    with col2:
        start_index = TIME_OPTIONS.index(task["start_time"]) if task["start_time"] in TIME_OPTIONS else 0
        st.selectbox(
            f"시작 시간 {i+1}",
            TIME_OPTIONS,
            index=start_index,
            key=f"start_time_{i}"
        )

    with col3:
        end_index = TIME_OPTIONS.index(task["end_time"]) if task["end_time"] in TIME_OPTIONS else 1
        st.selectbox(
            f"종료 시간 {i+1}",
            TIME_OPTIONS,
            index=end_index,
            key=f"end_time_{i}"
        )

    with col4:
        st.checkbox(
            "완료",
            value=task["completed"],
            key=f"completed_{i}"
        )

    priority_options = ["상", "중", "하"]
    priority_index = priority_options.index(task["priority"]) if task["priority"] in priority_options else 1

    st.selectbox(
        f"등급 {i+1}",
        priority_options,
        index=priority_index,
        format_func=priority_label,
        key=f"priority_{i}"
    )

sync_widget_values_to_editor_tasks()

tasks_data = []
last_saved_at_utc = datetime.now(timezone.utc).isoformat()

for task in st.session_state.editor_tasks:
    if task["task_name"].strip():
        start_total = time_text_to_minutes(task["start_time"])
        end_total = time_text_to_minutes(task["end_time"])

        if end_total > start_total:
            tasks_data.append({
                "study_date": selected_date_str,
                "task_name": task["task_name"],
                "start_minute_of_day": start_total,
                "end_minute_of_day": end_total,
                "priority": task["priority"],
                "completed": task["completed"],
                "last_saved_by": saver_name.strip() if saver_name.strip() else "이름없음",
                "last_saved_at": last_saved_at_utc,
            })

st.markdown("---")
st.markdown('<div class="section-title">🌀 오늘의 임무 요약</div>', unsafe_allow_html=True)

if tasks_data:
    input_df = pd.DataFrame(tasks_data)
    view_df = input_df.copy()
    view_df["시간"] = view_df["start_minute_of_day"].apply(minutes_to_text) + " ~ " + view_df["end_minute_of_day"].apply(minutes_to_text)
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
        st.markdown(f'<div class="metric-box"><div class="metric-title">총 임무 수</div><div class="metric-value">{total_tasks}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box"><div class="metric-title">완료한 임무</div><div class="metric-value">{completed_tasks}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-box"><div class="metric-title">남은 임무</div><div class="metric-value">{remaining_tasks}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚡ 주술 에너지 충전율</div>', unsafe_allow_html=True)
    st.progress(completion_rate / 100)
    st.write(f"현재 에너지 충전율: **{completion_rate}%**")

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
                st.success("최종 상태 저장 완료. 시작/종료 시간은 한 박스씩 선택하게 바뀌었어.")
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
                    saved_df["시간"] = saved_df["start_minute_of_day"].apply(minutes_to_text) + " ~ " + saved_df["end_minute_of_day"].apply(minutes_to_text)
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
