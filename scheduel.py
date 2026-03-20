import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

st.set_page_config(page_title="임상욱 일일 스케쥴러", layout="wide")

reward_amount = 5000

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

time_options = list(range(4, 25))

def format_hour(hour: int) -> str:
    return "24:00" if hour == 24 else f"{hour:02d}:00"

def priority_icon(priority: str) -> str:
    if priority == "상":
        return "🔴"
    elif priority == "중":
        return "🟡"
    return "🟢"

st.title("임상욱 일일 스케쥴러")
st.write("날짜별 공부 계획을 입력하고 DB에 누적 저장합니다.")

selected_date = st.date_input("날짜를 선택하세요", value=date.today())

st.subheader(f"{selected_date} 오늘의 할 일 입력")

task_count = st.number_input(
    "오늘 등록할 태스크 개수",
    min_value=1,
    max_value=15,
    value=5,
    step=1
)

tasks_data = []

for i in range(int(task_count)):
    st.markdown(f"### 태스크 {i+1}")
    col1, col2, col3, col4, col5 = st.columns([4, 1.2, 1.2, 1.2, 1])

    with col1:
        task_name = st.text_input(
            f"할 일 내용 {i+1}",
            placeholder="예: 고등 물리 숙제 완료하기",
            key=f"task_name_{i}"
        )

    with col2:
        start_hour = st.selectbox(
            f"시작 시간 {i+1}",
            time_options[:-1],
            format_func=format_hour,
            key=f"start_hour_{i}"
        )

    with col3:
        valid_end_hours = [h for h in time_options if h > start_hour]
        end_hour = st.selectbox(
            f"종료 시간 {i+1}",
            valid_end_hours,
            format_func=format_hour,
            key=f"end_hour_{i}"
        )

    with col4:
        priority = st.selectbox(
            f"중요도 {i+1}",
            ["상", "중", "하"],
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
st.subheader("입력 요약")

if tasks_data:
    input_df = pd.DataFrame(tasks_data)
    view_df = input_df.copy()
    view_df["시간"] = view_df["start_hour"].apply(format_hour) + " ~ " + view_df["end_hour"].apply(format_hour)
    view_df["완료 여부"] = view_df["completed"].apply(lambda x: "완료" if x else "미완료")
    view_df = view_df[["study_date", "시간", "task_name", "priority", "완료 여부"]]
    view_df.columns = ["날짜", "시간", "할 일", "중요도", "완료 여부"]

    st.dataframe(view_df, use_container_width=True, hide_index=True)

    total_tasks = len(input_df)
    completed_tasks = int(input_df["completed"].sum())
    remaining_tasks = total_tasks - completed_tasks
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("총 태스크 수", total_tasks)
    c2.metric("완료한 태스크", completed_tasks)
    c3.metric("남은 태스크", remaining_tasks)

    st.progress(completion_rate / 100)
    st.write(f"완료율: **{completion_rate}%**")

    if total_tasks > 0 and completed_tasks == total_tasks:
        st.success(f"{selected_date} 할 일을 모두 완료했습니다! Reward: {reward_amount:,}원 🎉")
    else:
        st.info(f"모든 태스크를 완료하면 Reward {reward_amount:,}원이 표시됩니다.")

    if st.button("DB에 저장"):
        try:
            supabase.table("study_tasks").insert(tasks_data).execute()
            st.success("Supabase DB에 저장되었습니다.")
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")
else:
    st.warning("할 일을 하나 이상 입력해 주세요.")

st.markdown("---")
st.subheader("선택 날짜 저장 내역 조회")

if st.button("저장된 데이터 불러오기"):
    try:
        response = (
            supabase.table("study_tasks")
            .select("*")
            .eq("study_date", str(selected_date))
            .order("start_hour")
            .execute()
        )

        rows = response.data if response.data else []
        if rows:
            saved_df = pd.DataFrame(rows)
            saved_df["시간"] = saved_df["start_hour"].apply(format_hour) + " ~ " + saved_df["end_hour"].apply(format_hour)
            saved_df["완료 여부"] = saved_df["completed"].apply(lambda x: "완료" if x else "미완료")
            saved_df = saved_df[["study_date", "시간", "task_name", "priority", "완료 여부"]]
            saved_df.columns = ["날짜", "시간", "할 일", "중요도", "완료 여부"]
            st.dataframe(saved_df, use_container_width=True, hide_index=True)
        else:
            st.info("해당 날짜에 저장된 데이터가 없습니다.")
    except Exception as e:
        st.error(f"조회 중 오류가 발생했습니다: {e}")

    
