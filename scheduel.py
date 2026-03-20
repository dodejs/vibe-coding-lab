import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="임상욱 일일 스케쥴러", layout="wide")

reward_amount = 5000

st.title("임상욱 일일 스케쥴러")
st.write("날짜별로 공부 계획을 입력하고 완료 여부와 중요도를 체크해보세요.")

# 날짜 선택
selected_date = st.date_input("날짜를 선택하세요", value=date.today())

# 시간 목록 생성: 04:00 ~ 24:00
time_options = list(range(4, 25))

def format_hour(hour: int) -> str:
    if hour == 24:
        return "24:00"
    return f"{hour:02d}:00"

def priority_icon(priority: str) -> str:
    if priority == "상":
        return "🔴"
    elif priority == "중":
        return "🟡"
    return "🟢"

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
            "날짜": str(selected_date),
            "시간": f"{format_hour(start_hour)} ~ {format_hour(end_hour)}",
            "할 일": task_name,
            "중요도": priority,
            "완료 여부": "완료" if completed else "미완료",
            "완료체크": completed,
            "시작": start_hour,
            "종료": end_hour
        })

st.markdown("---")
st.subheader("오늘의 스케줄 요약")

if tasks_data:
    df = pd.DataFrame(tasks_data)

    display_df = df[["날짜", "시간", "할 일", "중요도", "완료 여부"]]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    total_tasks = len(df)
    completed_tasks = int(df["완료체크"].sum())
    remaining_tasks = total_tasks - completed_tasks

    high_count = len(df[df["중요도"] == "상"])
    medium_count = len(df[df["중요도"] == "중"])
    low_count = len(df[df["중요도"] == "하"])

    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("총 태스크 수", total_tasks)
    col2.metric("완료한 태스크", completed_tasks)
    col3.metric("남은 태스크", remaining_tasks)

    col4, col5, col6 = st.columns(3)
    col4.metric("상", high_count)
    col5.metric("중", medium_count)
    col6.metric("하", low_count)

    st.subheader("완료율")
    st.progress(completion_rate / 100)
    st.write(f"완료율: **{completion_rate}%**")

    st.subheader("시간표 형태 보기")

    schedule_rows = []
    for hour in range(4, 24):
        matched_tasks = []
        for _, row in df.iterrows():
            if row["시작"] <= hour < row["종료"]:
                status_icon = "✅" if row["완료체크"] else "⬜"
                matched_tasks.append(
                    f"{status_icon} {priority_icon(row['중요도'])} {row['할 일']}"
                )

        schedule_rows.append({
            "날짜": str(selected_date),
            "시간대": f"{hour:02d}:00 ~ {hour+1:02d}:00",
            "계획": " / ".join(matched_tasks) if matched_tasks else ""
        })

    schedule_df = pd.DataFrame(schedule_rows)
    st.dataframe(schedule_df, use_container_width=True, hide_index=True)

    st.subheader("중요도 기준")
    st.write("🔴 상  |  🟡 중  |  🟢 하")

    if total_tasks > 0 and completed_tasks == total_tasks:
        st.success(f"{selected_date} 할 일을 모두 완료했습니다! Reward: {reward_amount:,}원 🎉")
    else:
        st.info(f"모든 태스크를 완료하면 Reward {reward_amount:,}원이 표시됩니다.")
else:
    st.warning("할 일을 하나 이상 입력해 주세요.")
